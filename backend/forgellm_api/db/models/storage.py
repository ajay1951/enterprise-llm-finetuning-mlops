from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Text, JSON
from sqlalchemy.orm import relationship
from backend.forgellm_api.db.session import Base
from backend.forgellm_api.db.models.project import generate_uuid

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    
    artifact_type = Column(String, nullable=False) # dataset, checkpoint, adapter, model, tokenizer, evaluation, log
    uri = Column(String, nullable=False) # e.g. s3://forgellm/projects/project-123/models/v1
    size_bytes = Column(Integer, default=0)
    checksum = Column(String, nullable=True) # SHA-256
    storage_provider = Column(String, default="local") # local, s3
    
    status = Column(String, default="ACTIVE") # ACTIVE, ARCHIVED, DELETED, CORRUPTED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project")
    manifest = relationship("ArtifactManifest", back_populates="artifact", uselist=False, cascade="all, delete-orphan")


class ArtifactManifest(Base):
    __tablename__ = "artifact_manifests"

    id = Column(String, primary_key=True, default=generate_uuid)
    artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=False, unique=True)
    
    content = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    artifact = relationship("Artifact", back_populates="manifest")
