import os
import sys
import tempfile
import logging
import boto3
import httpx
from botocore.config import Config
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from video_processor import (
    probe_video, analyze_video, extract_audio, cut_video,
    add_subtitles, generate_thumbnail, create_short,
    export_video, remove_silence
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OmniVideo Worker", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT_URL", "")
S3_KEY = os.getenv("AWS_ACCESS_KEY_ID", "")
S3_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "")
S3_BUCKET = os.getenv("AWS_S3_BUCKET", "omnivideo")
S3_REGION = os.getenv("AWS_S3_REGION", "auto")
API_URL = os.getenv("API_URL", "http://localhost:8000")

s3 = None
if S3_ENDPOINT and S3_KEY:
    s3 = boto3.client(
        "s3", endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_KEY, aws_secret_access_key=S3_SECRET,
        config=Config(signature_version="s3v4"), region_name=S3_REGION,
    )


class ProcessRequest(BaseModel):
    video_id: str
    task_type: str
    params: Optional[dict] = None


def download_from_s3(key: str, local_path: str):
    if s3:
        s3.download_file(S3_BUCKET, key, local_path)
    else:
        raise Exception("S3 not configured")


def upload_to_s3(local_path: str, key: str, content_type: str = "video/mp4"):
    if s3:
        s3.upload_fileobj(open(local_path, "rb"), S3_BUCKET, key, ExtraArgs={"ContentType": content_type})
        return key
    raise Exception("S3 not configured")


def get_presigned_url(key: str, expiry: int = 86400) -> str:
    if s3:
        return s3.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=expiry)
    return ""


def update_job(job_id: str, status: str, result: dict = None, error: str = None):
    try:
        httpx.put(f"{API_URL}/api/worker/jobs/{job_id}", json={
            "status": status, "result": result, "error_message": error
        }, timeout=10)
    except Exception as e:
        logger.error(f"Failed to update job: {e}")


@app.get("/health")
async def health():
    return {"status": "ok", "s3": "configured" if s3 else "not configured"}


@app.post("/process")
async def process_video(req: ProcessRequest):
    tmpdir = tempfile.mkdtemp()
    input_path = os.path.join(tmpdir, "input.mp4")

    try:
        if req.task_type == "probe":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            info = probe_video(input_path)
            return {"status": "completed", "result": info}

        elif req.task_type == "analyze":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            analysis = analyze_video(input_path)
            thumb_path = os.path.join(tmpdir, "thumb.jpg")
            generate_thumbnail(input_path, thumb_path)
            thumb_key = f"thumbnails/{req.video_id}.jpg"
            upload_to_s3(thumb_path, thumb_key, "image/jpeg")
            return {"status": "completed", "result": analysis, "thumbnail_key": thumb_key}

        elif req.task_type == "extract_audio":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            audio_path = os.path.join(tmpdir, "audio.wav")
            extract_audio(input_path, audio_path)
            audio_key = f"audio/{req.video_id}.wav"
            upload_to_s3(audio_path, audio_key, "audio/wav")
            return {"status": "completed", "result": {"audio_key": audio_key}}

        elif req.task_type == "cut":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            out_path = os.path.join(tmpdir, "cut.mp4")
            cut_video(input_path, out_path, req.params["start"], req.params["end"])
            out_key = f"processed/{req.video_id}_cut.mp4"
            upload_to_s3(out_path, out_key)
            return {"status": "completed", "result": {"output_key": out_key, "download_url": get_presigned_url(out_key)}}

        elif req.task_type == "subtitles":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            srt_content = req.params.get("srt_content", "")
            srt_path = os.path.join(tmpdir, "subs.srt")
            with open(srt_path, "w") as f:
                f.write(srt_content)
            out_path = os.path.join(tmpdir, "subbed.mp4")
            add_subtitles(input_path, out_path, srt_path)
            out_key = f"processed/{req.video_id}_subtitled.mp4"
            upload_to_s3(out_path, out_key)
            return {"status": "completed", "result": {"output_key": out_key, "download_url": get_presigned_url(out_key)}}

        elif req.task_type == "thumbnail":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            ts = req.params.get("timestamp")
            thumb_path = os.path.join(tmpdir, "thumb.jpg")
            generate_thumbnail(input_path, thumb_path, ts)
            thumb_key = f"thumbnails/{req.video_id}_{ts or 'auto'}.jpg"
            upload_to_s3(thumb_path, thumb_key, "image/jpeg")
            return {"status": "completed", "result": {"thumbnail_key": thumb_key, "url": get_presigned_url(thumb_key)}}

        elif req.task_type == "short":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            out_path = os.path.join(tmpdir, "short.mp4")
            create_short(input_path, out_path, req.params.get("start", 0), req.params.get("duration", 60))
            out_key = f"shorts/{req.video_id}_short.mp4"
            upload_to_s3(out_path, out_key)
            return {"status": "completed", "result": {"output_key": out_key, "download_url": get_presigned_url(out_key)}}

        elif req.task_type == "export":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            res_map = {"720p": "1280:720", "1080p": "1920:1080", "4k": "3840:2160"}
            res = res_map.get(req.params.get("resolution", "1080p"), "1920:1080")
            out_path = os.path.join(tmpdir, "export.mp4")
            export_video(input_path, out_path, res)
            out_key = f"exports/{req.video_id}_{req.params.get('resolution', '1080p')}.mp4"
            upload_to_s3(out_path, out_key)
            return {"status": "completed", "result": {"output_key": out_key, "download_url": get_presigned_url(out_key)}}

        elif req.task_type == "remove_silence":
            download_from_s3(req.params.get("s3_key", ""), input_path)
            out_path = os.path.join(tmpdir, "no_silence.mp4")
            remove_silence(input_path, out_path)
            out_key = f"processed/{req.video_id}_no_silence.mp4"
            upload_to_s3(out_path, out_key)
            return {"status": "completed", "result": {"output_key": out_key, "download_url": get_presigned_url(out_key)}}

        else:
            return {"status": "error", "detail": f"Unknown task: {req.task_type}"}

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
