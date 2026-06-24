import httpx
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Worker"])


@router.get("/status")
async def worker_status():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.WORKER_URL}/health")
            return {"worker": "online", "details": r.json()}
    except Exception:
        return {"worker": "offline", "message": "Worker not reachable"}


@router.post("/process/{video_id}")
async def request_processing(video_id: str, task_type: str = "analyze"):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{settings.WORKER_URL}/process", json={
                "video_id": video_id,
                "task_type": task_type,
            })
            return r.json()
    except Exception as e:
        return {"status": "error", "detail": str(e)}
