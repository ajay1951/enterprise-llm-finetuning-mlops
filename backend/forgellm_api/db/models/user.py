from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from backend.forgellm_api.db.models.project import generate_uuid
from backend.forgellm_api.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")  # ACTIVE, SUSPENDED, DELETED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    organization_memberships = relationship(
        "OrganizationMember", back_populates="user", cascade="all, delete-orphan"
    )


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    key_prefix = Column(String, nullable=False)  # e.g. "sk-forgellm-abcd..."

    # Scopes - simple comma separated for now e.g. "models:read,models:inference"
    scopes = Column(String, default="models:inference")

    organization_id = Column(
        String, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    project = relationship("Project")
    user = relationship("User")
