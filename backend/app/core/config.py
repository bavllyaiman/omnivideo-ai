from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "OmniVideo AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/omnivideo"
    )
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/omnivideo"
    )

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "omnivideo-uploads")
    AWS_S3_REGION: str = os.getenv("AWS_S3_REGION", "us-east-1")
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL")
    CLOUDFLARE_R2_ACCOUNT_ID: Optional[str] = os.getenv("CLOUDFLARE_R2_ACCOUNT_ID")
    CLOUDFLARE_R2_ACCESS_KEY: Optional[str] = os.getenv("CLOUDFLARE_R2_ACCESS_KEY")
    CLOUDFLARE_R2_SECRET_KEY: Optional[str] = os.getenv("CLOUDFLARE_R2_SECRET_KEY")
    CLOUDFLARE_R2_BUCKET: Optional[str] = os.getenv("CLOUDFLARE_R2_BUCKET")
    CLOUDFLARE_R2_ENDPOINT: Optional[str] = os.getenv("CLOUDFLARE_R2_ENDPOINT")

    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GITHUB_CLIENT_ID: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET")

    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_MONTHLY: Optional[str] = os.getenv("STRIPE_PRICE_MONTHLY")
    STRIPE_PRICE_YEARLY: Optional[str] = os.getenv("STRIPE_PRICE_YEARLY")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")

    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "ffprobe")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/omnivideo")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 * 1024  # 10GB

    CORS_ORIGINS: list = ["http://localhost:3000", "https://omnivideo.ai"]

    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
