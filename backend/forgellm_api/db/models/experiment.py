from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from backend.forgellm_api.db.models.project import generate_uuid
from backend.forgellm_api.db.session import Base


class GatewayExperiment(Base):
    __tablename__ = "gateway_experiments"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    model_id = Column(String, ForeignKey("models.id"), nullable=False)

    name = Column(String, nullable=False)
    status = Column(String, default="DRAFT")  # DRAFT, RUNNING, PAUSED, COMPLETED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project")
    model = relationship("Model")
    variants = relationship(
        "ExperimentVariant", back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentVariant(Base):
    __tablename__ = "experiment_variants"

    id = Column(String, primary_key=True, default=generate_uuid)
    experiment_id = Column(
        String, ForeignKey("gateway_experiments.id"), nullable=False, index=True
    )
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=False)

    name = Column(String, nullable=False)  # e.g., "Model A"
    weight = Column(Integer, default=50)  # 0-100

    # Aggregated metrics cached from Redis
    requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    avg_latency_ms = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    fallback_count = Column(Integer, default=0)

    experiment = relationship("GatewayExperiment", back_populates="variants")
    model_version = relationship("ModelVersion")
