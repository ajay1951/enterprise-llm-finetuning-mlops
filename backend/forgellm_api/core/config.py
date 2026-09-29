from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://forgellm:password123@localhost:5432/forgellm"
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_ROOT: str = ".forgellm/storage"
    DATASET_ROOT: str = ".forgellm/datasets"
    MODEL_ROOT: str = ".forgellm/models"
    LOG_LEVEL: str = "INFO"
    CELERY_TASK_TIMEOUT: int = 86400
    JWT_SECRET_KEY: str = (
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
