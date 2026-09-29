from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DatasetVersionResponse(BaseModel):
    id: str
    dataset_id: str
    version_tag: str
    status: str
    num_examples: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetBase(BaseModel):
    name: str
    description: str | None = None


class DatasetResponse(DatasetBase):
    id: str
    project_id: str
    created_at: datetime
    versions: list[DatasetVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)
