from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Video, Transcript, Translation, VideoStatus
from app.schemas.schemas import (
    TranscriptResponse, TranscriptCreate,
    TranslationCreate, TranslationResponse
)
from app.workers.tasks import transcribe_video, translate_transcript

router = APIRouter(prefix="/transcripts", tags=["Transcripts"])


@router.post("", response_model=TranscriptResponse, status_code=status.HTTP_201_CREATED)
async def create_transcript(
    data: TranscriptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Video).where(
            Video.id == data.video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    existing = await db.execute(
        select(Transcript).where(Transcript.video_id == video.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Transcript already exists")

    transcript = Transcript(video_id=video.id)
    db.add(transcript)
    await db.flush()
    await db.refresh(transcript)

    task = transcribe_video.delay(str(video.id), str(transcript.id))

    return TranscriptResponse.model_validate(transcript)


@router.get("/video/{video_id}", response_model=TranscriptResponse)
async def get_transcript_by_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    transcript_result = await db.execute(
        select(Transcript).where(Transcript.video_id == video.id)
    )
    transcript = transcript_result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return TranscriptResponse.model_validate(transcript)


@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transcript).where(Transcript.id == transcript_id))
    transcript = result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    video_result = await db.execute(
        select(Video).where(
            Video.id == transcript.video_id,
            Video.user_id == current_user.id
        )
    )
    if not video_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    return TranscriptResponse.model_validate(transcript)


@router.put("/{transcript_id}", response_model=TranscriptResponse)
async def update_transcript(
    transcript_id: UUID,
    full_text: str = None,
    segments: list = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transcript).where(Transcript.id == transcript_id))
    transcript = result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    video_result = await db.execute(
        select(Video).where(
            Video.id == transcript.video_id,
            Video.user_id == current_user.id
        )
    )
    if not video_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    if full_text is not None:
        transcript.full_text = full_text
    if segments is not None:
        transcript.segments = segments

    await db.flush()
    await db.refresh(transcript)
    return TranscriptResponse.model_validate(transcript)


@router.post("/translate", response_model=TranslationResponse, status_code=status.HTTP_201_CREATED)
async def create_translation(
    data: TranslationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transcript_result = await db.execute(
        select(Transcript).where(Transcript.id == data.transcript_id)
    )
    transcript = transcript_result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    video_result = await db.execute(
        select(Video).where(
            Video.id == transcript.video_id,
            Video.user_id == current_user.id
        )
    )
    if not video_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    existing = await db.execute(
        select(Translation).where(
            Translation.transcript_id == transcript.id,
            Translation.target_language == data.target_language
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Translation already exists")

    translation = Translation(
        transcript_id=transcript.id,
        source_language=transcript.language or "en",
        target_language=data.target_language,
    )
    db.add(translation)
    await db.flush()
    await db.refresh(translation)

    task = translate_transcript.delay(
        str(transcript.id), str(translation.id), data.target_language
    )

    return TranslationResponse.model_validate(translation)


@router.get("/{transcript_id}/translations", response_model=list[TranslationResponse])
async def get_translations(
    transcript_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transcript_result = await db.execute(
        select(Transcript).where(Transcript.id == transcript_id)
    )
    transcript = transcript_result.scalar_one_or_none()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    result = await db.execute(
        select(Translation).where(Translation.transcript_id == transcript_id)
    )
    translations = result.scalars().all()

    return [TranslationResponse.model_validate(t) for t in translations]
