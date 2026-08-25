from sqlalchemy import Column, String, DateTime, func, JSON
from backend.forgellm_api.db.session import Base
from backend.forgellm_api.db.models.project import generate_uuid

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, index=True, nullable=True)
    project_id = Column(String, index=True, nullable=True)
    user_id = Column(String, index=True, nullable=True)
    
    action = Column(String, nullable=False, index=True) # e.g. USER_LOGIN, PROJECT_CREATED, MODEL_DEPLOYED
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    
    ip_address = Column(String, nullable=True)
    status = Column(String, default="SUCCESS") # SUCCESS, FAILED
    
    details = Column(JSON, nullable=True) # additional context (never secrets)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
