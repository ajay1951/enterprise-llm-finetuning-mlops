from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GPUInfo(BaseModel):
    gpu_index: int
    uuid: str
    name: str
    memory_total: float
    memory_used: float = 0.0
    utilization: float = 0.0
    temperature: float = 0.0
    power: float = 0.0
    status: str | None = "AVAILABLE"
    current_job_id: str | None = None


class WorkerRegisterRequest(BaseModel):
    worker_id: str
    hostname: str
    worker_type: str
    cpu_count: int
    ram_total: float
    gpu_count: int
    gpus: list[GPUInfo] = []
    software_version: str | None = None
    cuda_version: str | None = None
    driver_version: str | None = None
    region: str | None = None
    zone: str | None = None
    metadata_json: dict[str, Any] | None = None


class WorkerHeartbeatRequest(BaseModel):
    status: str
    ram_available: float
    gpus: list[GPUInfo] = []
    active_jobs: list[str] = []


class WorkerResponse(BaseModel):
    id: str
    worker_id: str
    name: str | None
    hostname: str
    status: str
    worker_type: str
    cpu_count: int
    ram_total: float
    ram_available: float
    gpu_count: int
    software_version: str | None
    last_heartbeat: datetime | None
    registered_at: datetime
    gpus: list[GPUInfo] = []

    class Config:
        from_attributes = True


class GPUInfoConfig:
    pass


GPUInfo.model_config = {"from_attributes": True}
