from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from backend.forgellm_api.db.models.project import generate_uuid
from backend.forgellm_api.db.session import Base


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    dataset_version_id = Column(
        String, ForeignKey("dataset_versions.id"), nullable=False
    )

    # Configuration
    model_name = Column(String, nullable=False)
    method = Column(String, default="qlora")
    preset = Column(String, nullable=True)
    epochs = Column(Float, default=1.0)
    learning_rate = Column(Float, default=2e-4)
    lora_rank = Column(Integer, default=8)

    # State Machine
    status = Column(
        String, default="queued", index=True
    )  # queued, running, evaluating, completed, failed, cancel_requested, cancelled
    error_message = Column(String, nullable=True)

    # Progress
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    current_epoch = Column(Float, default=0.0)
    current_loss = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="training_jobs")
    dataset_version = relationship("DatasetVersion", back_populates="training_jobs")
    experiment = relationship(
        "Experiment",
        back_populates="training_job",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String, primary_key=True, default=generate_uuid)
    training_job_id = Column(
        String, ForeignKey("training_jobs.id"), nullable=False, unique=True
    )

    # Store complete metadata snapshot
    configuration = Column(JSON, nullable=False)
    hardware = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    training_job = relationship("TrainingJob", back_populates="experiment")
    checkpoints = relationship(
        "Checkpoint", back_populates="experiment", cascade="all, delete-orphan"
    )
    model_version = relationship(
        "ModelVersion", back_populates="experiment", uselist=False
    )


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(String, primary_key=True, default=generate_uuid)
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=False)
    step = Column(Integer, nullable=False)
    path = Column(String, nullable=False)
    size_bytes = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    experiment = relationship("Experiment", back_populates="checkpoints")
