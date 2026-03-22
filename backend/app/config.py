"""Application configuration from environment."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Proctor"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://proctor:proctor@localhost:5432/proctor"

    # LiveKit
    livekit_url: str = "wss://your-livekit-server.livekit.cloud"
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # JWT for our API (proctor login, etc.)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # S3 / R2 / MinIO (recordings)
    s3_endpoint_url: str | None = None  # e.g. http://localhost:9000 for MinIO
    s3_region: str = "us-east-1"
    s3_bucket: str = "proctor-recordings"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_use_ssl: bool = True

    # Redis (optional, for pub/sub and rate limiting)
    redis_url: str | None = None

    # Proctor agent (automated bot that joins room and runs face detection)
    agent_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
