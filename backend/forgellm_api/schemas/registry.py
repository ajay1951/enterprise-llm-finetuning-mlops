from typing import Optional

from pydantic import BaseModel, Field


class PromoteModelRequest(BaseModel):
    new_status: str = Field(
        ..., description="Target lifecycle status (e.g., 'staging', 'production')"
    )
    reason: str | None = Field(None, description="Reason for promotion")


class RollbackModelRequest(BaseModel):
    target_version_id: str = Field(
        ..., description="The model_version_id to rollback to"
    )
    reason: str | None = Field(None, description="Reason for rollback")


class ArchiveModelRequest(BaseModel):
    reason: str | None = Field(None, description="Reason for archiving")
