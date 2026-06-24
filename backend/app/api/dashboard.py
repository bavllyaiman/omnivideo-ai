from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.models import User, Video, Project, Export, Job
from app.schemas.schemas import (
    DashboardStats, NotificationResponse, ContentRepurposeRequest,
    ContentRepurposeResponse
)
from app.workers.tasks import repurpose_content

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    videos_result = await db.execute(
        select(func.count(Video.id)).where(Video.user_id == current_user.id)
    )
    total_videos = videos_result.scalar()

    projects_result = await db.execute(
        select(func.count(Project.id)).where(Project.user_id == current_user.id)
    )
    total_projects = projects_result.scalar()

    exports_result = await db.execute(
        select(func.count(Export.id))
        .join(Project)
        .where(Project.user_id == current_user.id)
    )
    total_exports = exports_result.scalar()

    return DashboardStats(
        total_videos=total_videos,
        total_projects=total_projects,
        total_processing_hours=0.0,
        total_exports=total_exports,
        credits_used=current_user.credits_used_this_month,
        credits_remaining=current_user.credits_remaining,
    )


@router.get("/notifications", response_model=list[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Notification
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)

    result = await db.execute(query.order_by(Notification.created_at.desc()).limit(50))
    notifications = result.scalars().all()

    return [NotificationResponse.model_validate(n) for n in notifications]


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Notification
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await db.flush()
    return {"status": "ok"}


@router.post("/repurpose", response_model=ContentRepurposeResponse)
async def repurpose_video_content(
    data: ContentRepurposeRequest,
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

    task = repurpose_content.delay(
        str(video.id),
        data.platforms,
        data.tone,
        data.custom_instructions,
    )

    return ContentRepurposeResponse(
        blog=None,
        twitter=None,
        linkedin=None,
        instagram=None,
        facebook=None,
        newsletter=None,
    )
