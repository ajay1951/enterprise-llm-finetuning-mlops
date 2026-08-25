import json
from typing import Optional, Dict, Any
from forgellm.experiments.metadata import ExperimentMetadata
from forgellm.experiments.storage import StorageInterface, LocalFileStorage
from forgellm.hardware.detector import HardwareDetector
from forgellm.dataset.registry import DatasetRegistry
import subprocess
from datetime import datetime
import time

class ExperimentManager:
    def __init__(self, storage: Optional[StorageInterface] = None):
        self.storage = storage or LocalFileStorage()
        self.dataset_registry = DatasetRegistry()
        
    def _get_git_commit(self) -> str:
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            
            # Check if dirty
            status = subprocess.check_output(
                ["git", "status", "--porcelain"], 
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            
            if status:
                return f"{commit}-dirty"
            return commit
        except Exception:
            return "unknown"
            
    def _generate_exp_id(self) -> str:
        experiments = self.storage.list_experiments()
        if not experiments:
            return "EXP-000001"
            
        last_id = experiments[-1].experiment_id
        try:
            num = int(last_id.split("-")[1])
            return f"EXP-{num + 1:06d}"
        except (IndexError, ValueError):
            return f"EXP-{len(experiments) + 1:06d}"

    def create_experiment(self, 
                          model: str, 
                          dataset: str, 
                          dataset_version: str, 
                          method: str) -> ExperimentMetadata:
                          
        exp_id = self._generate_exp_id()
        hardware = HardwareDetector.detect()
        
        metadata = ExperimentMetadata(
            experiment_id=exp_id,
            model=model,
            dataset=dataset,
            dataset_version=dataset_version,
            method=method,
            status="created",
            git_commit=self._get_git_commit(),
            python_version=hardware.pytorch_version, # Close enough to Python env version tracking
            torch_version=hardware.pytorch_version,
            transformers_version="unknown", # We could import transformers and check __version__
            trl_version="unknown",
            peft_version="unknown",
            cuda_version=hardware.cuda_version,
            gpu=hardware.gpu_names[0] if hardware.gpu_count > 0 else "None"
        )
        
        try:
            import transformers
            metadata.transformers_version = transformers.__version__
        except ImportError:
            pass
            
        try:
            import trl
            metadata.trl_version = trl.__version__
        except ImportError:
            pass
            
        try:
            import peft
            metadata.peft_version = peft.__version__
        except ImportError:
            pass
            
        self.storage.save_experiment(metadata)
        return metadata
        
    def start_experiment(self, exp_id: str):
        metadata = self.storage.get_experiment(exp_id)
        if metadata:
            metadata.status = "running"
            self.storage.save_experiment(metadata)
            
    def mark_completed(self, exp_id: str, duration_seconds: float):
        metadata = self.storage.get_experiment(exp_id)
        if metadata:
            metadata.status = "completed"
            metadata.duration_seconds = duration_seconds
            self.storage.save_experiment(metadata)
            
    def mark_failed(self, exp_id: str):
        metadata = self.storage.get_experiment(exp_id)
        if metadata:
            metadata.status = "failed"
            self.storage.save_experiment(metadata)
