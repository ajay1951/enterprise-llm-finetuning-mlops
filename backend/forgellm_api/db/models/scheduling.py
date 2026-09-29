from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from backend.forgellm_api.db.models.project import generate_uuid
from backend.forgellm_api.db.session import Base


class JobAssignment(Base):
    __tablename__ = "job_assignments"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(
        String, nullable=False, index=True
    )  # ID of training job or deployment
    job_type = Column(String, nullable=False)  # training, inference
    worker_id = Column(
        String, ForeignKey("workers_registry.id"), nullable=False, index=True
    )

    status = Column(
        String, default="QUEUED"
    )  # QUEUED, ASSIGNED, RUNNING, COMPLETED, FAILED, CANCELLED

    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    worker = relationship("Worker", back_populates="job_assignments")


class ResourceReservation(Base):
    __tablename__ = "resource_reservations"

    id = Column(String, primary_key=True, default=generate_uuid)
    worker_id = Column(
        String, ForeignKey("workers_registry.id"), nullable=False, index=True
    )
    gpu_id = Column(String, ForeignKey("worker_gpus.id"), nullable=True, index=True)
    job_id = Column(String, nullable=False, index=True)

    status = Column(String, default="ACTIVE")  # ACTIVE, RELEASED, EXPIRED
    cpu_cores_reserved = Column(Float, default=0.0)
    ram_gb_reserved = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    worker = relationship("Worker", back_populates="reservations")
    gpu = relationship("WorkerGPU", back_populates="reservations")


class ComputeInstance(Base):
    __tablename__ = "compute_instances"

    id = Column(String, primary_key=True, default=generate_uuid)
    instance_id = Column(String, nullable=False, unique=True)
    provider = Column(String, nullable=False)  # LocalProvider, AWSProvider
    region = Column(String, nullable=True)
    instance_type = Column(String, nullable=True)
    status = Column(String, default="STARTING")

    gpu_type = Column(String, nullable=True)
    gpu_count = Column(Float, default=0)
    vram = Column(Float, default=0)
    cpu = Column(Float, default=0)
    ram = Column(Float, default=0)

    hourly_cost_estimate = Column(Float, default=0.0)
    worker_id = Column(String, ForeignKey("workers_registry.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
