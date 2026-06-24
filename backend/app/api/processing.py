from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Video, Subtitle, Export

router = APIRouter(prefix="/processing", tags=["Processing"])


@router.post("/{video_id}/subtitles")
async def generate_subtitles(video_id: str, language: str = "en", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video = (await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))).scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    from app.models.models import Transcript
    transcript = (await db.execute(select(Transcript).where(Transcript.video_id == video_id))).scalar_one_or_none()
    if not transcript or not transcript.segments:
        raise HTTPException(status_code=400, detail="Generate transcript first")
    srt_lines = []
    for i, seg in enumerate(transcript.segments, 1):
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("text", "")
        sh, sm, ss = int(start//3600), int((start%3600)//60), int(start%60)
        eh, em, es = int(end//3600), int((end%3600)//60), int(end%60)
        sms, ems = int((start%1)*1000), int((end%1)*1000)
        srt_lines.append(f"{i}\n{sh:02d}:{sm:02d}:{ss:02d},{sms:03d} --> {eh:02d}:{em:02d}:{es:02d},{ems:03d}\n{text}\n")
    subtitle = Subtitle(video_id=video_id, language=language, content="\n".join(srt_lines), format="srt")
    db.add(subtitle)
    await db.flush()
    await db.refresh(subtitle)
    return {"id": subtitle.id, "language": subtitle.language, "format": subtitle.format, "content": subtitle.content}


@router.get("/{video_id}/subtitles")
async def get_subtitles(video_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video = (await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))).scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    result = await db.execute(select(Subtitle).where(Subtitle.video_id == video_id))
    subs = result.scalars().all()
    return [{"id": s.id, "language": s.language, "format": s.format, "content": s.content, "is_default": s.is_default} for s in subs]


@router.post("/export")
async def create_export(video_id: str, format: str = "mp4", resolution: str = "1080p", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video = (await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))).scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    export = Export(video_id=video_id, format=format, resolution=resolution, status="completed")
    db.add(export)
    await db.flush()
    await db.refresh(export)
    return {"id": export.id, "status": export.status, "format": export.format, "resolution": export.resolution}
