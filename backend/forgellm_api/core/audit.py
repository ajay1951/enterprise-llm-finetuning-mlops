from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from backend.forgellm_api.db.models.audit import AuditLog
from backend.forgellm_api.db.models.user import User


class AuditLogger:
    @staticmethod
    def log(
        db: Session,
        action: str,
        organization_id: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        status: str = "SUCCESS",
        details: Any | None = None,
        request: Request | None = None,
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
