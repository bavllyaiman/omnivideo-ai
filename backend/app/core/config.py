from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    APP_NAME: str = "OmniVideo AI"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-in-production-omnivideo-2024")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "omnivideo")
    AWS_S3_ENDPOINT_URL: str = os.getenv("AWS_S3_ENDPOINT_URL", "")
    AWS_S3_REGION: str = os.getenv("AWS_S3_REGION", "auto")

    WORKER_URL: str = os.getenv("WORKER_URL", "http://localhost:8001")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()
