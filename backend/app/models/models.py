import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey,
    JSON, Enum as SAEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoStatus(str, enum.Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    PROCESSING = "processing"
    PROCESSED = "processed"
    EXPORTING = "exporting"
    EXPORTED = "exported"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    subscription_tier = Column(SAEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    credits_remaining = Column(Integer, default=100)
    credits_used_this_month = Column(Integer, default=0)

    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(255), nullable=True)

    storage_used_bytes = Column(Integer, default=0)
    storage_limit_bytes = Column(Integer, default=10 * 1024 * 1024 * 1024)  # 10GB

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    settings = Column(JSONB, default={})
    metadata_ = Column("metadata", JSONB, default={})

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="projects")
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
    )


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    s3_key = Column(String(1000), nullable=False)
    s3_bucket = Column(String(255), nullable=True)
    status = Column(SAEnum(VideoStatus), default=VideoStatus.UPLOADING)
    duration = Column(Float, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    resolution_width = Column(Integer, nullable=True)
    resolution_height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    codec = Column(String(50), nullable=True)
    source_type = Column(String(50), default="upload")
    source_url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    proxy_url = Column(Text, nullable=True)
    analysis = Column(JSONB, nullable=True)
    processing_settings = Column(JSONB, default={})
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="videos")
    jobs = relationship("Job", back_populates="video", cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="video", uselist=False, cascade="all, delete-orphan")
    subtitles = relationship("Subtitle", back_populates="video", cascade="all, delete-orphan")
    thumbnails = relationship("Thumbnail", back_populates="video", cascade="all, delete-orphan")
    shorts = relationship("Short", back_populates="original_video", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_videos_project_id", "project_id"),
        Index("ix_videos_user_id", "user_id"),
    )


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    status = Column(SAEnum(JobStatus), default=JobStatus.PENDING)
    priority = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    video = relationship("Video", back_populates="jobs")

    __table_args__ = (
        Index("ix_jobs_video_id", "video_id"),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_agent_name", "agent_name"),
    )


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True)
    full_text = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    confidence = Column(Float, nullable=True)
    speakers = Column(JSONB, default=[])
    segments = Column(JSONB, default=[])
    word_timestamps = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    video = relationship("Video", back_populates="transcript")
    translations = relationship("Translation", back_populates="transcript", cascade="all, delete-orphan")


class Translation(Base):
    __tablename__ = "translations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcript_id = Column(UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    translated_text = Column(Text, nullable=True)
    segments = Column(JSONB, default=[])
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    transcript = relationship("Transcript", back_populates="translations")


class Subtitle(Base):
    __tablename__ = "subtitles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=False)
    format = Column(String(20), default="srt")
    content = Column(Text, nullable=True)
    style = Column(JSONB, default={})
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    video = relationship("Video", back_populates="subtitles")


class Thumbnail(Base):
    __tablename__ = "thumbnails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    s3_key = Column(String(1000), nullable=False)
    timestamp = Column(Float, nullable=True)
    score = Column(Float, nullable=True)
    is_selected = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    video = relationship("Video", back_populates="thumbnails")


class Short(Base):
    __tablename__ = "shorts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=True)
    s3_key = Column(String(1000), nullable=True)
    duration = Column(Float, nullable=True)
    platform = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    original_video = relationship("Video", back_populates="shorts")


class Export(Base):
    __tablename__ = "exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    format = Column(String(50), default="mp4")
    resolution = Column(String(20), default="1080p")
    quality = Column(String(20), default="high")
    s3_key = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)
    status = Column(String(50), default="pending")
    settings = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="exports")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stripe_payment_id = Column(String(255), nullable=True)
    stripe_invoice_id = Column(String(255), nullable=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(50), default="pending")
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="payments")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    link = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSONB, default={})
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
    )
