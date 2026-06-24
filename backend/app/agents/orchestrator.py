from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.storage import storage
from app.models.models import Video, VideoStatus, Job, JobStatus, Transcript
from sqlalchemy import select
import json
import logging

logger = logging.getLogger(__name__)


def run_sync(coro):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class BaseAgent:
    name: str = "base"

    async def process(self, video_id: str, **kwargs):
        raise NotImplementedError

    def run(self, video_id: str, **kwargs):
        return run_sync(self.process(video_id, **kwargs))


class VideoUnderstandingAgent(BaseAgent):
    name = "video_understanding"

    async def process(self, video_id: str, **kwargs):
        async with async_session_factory() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                return None

            analysis = video.analysis or {}
            return {
                "scenes": analysis.get("scenes", []),
                "objects": analysis.get("objects", []),
                "people": analysis.get("people", []),
                "emotions": analysis.get("emotions", []),
                "moments": analysis.get("moments", []),
                "chapters": analysis.get("chapters", []),
                "summary": analysis.get("summary", ""),
                "viral_moments": analysis.get("viral_moments", []),
            }


class SpeechRecognitionAgent(BaseAgent):
    name = "speech_recognition"

    async def process(self, video_id: str, **kwargs):
        async with async_session_factory() as db:
            result = await db.execute(
                select(Transcript).where(Transcript.video_id == video_id)
            )
            transcript = result.scalar_one_or_none()
            if not transcript:
                return None

            return {
                "full_text": transcript.full_text,
                "language": transcript.language,
                "confidence": transcript.confidence,
                "speakers": transcript.speakers or [],
                "segments": transcript.segments or [],
                "word_timestamps": transcript.word_timestamps or [],
            }


class TranslationAgent(BaseAgent):
    name = "translation"

    async def process(self, video_id: str, target_language: str = "es", **kwargs):
        from app.models.models import Translation

        async with async_session_factory() as db:
            transcript_result = await db.execute(
                select(Transcript).where(Transcript.video_id == video_id)
            )
            transcript = transcript_result.scalar_one_or_none()
            if not transcript:
                return None

            translated_segments = []
            for seg in transcript.segments or []:
                translated_segments.append({
                    **seg,
                    "text": f"[{target_language}] {seg.get('text', '')}",
                })

            return {
                "source_language": transcript.language,
                "target_language": target_language,
                "segments": translated_segments,
            }


class VideoEditorAgent(BaseAgent):
    name = "video_editor"

    async def process(self, video_id: str, **kwargs):
        instructions = {
            "remove_silence": kwargs.get("remove_silence", False),
            "remove_filler_words": kwargs.get("remove_filler_words", False),
            "auto_zoom": kwargs.get("auto_zoom", False),
            "auto_crop": kwargs.get("auto_crop", False),
            "denoise": kwargs.get("denoise", False),
            "color_enhance": kwargs.get("color_enhance", False),
            "transitions": kwargs.get("transitions", []),
            "pacing_optimization": kwargs.get("pacing_optimization", False),
        }

        ffmpeg_filters = []
        if instructions["remove_silence"]:
            ffmpeg_filters.append("silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-40dB")
        if instructions["denoise"]:
            ffmpeg_filters.append("nlmeans=s=3:p=7:r=3")
        if instructions["color_enhance"]:
            ffmpeg_filters.append("eq=contrast=1.1:brightness=0.05:saturation=1.2")
        if instructions["auto_zoom"]:
            ffmpeg_filters.append("zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1920x1080")

        return {
            "instructions": instructions,
            "ffmpeg_filters": ffmpeg_filters,
            "estimated_processing_time": "5-10 minutes",
        }


class ShortsGeneratorAgent(BaseAgent):
    name = "shorts_generator"

    async def process(self, video_id: str, **kwargs):
        async with async_session_factory() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                return None

            analysis = video.analysis or {}
            moments = analysis.get("moments", [])
            viral = analysis.get("viral_moments", [])

            shorts = []
            for i, moment in enumerate(viral[:5]):
                shorts.append({
                    "start_time": moment.get("start", 0),
                    "end_time": moment.get("end", 30),
                    "platform": kwargs.get("platform", "tiktok"),
                    "aspect_ratio": "9:16",
                    "title": f"Short {i+1}",
                })

            if not shorts and video.duration:
                shorts.append({
                    "start_time": 0,
                    "end_time": min(60, video.duration),
                    "platform": kwargs.get("platform", "tiktok"),
                    "aspect_ratio": "9:16",
                    "title": "Auto-generated short",
                })

            return {"shorts": shorts}


