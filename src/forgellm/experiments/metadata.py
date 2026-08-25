from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class ExperimentMetadata:
    experiment_id: str
    model: str
    dataset: str
    dataset_version: str
    method: str
    status: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    duration_seconds: Optional[float] = None
    git_commit: str = "unknown"
    python_version: str = "unknown"
    torch_version: str = "unknown"
    transformers_version: str = "unknown"
    trl_version: str = "unknown"
    peft_version: str = "unknown"
    cuda_version: str = "unknown"
    gpu: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentMetadata":
        return cls(**data)
