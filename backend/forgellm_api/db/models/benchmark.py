from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer, Float, JSON
from sqlalchemy.orm import relationship
from backend.forgellm_api.db.session import Base
from backend.forgellm_api.db.models.project import generate_uuid


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    status = Column(String, default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED
    dataset_uri = Column(
        String, nullable=True
    )  # Optional dataset used for benchmarking

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project")
    results = relationship(
        "BenchmarkResult", back_populates="benchmark_run", cascade="all, delete-orphan"
    )


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    benchmark_run_id = Column(
        String, ForeignKey("benchmark_runs.id"), nullable=False, index=True
    )
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=False)

    # Metrics
    total_requests = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_latency_ms = Column(Integer, default=0)
    p50_latency_ms = Column(Integer, default=0)
    p95_latency_ms = Column(Integer, default=0)
    p99_latency_ms = Column(Integer, default=0)
    ttft_ms = Column(Integer, default=0)  # Time to First Token
    tokens_per_second = Column(Float, default=0.0)

    error_message = Column(String, nullable=True)

    benchmark_run = relationship("BenchmarkRun", back_populates="results")
    model_version = relationship("ModelVersion")
