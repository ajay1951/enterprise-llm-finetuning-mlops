from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    organization_id: str | None
    project_id: str | None
    user_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    status: str
    details: Any | None
    created_at: datetime

    class Config:
        from_attributes = True
