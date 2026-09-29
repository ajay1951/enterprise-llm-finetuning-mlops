from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict


class BaseEvent(BaseModel):
    event_id: str
    event_type: str
    job_id: str
    timestamp: datetime
    sequence: int
    data: dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class MetricData(BaseModel):
    step: int
    epoch: float | None = None
    loss: float | None = None
    learning_rate: float | None = None
    samples_per_second: float | None = None
    tokens_per_second: float | None = None
    elapsed_time: float | None = None
    estimated_remaining_time: float | None = None


class LogData(BaseModel):
    level: str  # INFO, DEBUG, WARNING, ERROR
    message: str


class JobStatusData(BaseModel):
    status: str
    error_message: str | None = None


# Worker models (not part of job stream, but used generally)
class GPUMetric(BaseModel):
    id: int
    utilization: float
    memory_used_gb: float
    memory_total_gb: float
    temperature: float
    power_usage_w: float


class WorkerHeartbeat(BaseModel):
    worker_id: str
    status: str
    job_id: str | None = None
    gpu_count: int
    cpu_percent: float | None = None
    ram_used_gb: float | None = None
    gpu_metrics: list[GPUMetric] | None = None
