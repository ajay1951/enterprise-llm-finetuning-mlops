from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class GPUInfo(BaseModel):
    gpu_index: int
    uuid: str
    name: str
    memory_total: float
    memory_used: float = 0.0
    utilization: float = 0.0
    temperature: float = 0.0
    power: float = 0.0
    status: Optional[str] = "AVAILABLE"
    current_job_id: Optional[str] = None


class WorkerRegisterRequest(BaseModel):
    worker_id: str
    hostname: str
    worker_type: str
    cpu_count: int
    ram_total: float
    gpu_count: int
    gpus: List[GPUInfo] = []
    software_version: Optional[str] = None
    cuda_version: Optional[str] = None
    driver_version: Optional[str] = None
    region: Optional[str] = None
    zone: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class WorkerHeartbeatRequest(BaseModel):
    status: str
    ram_available: float
    gpus: List[GPUInfo] = []
    active_jobs: List[str] = []


class WorkerResponse(BaseModel):
    id: str
    worker_id: str
    name: Optional[str]
    hostname: str
    status: str
    worker_type: str
    cpu_count: int
    ram_total: float
    ram_available: float
    gpu_count: int
    software_version: Optional[str]
    last_heartbeat: Optional[datetime]
    registered_at: datetime
    gpus: List[GPUInfo] = []

    class Config:
        from_attributes = True


class GPUInfoConfig:
    pass


GPUInfo.model_config = {"from_attributes": True}
