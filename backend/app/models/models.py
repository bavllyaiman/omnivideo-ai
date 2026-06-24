import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, Float,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(20), default="free")
    credits_remaining = Column(Integer, default=100)
    credits_used_this_month = Column(Integer, default=0)
    storage_used_bytes = Column(Integer, default=0)
    storage_limit_bytes = Column(Integer, default=10737418240)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    owner = relationship("User", back_populates="projects")
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")


class Video(Base):
    __tablename__ = "videos"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    s3_key = Column(String(1000), nullable=True)
    status = Column(String(50), default="uploading")
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
    analysis = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    project = relationship("Project", back_populates="videos")
    transcript = relationship("Transcript", back_populates="video", uselist=False, cascade="all, delete-orphan")
    subtitles = relationship("Subtitle", back_populates="video", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="video", cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True)
    full_text = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    confidence = Column(Float, nullable=True)
    speakers = Column(JSON, default=[])
    segments = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), default=utcnow)
    video = relationship("Video", back_populates="transcript")
    translations = relationship("Translation", back_populates="transcript", cascade="all, delete-orphan")


class Translation(Base):
    __tablename__ = "translations"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    transcript_id = Column(String(36), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    translated_text = Column(Text, nullable=True)
    segments = Column(JSON, default=[])
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    transcript = relationship("Transcript", back_populates="translations")


class Subtitle(Base):
    __tablename__ = "subtitles"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=False)
    format = Column(String(20), default="srt")
    content = Column(Text, nullable=True)
    style = Column(JSON, default={})
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    video = relationship("Video", back_populates="subtitles")


class Export(Base):
    __tablename__ = "exports"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    format = Column(String(50), default="mp4")
    resolution = Column(String(20), default="1080p")
    quality = Column(String(20), default="high")
    status = Column(String(50), default="pending")
    s3_key = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)
    download_url = Column(Text, nullable=True)
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=utcnow)
    video = relationship("Video", back_populates="exports")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    progress = Column(Float, default=0.0)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
