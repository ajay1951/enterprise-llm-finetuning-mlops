from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: str
    organization_id: Optional[str]
    project_id: Optional[str]
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    status: str
    details: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True
