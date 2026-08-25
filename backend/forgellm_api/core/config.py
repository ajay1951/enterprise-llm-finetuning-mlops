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

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
