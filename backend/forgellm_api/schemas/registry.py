from pydantic import BaseModel, Field
from typing import Optional


class PromoteModelRequest(BaseModel):
    new_status: str = Field(
        ..., description="Target lifecycle status (e.g., 'staging', 'production')"
    )
    reason: Optional[str] = Field(None, description="Reason for promotion")


class RollbackModelRequest(BaseModel):
    target_version_id: str = Field(
        ..., description="The model_version_id to rollback to"
    )
    reason: Optional[str] = Field(None, description="Reason for rollback")


class ArchiveModelRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Reason for archiving")
