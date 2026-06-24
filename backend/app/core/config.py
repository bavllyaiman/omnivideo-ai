from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    APP_NAME: str = "OmniVideo AI"
    DEBUG: bool = False
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./omnivideo.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "omnivideo-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()
