from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from uuid import UUID
import httpx
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.storage import storage
from app.core.config import settings
from app.models.models import User, Video, VideoStatus, Project
from app.schemas.schemas import (
    VideoUploadRequest, VideoResponse, VideoAnalysisResponse,
    PaginatedResponse
)
from app.workers.tasks import process_video_upload, extract_video_metadata

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.get("", response_model=PaginatedResponse)
async def list_videos(
    project_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    query = select(Video).where(Video.user_id == current_user.id)

    if project_id:
        query = query.where(Video.project_id == project_id)

    total_result = await db.execute(
        select(func.count(Video.id)).where(Video.user_id == current_user.id)
    )
    total = total_result.scalar()

    result = await db.execute(
        query.order_by(desc(Video.created_at)).offset(offset).limit(per_page)
    )
    videos = result.scalars().all()

    return PaginatedResponse(
        items=[VideoResponse.model_validate(v) for v in videos],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.post("/upload-url", response_model=dict)
async def get_upload_url(
    data: VideoUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project_result = await db.execute(
        select(Project).where(
            Project.id == data.project_id,
            Project.user_id == current_user.id
        )
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.storage_used_bytes >= current_user.storage_limit_bytes:
        raise HTTPException(status_code=402, detail="Storage limit exceeded")

    if current_user.credits_remaining <= 0:
        raise HTTPException(status_code=402, detail="No credits remaining")

    presigned_url, key = await storage.generate_upload_url(
        data.filename, data.content_type
    )

    video = Video(
        project_id=data.project_id,
        user_id=current_user.id,
        filename=data.filename,
        original_filename=data.filename,
        s3_key=key,
        status=VideoStatus.UPLOADING,
        mime_type=data.content_type,
        file_size=data.file_size,
        source_type=data.source_type,
        source_url=data.source_url,
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)

    return {
        "upload_url": presigned_url,
        "video_id": str(video.id),
        "s3_key": key,
    }


@router.post("/upload-direct", response_model=VideoResponse)
async def upload_video_direct(
    project_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.storage_used_bytes >= current_user.storage_limit_bytes:
        raise HTTPException(status_code=402, detail="Storage limit exceeded")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "mp4"
    from datetime import datetime
    import uuid
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
    key = f"uploads/{date_prefix}/{uuid.uuid4()}.{ext}"

    from io import BytesIO
    await storage.upload_file(BytesIO(content), key, file.content_type)

    video = Video(
        project_id=project_id,
        user_id=current_user.id,
        filename=file.filename,
        original_filename=file.filename,
        s3_key=key,
        status=VideoStatus.UPLOADED,
        mime_type=file.content_type,
        file_size=len(content),
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)

    task = extract_video_metadata.delay(str(video.id))

    return VideoResponse.model_validate(video)


@router.post("/import/youtube", response_model=VideoResponse)
async def import_from_youtube(
    project_id: UUID,
    url: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import re
    youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_regex, url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    video_id_str = match.group(1)

    video = Video(
        project_id=project_id,
        user_id=current_user.id,
        filename=f"youtube_{video_id_str}.mp4",
        s3_key=f"imports/youtube/{video_id_str}.mp4",
        status=VideoStatus.UPLOADING,
        source_type="youtube",
        source_url=url,
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)

    task = process_video_upload.delay(str(video.id), "youtube", url)

    return VideoResponse.model_validate(video)


@router.post("/import/url", response_model=VideoResponse)
async def import_from_url(
    project_id: UUID,
    url: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid as uuid_mod
    import os

    video = Video(
        project_id=project_id,
        user_id=current_user.id,
        filename=f"url_import_{uuid_mod.uuid4()}.mp4",
        s3_key=f"imports/url/{uuid_mod.uuid4()}.mp4",
        status=VideoStatus.UPLOADING,
        source_type="url",
        source_url=url,
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)

    task = process_video_upload.delay(str(video.id), "url", url)

    return VideoResponse.model_validate(video)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
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
    return VideoResponse.model_validate(video)


@router.get("/{video_id}/analysis", response_model=VideoAnalysisResponse)
async def get_video_analysis(
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

    if not video.analysis:
        raise HTTPException(status_code=404, detail="Video not yet analyzed")

    return VideoAnalysisResponse(**video.analysis)


@router.post("/{video_id}/reanalyze", response_model=dict)
async def reanalyze_video(
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

    from app.workers.tasks import analyze_video
    task = analyze_video.delay(str(video.id))

    return {"task_id": task.id, "status": "queued"}


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
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

    await storage.delete_file(video.s3_key)
    await db.delete(video)
    return None