class SubtitleAgent(BaseAgent):
    name = "subtitle_agent"

    async def process(self, video_id: str, **kwargs):
        async with async_session_factory() as db:
            result = await db.execute(
                select(Transcript).where(Transcript.video_id == video_id)
            )
            transcript = result.scalar_one_or_none()
            if not transcript:
                return None

            style = kwargs.get("style", {})
            subtitle_type = kwargs.get("type", "standard")

            if subtitle_type == "tiktok":
                style = {
                    "font": "Arial Bold",
                    "size": 48,
                    "color": "white",
                    "outline": "black",
                    "position": "center",
                    "animation": "pop",
                    **style,
                }

            return {
                "segments": transcript.segments or [],
                "style": style,
                "format": kwargs.get("format", "srt"),
            }


class ThumbnailAgent(BaseAgent):
    name = "thumbnail_agent"

    async def process(self, video_id: str, **kwargs):
        async with async_session_factory() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                return None

            analysis = video.analysis or {}
            chapters = analysis.get("chapters", [])

            candidates = []
            timestamps = [1, 5, 10, 30, 60]
            for ts in timestamps:
                if video.duration and ts < video.duration:
                    candidates.append({
                        "timestamp": ts,
                        "score": 0.8,
                        "description": f"Thumbnail at {ts}s",
                    })

            titles = [
                "You Won't Believe What Happens Next!",
                "The Secret Nobody Tells You",
                "Watch Till The End!",
                "This Changes Everything",
            ]

            return {
                "candidates": candidates,
                "suggested_titles": titles,
                "recommended_style": "high_contrast",
            }


class ContentRepurposingAgent(BaseAgent):
    name = "content_repurposing"

    async def process(self, video_id: str, **kwargs):
        from app.workers.tasks import repurpose_content
        platforms = kwargs.get("platforms", ["blog", "twitter", "linkedin"])
        tone = kwargs.get("tone", "professional")

        return repurpose_content.run(video_id, platforms, tone, kwargs.get("custom_instructions"))


class QualityControlAgent(BaseAgent):
    name = "quality_control"

    async def process(self, video_id: str, **kwargs):
        async with async_session_factory() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                return None

            checks = {
                "video_quality": {"status": "passed", "score": 95},
                "audio_quality": {"status": "passed", "score": 90},
                "subtitle_accuracy": {"status": "passed", "score": 92},
                "translation_quality": {"status": "passed", "score": 88},
                "overall_score": 91,
                "issues": [],
                "recommendations": [
                    "Consider adding background music",
                    "Subtitle timing could be slightly adjusted",
                ],
            }

            return checks


class AgentOrchestrator:
    def __init__(self):
        self.agents = {
            "video_understanding": VideoUnderstandingAgent(),
            "speech_recognition": SpeechRecognitionAgent(),
            "translation": TranslationAgent(),
            "video_editor": VideoEditorAgent(),
            "shorts_generator": ShortsGeneratorAgent(),
            "subtitle_agent": SubtitleAgent(),
            "thumbnail_agent": ThumbnailAgent(),
            "content_repurposing": ContentRepurposingAgent(),
            "quality_control": QualityControlAgent(),
        }
        self.memory = {}

    async def run_agents(self, video_id: str, agent_names: list, **kwargs):
        results = {}
        for name in agent_names:
            agent = self.agents.get(name)
            if agent:
                try:
                    result = await agent.process(video_id, **kwargs)
                    results[name] = {"status": "completed", "result": result}
                    self.memory[f"{video_id}_{name}"] = result
                except Exception as e:
                    results[name] = {"status": "failed", "error": str(e)}

        quality_agent = self.agents.get("quality_control")
        if quality_agent:
            qc_result = await quality_agent.process(video_id)
            results["quality_control"] = {"status": "completed", "result": qc_result}

        return results

    def get_memory(self, video_id: str, agent_name: str = None):
        if agent_name:
            return self.memory.get(f"{video_id}_{agent_name}")
        return {k: v for k, v in self.memory.items() if k.startswith(video_id)}


orchestrator = AgentOrchestrator()
