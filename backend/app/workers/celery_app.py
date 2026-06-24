from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "omnivideo",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_concurrency=4,
    task_routes={
        "app.workers.tasks.*": {"queue": "video_processing"},
        "app.workers.ai_agents.*": {"queue": "ai_agents"},
    },
    beat_schedule={
        "cleanup-temp-files": {
            "task": "app.workers.tasks.cleanup_temp_files",
            "schedule": 3600.0,
        },
        "check-stuck-jobs": {
            "task": "app.workers.tasks.check_stuck_jobs",
            "schedule": 300.0,
        },
    },
)

celery_app.autodiscover_tasks(["app.workers"])
