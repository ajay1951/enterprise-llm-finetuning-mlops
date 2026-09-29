from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class APIKeyCreate(BaseModel):
    name: str
    organization_id: str
    project_id: Optional[str] = None
    scopes: Optional[str] = "models:inference"


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: str
    organization_id: str
    project_id: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    key: APIKeyResponse
    secret: str  # Only returned once
