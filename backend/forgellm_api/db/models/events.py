from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.forgellm_api.db.session import Base

class JobEvent(Base):
    __tablename__ = "job_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("training_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False) # e.g. training.started, training.completed
    sequence = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    data = Column(JSON, nullable=True)

class TrainingMetric(Base):
    __tablename__ = "training_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("training_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    sequence = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    step = Column(Integer, nullable=False)
    epoch = Column(Float, nullable=True)
    loss = Column(Float, nullable=True)
    learning_rate = Column(Float, nullable=True)
    samples_per_second = Column(Float, nullable=True)
    tokens_per_second = Column(Float, nullable=True)

class TrainingLog(Base):
    __tablename__ = "training_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("training_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    sequence = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    level = Column(String, index=True, nullable=False) # INFO, DEBUG, WARNING, ERROR
    message = Column(Text, nullable=False)

class WorkerMetric(Base):
    __tablename__ = "worker_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    worker_id = Column(String, ForeignKey("workers_registry.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    cpu_percent = Column(Float, nullable=True)
    ram_used_gb = Column(Float, nullable=True)
    gpu_metrics = Column(JSON, nullable=True) # Array of objects for each GPU: {id: 0, util: 94, mem_used: 18.2, temp: 71}
