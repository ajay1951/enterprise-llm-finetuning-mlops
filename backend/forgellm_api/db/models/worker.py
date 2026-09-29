from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Float,
    ForeignKey,
    func,
    Text,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from backend.forgellm_api.db.session import Base
from backend.forgellm_api.db.models.project import generate_uuid


class Worker(Base):
    __tablename__ = "workers_registry"

    id = Column(String, primary_key=True, default=generate_uuid)
    worker_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    hostname = Column(String, nullable=False)
    status = Column(
        String, default="REGISTERING"
    )  # REGISTERING, ONLINE, BUSY, DRAINING, OFFLINE, ERROR
    worker_type = Column(String, nullable=False)  # training, inference, hybrid

    cpu_count = Column(Integer, default=0)
    ram_total = Column(Float, default=0.0)  # GB
    ram_available = Column(Float, default=0.0)  # GB
    gpu_count = Column(Integer, default=0)

    gpu_information = Column(JSON, nullable=True)
    software_version = Column(String, nullable=True)
    cuda_version = Column(String, nullable=True)
    driver_version = Column(String, nullable=True)

    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    region = Column(String, nullable=True)
    zone = Column(String, nullable=True)

    gpus = relationship(
        "WorkerGPU", back_populates="worker", cascade="all, delete-orphan"
    )
    job_assignments = relationship("JobAssignment", back_populates="worker")
    reservations = relationship("ResourceReservation", back_populates="worker")


class WorkerGPU(Base):
    __tablename__ = "worker_gpus"

    id = Column(String, primary_key=True, default=generate_uuid)
    worker_id = Column(
        String, ForeignKey("workers_registry.id"), nullable=False, index=True
    )
    gpu_index = Column(Integer, nullable=False)  # e.g. 0, 1
    uuid = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)

    memory_total = Column(Float, default=0.0)  # MB
    memory_used = Column(Float, default=0.0)  # MB
    utilization = Column(Float, default=0.0)  # percentage
    temperature = Column(Float, default=0.0)  # Celsius
    power = Column(Float, default=0.0)  # Watts

    status = Column(
        String, default="AVAILABLE"
    )  # AVAILABLE, ALLOCATED, BUSY, DRAINING, ERROR
    current_job_id = Column(String, nullable=True)

    worker = relationship("Worker", back_populates="gpus")
    reservations = relationship("ResourceReservation", back_populates="gpu")
