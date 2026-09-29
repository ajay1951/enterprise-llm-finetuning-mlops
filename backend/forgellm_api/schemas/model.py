from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class ModelImportRequest(BaseModel):
    name: str
    base_model: str
    local_path: str


class ModelVersionResponse(BaseModel):
    id: str
    version_tag: str
    base_model: str
    status: str
    lifecycle_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    versions: List[ModelVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)
