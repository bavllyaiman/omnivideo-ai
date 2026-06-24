"""initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('username', sa.String(100), unique=True, nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_superuser', sa.Boolean, default=False),
        sa.Column('subscription_tier', sa.String(20), default='free'),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True, unique=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('credits_remaining', sa.Integer, default=100),
        sa.Column('credits_used_this_month', sa.Integer, default=0),
        sa.Column('oauth_provider', sa.String(50), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('storage_used_bytes', sa.Integer, default=0),
        sa.Column('storage_limit_bytes', sa.Integer, default=10737418240),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('settings', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])

    # Videos table
    op.create_table(
        'videos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=True),
        sa.Column('s3_key', sa.String(1000), nullable=False),
        sa.Column('s3_bucket', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), default='uploading'),
        sa.Column('duration', sa.Float, nullable=True),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('resolution_width', sa.Integer, nullable=True),
        sa.Column('resolution_height', sa.Integer, nullable=True),
        sa.Column('fps', sa.Float, nullable=True),
        sa.Column('codec', sa.String(50), nullable=True),
        sa.Column('source_type', sa.String(50), default='upload'),
        sa.Column('source_url', sa.Text, nullable=True),
        sa.Column('thumbnail_url', sa.Text, nullable=True),
        sa.Column('proxy_url', sa.Text, nullable=True),
        sa.Column('analysis', JSONB, nullable=True),
        sa.Column('processing_settings', JSONB, default={}),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_videos_project_id', 'videos', ['project_id'])
    op.create_index('ix_videos_user_id', 'videos', ['user_id'])

    # Jobs table
    op.create_table(
        'jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('video_id', UUID(as_uuid=True), sa.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('progress', sa.Float, default=0.0),
        sa.Column('result', JSONB, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_jobs_video_id', 'jobs', ['video_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])

    # Transcripts table
    op.create_table(
        'transcripts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('video_id', UUID(as_uuid=True), sa.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('full_text', sa.Text, nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('speakers', JSONB, default=[]),
        sa.Column('segments', JSONB, default=[]),
        sa.Column('word_timestamps', JSONB, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Translations table
    op.create_table(
        'translations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('transcript_id', UUID(as_uuid=True), sa.ForeignKey('transcripts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_language', sa.String(10), nullable=False),
        sa.Column('target_language', sa.String(10), nullable=False),
        sa.Column('translated_text', sa.Text, nullable=True),
        sa.Column('segments', JSONB, default=[]),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Subtitles table
    op.create_table(
        'subtitles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('video_id', UUID(as_uuid=True), sa.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('language', sa.String(10), nullable=False),
        sa.Column('format', sa.String(20), default='srt'),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('style', JSONB, default={}),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Thumbnails table
    op.create_table(
        'thumbnails',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('video_id', UUID(as_uuid=True), sa.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('s3_key', sa.String(1000), nullable=False),
        sa.Column('timestamp', sa.Float, nullable=True),
        sa.Column('score', sa.Float, nullable=True),
        sa.Column('is_selected', sa.Boolean, default=False),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Shorts table
    op.create_table(
        'shorts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('original_video_id', UUID(as_uuid=True), sa.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('s3_key', sa.String(1000), nullable=True),
        sa.Column('duration', sa.Float, nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Exports table
    op.create_table(
        'exports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('video_id', UUID(as_uuid=True), sa.ForeignKey('videos.id', ondelete='SET NULL'), nullable=True),
        sa.Column('format', sa.String(50), default='mp4'),
        sa.Column('resolution', sa.String(20), default='1080p'),
        sa.Column('quality', sa.String(20), default='high'),
        sa.Column('s3_key', sa.String(1000), nullable=True),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('duration', sa.Float, nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('settings', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Payments table
    op.create_table(
        'payments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_payment_id', sa.String(255), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), default='usd'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('type', sa.String(50), default='info'),
        sa.Column('is_read', sa.Boolean, default=False),
        sa.Column('link', sa.Text, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', JSONB, default={}),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('payments')
    op.drop_table('exports')
    op.drop_table('shorts')
    op.drop_table('thumbnails')
    op.drop_table('subtitles')
    op.drop_table('translations')
    op.drop_table('transcripts')
    op.drop_table('jobs')
    op.drop_table('videos')
    op.drop_table('projects')
    op.drop_table('users')
