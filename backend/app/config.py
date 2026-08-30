from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3000"

    # Database
    # Default SQLite for zero-install demos. Switch to Postgres for production:
    #   DATABASE_URL=postgresql://labelguard:labelguard@localhost:5432/labelguard
    DATABASE_URL: str = "sqlite:///./labelguard.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Object Storage (MinIO / S3)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "labelguard-media"
    MINIO_SECURE: bool = False

    # ML Worker URLs
    OCR_WORKER_URL: str = "http://localhost:8001"
    VLM_WORKER_URL: str = "http://localhost:8002"
    LAYOUT_WORKER_URL: str = "http://localhost:8003"

    # External VLM fallbacks
    GROQ_API_KEY: str = ""
    TOGETHER_API_KEY: str = ""

    # Auth
    JWT_SECRET: str = "change-me-to-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
