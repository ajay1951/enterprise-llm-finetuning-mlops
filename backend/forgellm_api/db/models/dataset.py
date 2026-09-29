from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from backend.forgellm_api.db.models.project import generate_uuid
from backend.forgellm_api.db.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="datasets")
    versions = relationship(
        "DatasetVersion", back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    version_tag = Column(String, nullable=False)  # e.g. "v1"
    original_path = Column(String, nullable=False)
    processed_path = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, valid, invalid, formatted
    num_examples = Column(Integer, default=0)
    file_hash = Column(String, nullable=True)

    # Lineage and Versioning
    s3_uri = Column(String, nullable=True)
    commit_hash = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", back_populates="versions")
    training_jobs = relationship("TrainingJob", back_populates="dataset_version")
