import json
from abc import ABC, abstractmethod
from pathlib import Path

from forgellm.experiments.metadata import ExperimentMetadata


class StorageInterface(ABC):
    @abstractmethod
    def save_experiment(self, metadata: ExperimentMetadata):
        pass
        
    @abstractmethod
    def get_experiment(self, experiment_id: str) -> ExperimentMetadata | None:
        pass
        
    @abstractmethod
    def list_experiments(self) -> list[ExperimentMetadata]:
        pass

class LocalFileStorage(StorageInterface):
    def __init__(self, base_dir: str = ".forgellm/experiments"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_exp_dir(self, experiment_id: str) -> Path:
        exp_dir = self.base_dir / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)
        return exp_dir

    def save_experiment(self, metadata: ExperimentMetadata):
        exp_dir = self._get_exp_dir(metadata.experiment_id)
        with open(exp_dir / "metadata.json", "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)
            
    def get_experiment(self, experiment_id: str) -> ExperimentMetadata | None:
        meta_path = self.base_dir / experiment_id / "metadata.json"
        if not meta_path.exists():
            return None
        with open(meta_path, "r") as f:
            data = json.load(f)
            return ExperimentMetadata.from_dict(data)
            
    def list_experiments(self) -> list[ExperimentMetadata]:
        if not self.base_dir.exists():
            return []
            
        experiments = []
        for d in self.base_dir.iterdir():
            if d.is_dir() and d.name.startswith("EXP-"):
                exp = self.get_experiment(d.name)
                if exp:
                    experiments.append(exp)
        
        experiments.sort(key=lambda x: x.experiment_id)
        return experiments
