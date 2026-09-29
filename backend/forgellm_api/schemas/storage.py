from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ArtifactResponse(BaseModel):
    id: str
    project_id: str
    artifact_type: str
    uri: str
    size_bytes: int
    checksum: Optional[str]
    storage_provider: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class ArtifactManifestResponse(BaseModel):
    id: str
    artifact_id: str
    content: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True
