from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str
    organization_id: str
    project_id: str | None = None
    scopes: str | None = "models:inference"


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: str
    organization_id: str
    project_id: str | None
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    key: APIKeyResponse
    secret: str  # Only returned once
