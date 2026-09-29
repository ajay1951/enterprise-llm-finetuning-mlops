from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TrainingJobBase(BaseModel):
    model_name: str
    method: str = "qlora"
    preset: Optional[str] = None
    epochs: float = 1.0
    learning_rate: float = 2e-4
    lora_rank: int = 8


class TrainingJobCreate(TrainingJobBase):
    dataset_version_id: str


class TrainingJobResponse(TrainingJobBase):
    id: str
    project_id: str
    dataset_version_id: str
    status: str
    error_message: Optional[str] = None

    current_step: int
    total_steps: int
    current_epoch: float
    current_loss: Optional[float] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
