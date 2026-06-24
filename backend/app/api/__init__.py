from fastapi import APIRouter
from app.api import auth, projects, videos, transcripts, processing, dashboard, billing

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(videos.router)
api_router.include_router(transcripts.router)
api_router.include_router(processing.router)
api_router.include_router(dashboard.router)
api_router.include_router(billing.router)
