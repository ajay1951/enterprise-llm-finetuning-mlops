from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TrainingJobBase(BaseModel):
    model_name: str
    method: str = "qlora"
    preset: str | None = None
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
    error_message: str | None = None

    current_step: int
    total_steps: int
    current_epoch: float
    current_loss: float | None = None

    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
