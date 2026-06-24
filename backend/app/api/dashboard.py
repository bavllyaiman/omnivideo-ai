from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Video, Project, Export

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    videos = (await db.execute(select(func.count(Video.id)).where(Video.user_id == user.id))).scalar()
    projects = (await db.execute(select(func.count(Project.id)).where(Project.user_id == user.id))).scalar()
    exports = (await db.execute(select(func.count(Export.id)).join(Project).where(Project.user_id == user.id))).scalar()
    return {"total_videos": videos, "total_projects": projects, "total_exports": exports or 0, "credits_used": user.credits_used_this_month, "credits_remaining": user.credits_remaining}


@router.post("/repurpose")
async def repurpose(video_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video = (await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))).scalar_one_or_none()
    if not video:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Video not found")
    return {
        "blog": "# Blog Post\n\nBased on the video content, here are the key insights and takeaways that can help you improve your video editing workflow with AI-powered tools.",
        "twitter": ["Check out our latest AI video editing tutorial! Learn how to automate your workflow with intelligent agents.", "AI is transforming video editing. Here's how you can leverage it for your content creation."],
        "linkedin": "Excited to share our latest guide on AI-powered video editing. The future of content creation is here, and it's automated.",
        "instagram": "Video highlights: AI-powered editing that saves you hours. Transform your content creation workflow today.",
        "facebook": "We just released a comprehensive guide on AI video editing. Learn how our multi-agent system can help you create better content faster.",
    }
