from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


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
    description: str | None = None
    created_at: datetime
    versions: list[ModelVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)
