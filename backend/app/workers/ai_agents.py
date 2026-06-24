from app.workers.celery_app import celery_app
from app.agents.orchestrator import orchestrator
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.workers.ai_agents.run_agent_pipeline")
def run_agent_pipeline(self, video_id: str, agents: list, options: dict = None):
    options = options or {}

    async def _run():
        results = await orchestrator.run_agents(video_id, agents, **options)
        return results

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.ai_agents.run_video_understanding")
def run_video_understanding(self, video_id: str):
    async def _run():
        return await orchestrator.agents["video_understanding"].process(video_id)

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.ai_agents.run_speech_recognition")
def run_speech_recognition(self, video_id: str):
    async def _run():
        return await orchestrator.agents["speech_recognition"].process(video_id)

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.ai_agents.run_translation")
def run_translation(self, video_id: str, target_language: str = "es"):
    async def _run():
        return await orchestrator.agents["translation"].process(
            video_id, target_language=target_language
        )

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.ai_agents.run_video_editing")
def run_video_editing(self, video_id: str, **kwargs):
    async def _run():
        return await orchestrator.agents["video_editor"].process(video_id, **kwargs)

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.ai_agents.run_shorts_generation")
def run_shorts_generation(self, video_id: str, platform: str = "tiktok"):
    async def _run():
        return await orchestrator.agents["shorts_generator"].process(
            video_id, platform=platform
        )

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.ai_agents.run_quality_control")
def run_quality_control(self, video_id: str):
    async def _run():
        return await orchestrator.agents["quality_control"].process(video_id)

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
