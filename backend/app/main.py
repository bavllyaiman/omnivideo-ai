from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

_db_initialized = False


async def ensure_db():
    global _db_initialized
    if not _db_initialized:
        try:
            from app.core.database import engine, Base
            from app.models.models import User, Project, Video, Transcript, Translation, Subtitle, Export
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            _db_initialized = True
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"DB init error: {e}")


@app.middleware("http")
async def db_middleware(request: Request, call_next):
    await ensure_db()
    response = await call_next(request)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


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
    await ensure_db()
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api")
async def root():
    return {"name": "OmniVideo AI", "version": "1.0.0", "docs": "/docs"}
