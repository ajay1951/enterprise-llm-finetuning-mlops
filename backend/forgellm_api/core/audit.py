from sqlalchemy.orm import Session
from backend.forgellm_api.db.models.audit import AuditLog
from backend.forgellm_api.db.models.user import User
from typing import Optional, Any
from fastapi import Request


class AuditLogger:
    @staticmethod
    def log(
        db: Session,
        action: str,
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Any] = None,
        request: Optional[Request] = None,
    ):
        ip_address = None
        if request and request.client:
            ip_address = request.client.host

        audit = AuditLog(
            organization_id=organization_id,
            project_id=project_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            status=status,
            details=details,
        )
        db.add(audit)
        db.commit()
