from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from app.models.models import SubscriptionTier, JobStatus, VideoStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: Optional[str] = None
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    subscription_tier: SubscriptionTier
    credits_remaining: int
    credits_used_this_month: int
    storage_used_bytes: int
    storage_limit_bytes: int
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefresh(BaseModel):
    refresh_token: str


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[dict] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    settings: Optional[dict]
    video_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoUploadRequest(BaseModel):
    project_id: UUID
    filename: str
    content_type: str = "video/mp4"
    file_size: Optional[int] = None
    source_type: str = "upload"
    source_url: Optional[str] = None


class VideoResponse(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    original_filename: Optional[str]
    status: VideoStatus
    duration: Optional[float]
    file_size: Optional[int]
    mime_type: Optional[str]
    resolution_width: Optional[int]
    resolution_height: Optional[int]
    fps: Optional[float]
    source_type: str
    thumbnail_url: Optional[str]
    proxy_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoAnalysisResponse(BaseModel):
    scenes: Optional[List[dict]] = None
    objects: Optional[List[dict]] = None
    people: Optional[List[dict]] = None
    emotions: Optional[List[dict]] = None
    moments: Optional[List[dict]] = None
    chapters: Optional[List[dict]] = None
    summary: Optional[str] = None
    viral_moments: Optional[List[dict]] = None


class TranscriptResponse(BaseModel):
    id: UUID
    full_text: Optional[str]
    language: Optional[str]
    confidence: Optional[float]
    speakers: Optional[List[dict]]
    segments: Optional[List[dict]]
    word_timestamps: Optional[List[dict]]
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptCreate(BaseModel):
    video_id: UUID


class TranslationCreate(BaseModel):
    transcript_id: UUID
    target_language: str


class TranslationResponse(BaseModel):
    id: UUID
    source_language: str
    target_language: str
    translated_text: Optional[str]
    segments: Optional[List[dict]]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SubtitleCreate(BaseModel):
    video_id: UUID
    language: str = "en"
    format: str = "srt"
    style: Optional[dict] = None


class SubtitleResponse(BaseModel):
    id: UUID
    language: str
    format: str
    content: Optional[str]
    style: Optional[dict]
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: UUID
    agent_name: str
    status: JobStatus
    progress: float
    result: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    video_id: UUID
    format: str = "mp4"
    resolution: str = "1080p"
    quality: str = "high"
    include_subtitles: bool = True
    include_overlays: bool = False
    custom_settings: Optional[dict] = None


class ExportResponse(BaseModel):
    id: UUID
    status: str
    format: str
    resolution: str
    quality: str
    file_size: Optional[int]
    duration: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class ShortCreate(BaseModel):
    video_id: UUID
    platform: str = "tiktok"
    title: Optional[str] = None


class ShortResponse(BaseModel):
    id: UUID
    title: Optional[str]
    platform: Optional[str]
    status: str
    duration: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class ThumbnailResponse(BaseModel):
    id: UUID
    s3_key: str
    timestamp: Optional[float]
    score: Optional[float]
    is_selected: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    amount: int
    currency: str = "usd"
    description: Optional[str] = None


class PaymentResponse(BaseModel):
    id: UUID
    amount: int
    currency: str
    status: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    tier: SubscriptionTier
    payment_method_id: Optional[str] = None


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: Optional[str]
    type: str
    is_read: bool
    link: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ContentRepurposeRequest(BaseModel):
    video_id: UUID
    platforms: List[str] = ["blog", "twitter", "linkedin", "instagram", "facebook"]
    tone: Optional[str] = "professional"
    custom_instructions: Optional[str] = None


class ContentRepurposeResponse(BaseModel):
    blog: Optional[str] = None
    twitter: Optional[List[str]] = None
    linkedin: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    newsletter: Optional[str] = None


class AgentProcessRequest(BaseModel):
    video_id: UUID
    agents: List[str] = ["video_understanding", "speech_recognition"]
    options: Optional[dict] = None


class DashboardStats(BaseModel):
    total_videos: int = 0
    total_projects: int = 0
    total_processing_hours: float = 0
    total_exports: int = 0
    credits_used: int = 0
    credits_remaining: int = 0


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: str
    workers: int
