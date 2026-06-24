import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OmniVideo AI", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_db_initialized = False
_db_dropped = False


def load_routes():
    from app.api.auth import router as r1
    from app.api.projects import router as r2
    from app.api.videos import router as r3
    from app.api.transcripts import router as r4
    from app.api.processing import router as r5
    from app.api.dashboard import router as r6
    from app.api.billing import router as r7
    from app.api.worker_api import router as r8
    for prefix, r in [
        ("/api/v1/auth", r1), ("/api/v1/projects", r2), ("/api/v1/videos", r3),
        ("/api/v1/transcripts", r4), ("/api/v1/processing", r5),
        ("/api/v1/dashboard", r6), ("/api/v1/billing", r7), ("/api/worker", r8),
    ]:
        app.include_router(r, prefix=prefix)

load_routes()


@app.middleware("http")
async def db_init(request, call_next):
    global _db_initialized
    if not _db_initialized:
        try:
            from app.core.database import engine, Base
            from app.models import models
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            _db_initialized = True
        except Exception as e:
            logger.error(f"DB init error: {e}")
    return await call_next(request)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "service": "omnivideo-api"}

@app.get("/")
async def root():
    return {"name": "OmniVideo AI", "version": "1.0.0", "docs": "/docs"}

handler = Mangum(app)
