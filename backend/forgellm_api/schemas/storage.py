from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    id: str
    project_id: str
    artifact_type: str
    uri: str
    size_bytes: int
    checksum: str | None
    storage_provider: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class ArtifactManifestResponse(BaseModel):
    id: str
    artifact_id: str
    content: dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True
