from sqlalchemy import Column, String, DateTime, func, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.forgellm_api.db.session import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(
        String, ForeignKey("organizations.id"), nullable=True, index=True
    )  # nullable for backwards compatibility initially
    name = Column(String, nullable=False, index=True)
    slug = Column(
        String, nullable=False, unique=True, index=True, default=generate_uuid
    )
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    datasets = relationship(
        "Dataset", back_populates="project", cascade="all, delete-orphan"
    )
    training_jobs = relationship(
        "TrainingJob", back_populates="project", cascade="all, delete-orphan"
    )
    models = relationship(
        "Model", back_populates="project", cascade="all, delete-orphan"
    )
    organization = relationship("Organization", back_populates="projects")
