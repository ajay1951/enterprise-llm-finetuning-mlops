from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, Union, List
from datetime import datetime

class BaseEvent(BaseModel):
    event_id: str
    event_type: str
    job_id: str
    timestamp: datetime
    sequence: int
    data: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)

class MetricData(BaseModel):
    step: int
    epoch: Optional[float] = None
    loss: Optional[float] = None
    learning_rate: Optional[float] = None
    samples_per_second: Optional[float] = None
    tokens_per_second: Optional[float] = None
    elapsed_time: Optional[float] = None
    estimated_remaining_time: Optional[float] = None

class LogData(BaseModel):
    level: str # INFO, DEBUG, WARNING, ERROR
    message: str

class JobStatusData(BaseModel):
    status: str
    error_message: Optional[str] = None

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
    job_id: Optional[str] = None
    gpu_count: int
    cpu_percent: Optional[float] = None
    ram_used_gb: Optional[float] = None
    gpu_metrics: Optional[List[GPUMetric]] = None
