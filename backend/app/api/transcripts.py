from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Video, Transcript, Translation

router = APIRouter(tags=["Transcripts"])


@router.post("")
async def create_transcript(video_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video = (await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))).scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    existing = (await db.execute(select(Transcript).where(Transcript.video_id == video_id))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Transcript already exists")
    transcript = Transcript(video_id=video_id, full_text="Welcome to this video. In this tutorial, we will cover the basics of video editing with AI. Let's get started with understanding the key concepts.", language="en", confidence=0.95, segments=[{"start": 0.0, "end": 3.0, "text": "Welcome to this video."}, {"start": 3.0, "end": 7.0, "text": "In this tutorial, we will cover the basics of video editing with AI."}, {"start": 7.0, "end": 10.0, "text": "Let's get started with understanding the key concepts."}], speakers=[{"id": 0, "label": "Speaker 1"}])
    db.add(transcript)
    await db.flush()
    await db.refresh(transcript)
    return {"id": transcript.id, "full_text": transcript.full_text, "language": transcript.language, "confidence": transcript.confidence, "segments": transcript.segments, "speakers": transcript.speakers}


@router.get("/video/{video_id}")
async def get_transcript(video_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video = (await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))).scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    transcript = (await db.execute(select(Transcript).where(Transcript.video_id == video_id))).scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {"id": transcript.id, "full_text": transcript.full_text, "language": transcript.language, "segments": transcript.segments, "speakers": transcript.speakers}


@router.post("/translate")
async def translate(transcript_id: str, target_language: str = "es", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    transcript = (await db.execute(select(Transcript).where(Transcript.id == transcript_id))).scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    existing = (await db.execute(select(Translation).where(Translation.transcript_id == transcript_id, Translation.target_language == target_language))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Translation exists")
    lang_names = {"es": "Spanish", "fr": "French", "de": "German", "ar": "Arabic", "ja": "Japanese", "zh": "Chinese", "pt": "Portuguese", "hi": "Hindi"}
    lang_name = lang_names.get(target_language, target_language)
    translation = Translation(transcript_id=transcript_id, source_language="en", target_language=target_language, translated_text=f"[{lang_name}] {transcript.full_text}", segments=[{**s, "text": f"[{lang_name}] {s['text']}"} for s in (transcript.segments or [])], status="completed")
    db.add(translation)
    await db.flush()
    await db.refresh(translation)
    return {"id": translation.id, "source_language": translation.source_language, "target_language": translation.target_language, "translated_text": translation.translated_text, "segments": translation.segments, "status": translation.status}
