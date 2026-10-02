from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ExperimentMetadata:
    experiment_id: str
    model: str
    dataset: str
    dataset_version: str
    method: str
    status: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    duration_seconds: float | None = None
    git_commit: str = "unknown"
    python_version: str = "unknown"
    torch_version: str = "unknown"
    transformers_version: str = "unknown"
    trl_version: str = "unknown"
    peft_version: str = "unknown"
    cuda_version: str = "unknown"
    gpu: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentMetadata":
        return cls(**data)
