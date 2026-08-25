from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

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
    description: Optional[str] = None

class DatasetResponse(DatasetBase):
    id: str
    project_id: str
    created_at: datetime
    versions: List[DatasetVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)
