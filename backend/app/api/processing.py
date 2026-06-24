from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Video, Subtitle, Job, JobStatus
from app.schemas.schemas import (
    SubtitleCreate, SubtitleResponse, JobResponse, ExportRequest,
    ExportResponse, ShortCreate, ShortResponse
)
from app.workers.tasks import (
    generate_subtitles, burn_subtitles, export_video,
    generate_shorts, generate_thumbnail, process_video_edit
)

router = APIRouter(prefix="/processing", tags=["Video Processing"])


@router.post("/{video_id}/subtitles/generate", response_model=JobResponse)
async def generate_video_subtitles(
    video_id: UUID,
    language: str = "en",
    style: dict = None,
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

    job = Job(
        video_id=video.id,
        agent_name="subtitle_generation",
        status=JobStatus.QUEUED,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    subtitle = Subtitle(
        video_id=video.id,
        language=language,
        style=style or {},
    )
    db.add(subtitle)
    await db.flush()
    await db.refresh(subtitle)

    task = generate_subtitles.delay(
        str(video.id), str(job.id), str(subtitle.id), language
    )

    return JobResponse.model_validate(job)


@router.post("/{video_id}/subtitles/burn", response_model=JobResponse)
async def burn_video_subtitles(
    video_id: UUID,
    subtitle_id: UUID,
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

    sub_result = await db.execute(
        select(Subtitle).where(
            Subtitle.id == subtitle_id,
            Subtitle.video_id == video.id
        )
    )
    subtitle = sub_result.scalar_one_or_none()
    if not subtitle:
        raise HTTPException(status_code=404, detail="Subtitle not found")

    job = Job(
        video_id=video.id,
        agent_name="subtitle_burn",
        status=JobStatus.QUEUED,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    task = burn_subtitles.delay(str(video.id), str(job.id), str(subtitle_id))

    return JobResponse.model_validate(job)


@router.post("/{video_id}/edit", response_model=JobResponse)
async def edit_video(
    video_id: UUID,
    edit_instructions: dict,
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

    job = Job(
        video_id=video.id,
        agent_name="video_editing",
        status=JobStatus.QUEUED,
        result=edit_instructions,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    task = process_video_edit.delay(str(video.id), str(job.id), edit_instructions)

    return JobResponse.model_validate(job)


@router.post("/export", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
async def create_export(
    data: ExportRequest,
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

    from app.models.models import Export
    export = Export(
        project_id=video.project_id,
        video_id=video.id,
        format=data.format,
        resolution=data.resolution,
        quality=data.quality,
        settings={
            "include_subtitles": data.include_subtitles,
            "include_overlays": data.include_overlays,
            "custom_settings": data.custom_settings,
        },
        status="pending",
    )
    db.add(export)
    await db.flush()
    await db.refresh(export)

    task = export_video.delay(str(export.id))

    return ExportResponse.model_validate(export)


@router.post("/{video_id}/shorts", response_model=ShortResponse, status_code=status.HTTP_201_CREATED)
async def create_short(
    video_id: UUID,
    data: ShortCreate,
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

    from app.models.models import Short
    short = Short(
        original_video_id=video.id,
        platform=data.platform,
        title=data.title,
        status="pending",
    )
    db.add(short)
    await db.flush()
    await db.refresh(short)

    task = generate_shorts.delay(str(video.id), str(short.id), data.platform)

    return ShortResponse.model_validate(short)


@router.post("/{video_id}/thumbnail", response_model=dict)
async def create_thumbnail(
    video_id: UUID,
    timestamp: float = None,
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

    task = generate_thumbnail.delay(str(video.id), timestamp)

    return {"task_id": task.id, "status": "queued"}


@router.get("/{video_id}/jobs", response_model=list[JobResponse])
async def get_video_jobs(
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

    jobs_result = await db.execute(
        select(Job).where(Job.video_id == video.id).order_by(Job.created_at.desc())
    )
    jobs = jobs_result.scalars().all()

    return [JobResponse.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    video_result = await db.execute(
        select(Video).where(
            Video.id == job.video_id,
            Video.user_id == current_user.id
        )
    )
    if not video_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    return JobResponse.model_validate(job)
