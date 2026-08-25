from sqlalchemy import Column, String, DateTime, ForeignKey, func, Text, JSON, Integer
from sqlalchemy.orm import relationship
from backend.forgellm_api.db.session import Base
from backend.forgellm_api.db.models.project import generate_uuid

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False, unique=True)
    status = Column(String, default="created") # created, queued, starting, loading, ready, stopping, stopped, failed
    health_status = Column(String, default="unknown") # healthy, unhealthy, unknown
    
    serving_backend = Column(String, nullable=False) # transformers, vllm
    device = Column(String, nullable=False) # cuda, cpu
    port = Column(Integer, nullable=True) # internal assigned port for the worker to run on
    endpoint = Column(String, nullable=True) # full resolved endpoint for internal proxying
    
    configuration = Column(JSON, nullable=True) # max_model_len, max_new_tokens, temperature
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project")
    model_version = relationship("ModelVersion")
    events = relationship("DeploymentEvent", back_populates="deployment", cascade="all, delete-orphan")
    requests = relationship("InferenceRequest", back_populates="deployment")


class DeploymentEvent(Base):
    __tablename__ = "deployment_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    deployment_id = Column(String, ForeignKey("deployments.id"), nullable=False, index=True)
    
    event_type = Column(String, nullable=False)
    sequence = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    data = Column(JSON, nullable=True)

    deployment = relationship("Deployment", back_populates="events")


class InferenceRequest(Base):
    __tablename__ = "inference_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    deployment_id = Column(String, ForeignKey("deployments.id"), nullable=False, index=True)
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=False)
    
    status = Column(String, default="success") # success, error, cancelled
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    ttft_ms = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    deployment = relationship("Deployment", back_populates="requests")
