from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from backend.forgellm_api.db.models.project import generate_uuid
from backend.forgellm_api.db.session import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="models")
    versions = relationship(
        "ModelVersion", back_populates="model", cascade="all, delete-orphan"
    )
    aliases = relationship(
        "ModelAlias", back_populates="model", cascade="all, delete-orphan"
    )
    routing_config = relationship(
        "RoutingConfig",
        uselist=False,
        back_populates="model",
        cascade="all, delete-orphan",
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, ForeignKey("models.id"), nullable=False, index=True)
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=True)

    version_tag = Column(String, nullable=False)
    base_model = Column(String, nullable=False)
    adapter_path = Column(String, nullable=False)
    artifact_uri = Column(String, nullable=True)
    tokenizer_uri = Column(String, nullable=True)

    # MLflow and Lineage
    training_run_id = Column(String, nullable=True)
    git_commit = Column(String, nullable=True)
    quality_score = Column(String, nullable=True)  # JSON representing quality gate

    status = Column(String, default="ready")  # ready, evaluating, failed
    lifecycle_status = Column(
        String, default="development"
    )  # development, staging, production, archived, rejected

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    model = relationship("Model", back_populates="versions")
    experiment = relationship(
        "Experiment", back_populates="model_version", foreign_keys=[experiment_id]
    )
    evaluations = relationship(
        "Evaluation", back_populates="model_version", cascade="all, delete-orphan"
    )
    deployments = relationship(
        "Deployment", back_populates="model_version", cascade="all, delete-orphan"
    )
    promotions = relationship(
        "ModelPromotionHistory",
        back_populates="model_version",
        cascade="all, delete-orphan",
    )


class ModelPromotionHistory(Base):
    __tablename__ = "model_promotion_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    model_version_id = Column(
        String, ForeignKey("model_versions.id"), nullable=False, index=True
    )

    previous_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    actor = Column(String, nullable=True)
    reason = Column(Text, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    model_version = relationship("ModelVersion", back_populates="promotions")


class ModelAlias(Base):
    __tablename__ = "model_aliases"

    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, ForeignKey("models.id"), nullable=False, index=True)
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=False)
    alias = Column(String, nullable=False, unique=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    model = relationship("Model", back_populates="aliases")
    model_version = relationship("ModelVersion")


class RoutingConfig(Base):
    __tablename__ = "routing_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, ForeignKey("models.id"), nullable=False, unique=True)
    primary_version_id = Column(String, ForeignKey("model_versions.id"), nullable=False)
    fallback_version_id = Column(String, ForeignKey("model_versions.id"), nullable=True)

    strategy = Column(
        String, default="LEAST_LOADED"
    )  # ROUND_ROBIN, LEAST_LOADED, WEIGHTED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    model = relationship("Model", back_populates="routing_config")
    primary_version = relationship("ModelVersion", foreign_keys=[primary_version_id])
    fallback_version = relationship("ModelVersion", foreign_keys=[fallback_version_id])


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String, primary_key=True, default=generate_uuid)
    model_version_id = Column(
        String, ForeignKey("model_versions.id"), nullable=False, index=True
    )

    status = Column(String, default="queued")  # queued, running, completed, failed
    metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    model_version = relationship("ModelVersion", back_populates="evaluations")
    results = relationship(
        "EvaluationResult", back_populates="evaluation", cascade="all, delete-orphan"
    )


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    evaluation_id = Column(
        String, ForeignKey("evaluations.id"), nullable=False, index=True
    )

    prompt = Column(Text, nullable=False)
    expected_response = Column(Text, nullable=True)
    base_response = Column(Text, nullable=False)
    ft_response = Column(Text, nullable=False)

    evaluation = relationship("Evaluation", back_populates="results")
