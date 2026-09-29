from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DeploymentConfiguration(BaseModel):
    max_model_len: int = 4096
    max_new_tokens: int = 512
    temperature: float = 0.7


class DeploymentCreate(BaseModel):
    model_version_id: str
    name: str
    backend: str = "transformers"
    device: str = "cuda"
    configuration: DeploymentConfiguration | None = None


class DeploymentResponse(BaseModel):
    id: str
    project_id: str
    model_version_id: str
    name: str
    status: str
    health_status: str
    serving_backend: str
    device: str
    port: int | None
    endpoint: str | None
    configuration: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    stopped_at: datetime | None

    class Config:
        orm_mode = True


class InferenceRequest(BaseModel):
    model: str
    messages: list[dict[str, str]]
    temperature: float | None = 0.7
    max_tokens: int | None = 512
    stream: bool | None = False


class CompletionRequest(BaseModel):
    model: str
    prompt: str
    temperature: float | None = 0.7
    max_tokens: int | None = 512
    stream: bool | None = False
