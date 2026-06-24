import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI(title="OmniVideo AI", version="1.0.0", docs_url="/docs")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

_db_ok = False

def load_routes():
    from app.api.auth import router as r1
    from app.api.projects import router as r2
    from app.api.videos import router as r3
    from app.api.transcripts import router as r4
    from app.api.processing import router as r5
    from app.api.dashboard import router as r6
    from app.api.billing import router as r7
    for r in [r1, r2, r3, r4, r5, r6, r7]:
        app.include_router(r, prefix="/api/v1")

load_routes()

@app.get("/api/health")
async def health():
    global _db_ok
    if not _db_ok:
        try:
            from app.core.database import engine, Base
            from app.models import models
            async with engine.begin() as c:
                await c.run_sync(Base.metadata.create_all)
            _db_ok = True
        except Exception as e:
            return {"status": "error", "detail": str(e)}
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"name": "OmniVideo AI", "status": "running"}

handler = Mangum(app)
