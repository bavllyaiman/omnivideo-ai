import os
import subprocess
import json
import tempfile
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FFMPEG = os.getenv("FFMPEG_PATH", "ffmpeg")
FFPROBE = os.getenv("FFPROBE_PATH", "ffprobe")


def probe_video(path: str) -> dict:
    try:
        cmd = [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            info = {"duration": 0, "width": 0, "height": 0, "fps": 0, "codec": ""}
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    info["width"] = int(s.get("width", 0))
                    info["height"] = int(s.get("height", 0))
                    info["codec"] = s.get("codec_name", "")
                    rfr = s.get("r_frame_rate", "0/1")
                    if "/" in rfr:
                        num, den = rfr.split("/")
                        info["fps"] = round(int(num) / int(den), 2) if int(den) > 0 else 0
                    break
            fmt = data.get("format", {})
            info["duration"] = round(float(fmt.get("duration", 0)), 2)
            return info
    except Exception as e:
        logger.error(f"probe error: {e}")
    return {}


def analyze_video(path: str) -> dict:
    info = probe_video(path)
    duration = info.get("duration", 0)
    analysis = {
        "scenes": [],
        "chapters": [],
        "summary": f"Video analyzed. Duration: {duration}s, Resolution: {info.get('width')}x{info.get('height')}, Codec: {info.get('codec')}",
        "objects_detected": [],
        "emotions": [],
        "viral_moments": [],
    }
    try:
        cmd = [
            FFMPEG, "-i", path,
            "-vf", "select='gt(scene,0.3)',showinfo",
            "-vsync", "vfr", "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        for line in result.stderr.split("\n"):
            if "showinfo" in line and "pts_time" in line:
                try:
                    pts = float(line.split("pts_time:")[1].split()[0])
                    analysis["scenes"].append({"timestamp": round(pts, 2)})
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"scene detection error: {e}")

    if analysis["scenes"]:
        analysis["chapters"] = [
            {"start": 0, "end": analysis["scenes"][0]["timestamp"], "title": "Opening"},
        ]
        for i, scene in enumerate(analysis["scenes"][:-1]):
            analysis["chapters"].append({
                "start": scene["timestamp"],
                "end": analysis["scenes"][i + 1]["timestamp"],
                "title": f"Scene {i + 2}",
            })
        analysis["chapters"].append({
            "start": analysis["scenes"][-1]["timestamp"],
            "end": duration,
            "title": "Ending",
        })

    return analysis


def extract_audio(path: str, output_path: str) -> bool:
    try:
        cmd = [FFMPEG, "-i", path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_path, "-y"]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"audio extraction error: {e}")
        return False


def cut_video(input_path: str, output_path: str, start: float, end: float) -> bool:
    try:
        duration = end - start
        cmd = [FFMPEG, "-ss", str(start), "-i", input_path, "-t", str(duration), "-c", "copy", output_path, "-y"]
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"cut error: {e}")
        return False


def add_subtitles(input_path: str, output_path: str, srt_path: str) -> bool:
    try:
        cmd = [
            FFMPEG, "-i", input_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy", output_path, "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"subtitle burn error: {e}")
        return False


def generate_thumbnail(input_path: str, output_path: str, timestamp: float = None) -> bool:
    try:
        if timestamp is None:
            info = probe_video(input_path)
            timestamp = info.get("duration", 10) / 4
        cmd = [FFMPEG, "-ss", str(timestamp), "-i", input_path, "-vframes", "1", "-q:v", "2", output_path, "-y"]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"thumbnail error: {e}")
        return False


def create_short(input_path: str, output_path: str, start: float, duration: float = 60) -> bool:
    try:
        cmd = [
            FFMPEG, "-ss", str(start), "-i", input_path,
            "-t", str(duration),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", output_path, "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"short error: {e}")
        return False


def export_video(input_path: str, output_path: str, resolution: str = "1920:1080") -> bool:
    try:
        cmd = [
            FFMPEG, "-i", input_path,
            "-vf", f"scale={resolution}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", output_path, "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=3600)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"export error: {e}")
        return False


def remove_silence(input_path: str, output_path: str) -> bool:
    try:
        cmd = [
            FFMPEG, "-i", input_path,
            "-af", "silenceremove=start_periods=1:start_duration=0.5:start_threshold=-40dB:stop_periods=-1:stop_duration=0.5:stop_threshold=-40dB",
            "-c:v", "copy", output_path, "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=3600)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"remove silence error: {e}")
        return False
