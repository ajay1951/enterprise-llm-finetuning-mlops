from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship
from backend.forgellm_api.db.session import Base
from backend.forgellm_api.db.models.project import generate_uuid


class Workload(Base):
    __tablename__ = "workloads"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(
        String, nullable=False, default="INFERENCE"
    )  # INFERENCE, TRAINING, EVALUATION
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=True)

    desired_replicas = Column(Integer, default=1)
    min_replicas = Column(Integer, default=1)
    max_replicas = Column(Integer, default=1)

    status = Column(
        String, default="PENDING"
    )  # PENDING, DEPLOYING, READY, DEGRADED, SCALING, FAILED, STOPPED
    strategy = Column(String, default="ROLLING")  # ROLLING, BLUE_GREEN

    resource_requirements = Column(
        JSON, nullable=True
    )  # e.g. {"gpu": 1, "cpu": 4, "ram_gb": 16}

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    replicas = relationship(
        "WorkloadReplica", back_populates="workload", cascade="all, delete-orphan"
    )
    autoscaling_policy = relationship(
        "AutoscalingPolicy",
        uselist=False,
        back_populates="workload",
        cascade="all, delete-orphan",
    )


class WorkloadReplica(Base):
    __tablename__ = "workload_replicas"

    id = Column(String, primary_key=True, default=generate_uuid)
    workload_id = Column(String, ForeignKey("workloads.id"), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("workers_registry.id"), nullable=True)
    gpu_id = Column(String, ForeignKey("worker_gpus.id"), nullable=True)

    status = Column(
        String, default="PENDING"
    )  # PENDING, STARTING, READY, UNHEALTHY, STOPPING, STOPPED, FAILED
    health_status = Column(String, default="UNKNOWN")  # HEALTHY, UNHEALTHY, UNKNOWN
    endpoint = Column(String, nullable=True)  # e.g. http://worker-ip:port

    restart_count = Column(Integer, default=0)

    started_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)

    workload = relationship("Workload", back_populates="replicas")
    worker = relationship("Worker")
    gpu = relationship("WorkerGPU")


class AutoscalingPolicy(Base):
    __tablename__ = "autoscaling_policies"

    id = Column(String, primary_key=True, default=generate_uuid)
    workload_id = Column(
        String, ForeignKey("workloads.id"), nullable=False, unique=True
    )

    enabled = Column(Boolean, default=False)
    target_gpu_utilization = Column(Float, default=70.0)
    target_requests_per_sec = Column(Float, default=10.0)

    scale_up_cooldown = Column(Integer, default=60)  # seconds
    scale_down_cooldown = Column(Integer, default=300)  # seconds

    last_scale_event_at = Column(DateTime(timezone=True), nullable=True)

    workload = relationship("Workload", back_populates="autoscaling_policy")


class ScalingEvent(Base):
    __tablename__ = "scaling_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    workload_id = Column(String, ForeignKey("workloads.id"), nullable=False, index=True)

    event_type = Column(
        String, nullable=False
    )  # SCALE_UP, SCALE_DOWN, RECOVERY, ROLLING_UPDATE
    previous_replicas = Column(Integer, nullable=False)
    new_replicas = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResourceQuota(Base):
    __tablename__ = "resource_quotas"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, unique=True)

    max_gpus = Column(Integer, default=2)
    max_cpu_cores = Column(Float, default=16.0)
    max_ram_gb = Column(Float, default=64.0)
    max_replicas = Column(Integer, default=4)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
