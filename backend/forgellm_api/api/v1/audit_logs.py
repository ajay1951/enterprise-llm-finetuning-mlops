from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.db.models.user import User
from backend.forgellm_api.db.models.audit import AuditLog
from backend.forgellm_api.db.models.organization import OrganizationMember
from backend.forgellm_api.schemas.audit import AuditLogResponse
from backend.forgellm_api.api.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(
    organization_id: str,
    action: Optional[str] = None,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify ADMIN or OWNER membership
    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )

    if not membership or membership.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")

    query = db.query(AuditLog).filter(AuditLog.organization_id == organization_id)

    if action:
        query = query.filter(AuditLog.action == action)
    if project_id:
        query = query.filter(AuditLog.project_id == project_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    return query.order_by(AuditLog.created_at.desc()).limit(100).all()
