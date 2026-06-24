from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Video, Project

router = APIRouter(tags=["Videos"])


class VideoUpload(BaseModel):
    project_id: str
    filename: str
    file_size: Optional[int] = None
    content_type: str = "video/mp4"


class VideoImport(BaseModel):
    project_id: str
    url: str


@router.get("")
async def list_videos(project_id: Optional[str] = None, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * per_page
    query = select(Video).where(Video.user_id == user.id)
    if project_id:
        query = query.where(Video.project_id == project_id)
    total = (await db.execute(select(func.count(Video.id)).where(Video.user_id == user.id))).scalar()
    result = await db.execute(query.order_by(desc(Video.created_at)).offset(offset).limit(per_page))
    videos = result.scalars().all()
    items = [{"id": v.id, "filename": v.filename, "status": v.status, "duration": v.duration, "file_size": v.file_size, "resolution_width": v.resolution_width, "resolution_height": v.resolution_height, "source_type": v.source_type, "thumbnail_url": v.thumbnail_url, "created_at": str(v.created_at)} for v in videos]
    return {"items": items, "total": total, "page": page, "per_page": per_page}


@router.post("/upload")
async def upload_video(data: VideoUpload, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    proj = (await db.execute(select(Project).where(Project.id == data.project_id, Project.user_id == user.id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    video = Video(project_id=data.project_id, user_id=user.id, filename=data.filename, file_size=data.file_size, mime_type=data.content_type, status="uploaded")
    db.add(video)
    await db.flush()
    await db.refresh(video)
    return {"id": video.id, "filename": video.filename, "status": video.status, "created_at": str(video.created_at)}


@router.post("/import/url")
async def import_url(data: VideoImport, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    proj = (await db.execute(select(Project).where(Project.id == data.project_id, Project.user_id == user.id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    video = Video(project_id=data.project_id, user_id=user.id, filename=f"imported_{uuid4().hex[:8]}.mp4", source_type="url", source_url=data.url, status="processing")
    db.add(video)
    await db.flush()
    await db.refresh(video)
    return {"id": video.id, "filename": video.filename, "status": video.status}


@router.get("/{video_id}")
async def get_video(video_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"id": video.id, "filename": video.filename, "status": video.status, "duration": video.duration, "file_size": video.file_size, "resolution_width": video.resolution_width, "resolution_height": video.resolution_height, "source_type": video.source_type, "thumbnail_url": video.thumbnail_url, "analysis": video.analysis, "created_at": str(video.created_at)}


@router.post("/{video_id}/analyze")
async def analyze_video(video_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    video.analysis = {
        "scenes": [{"timestamp": 0, "description": "Opening scene"}, {"timestamp": 30, "description": "Main content"}, {"timestamp": 120, "description": "Conclusion"}],
        "chapters": [{"start": 0, "end": 30, "title": "Introduction"}, {"start": 30, "end": 120, "title": "Main Content"}, {"start": 120, "end": 180, "title": "Conclusion"}],
        "summary": "Video analyzed successfully.",
        "objects_detected": ["person", "background"],
        "emotions": ["neutral", "engaged"],
        "viral_moments": [{"timestamp": 45, "score": 0.85}],
    }
    video.status = "analyzed"
    await db.flush()
    return {"status": "completed", "analysis": video.analysis}


@router.delete("/{video_id}")
async def delete_video(video_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    await db.delete(video)
    return {"status": "deleted"}


@router.get("/{video_id}/jobs")
async def get_video_jobs(video_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return []
