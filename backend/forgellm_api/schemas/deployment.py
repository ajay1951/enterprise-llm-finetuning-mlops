from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class DeploymentConfiguration(BaseModel):
    max_model_len: int = 4096
    max_new_tokens: int = 512
    temperature: float = 0.7

class DeploymentCreate(BaseModel):
    model_version_id: str
    name: str
    backend: str = "transformers"
    device: str = "cuda"
    configuration: Optional[DeploymentConfiguration] = None

class DeploymentResponse(BaseModel):
    id: str
    project_id: str
    model_version_id: str
    name: str
    status: str
    health_status: str
    serving_backend: str
    device: str
    port: Optional[int]
    endpoint: Optional[str]
    configuration: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]

    class Config:
        orm_mode = True

class InferenceRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False
