from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class OrganizationMemberResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
