from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./omnivideo.db")
REDIS_URL = os.getenv("REDIS_URL", "")

app = FastAPI(
    title="OmniVideo AI",
    version="1.0.0",
    description="AI-Powered Video Editing SaaS Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, projects, videos, transcripts, processing, dashboard, billing

app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(videos.router, prefix="/api/v1")
app.include_router(transcripts.router, prefix="/api/v1")
app.include_router(processing.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api")
async def root():
    return {"name": "OmniVideo AI", "version": "1.0.0", "docs": "/docs"}
