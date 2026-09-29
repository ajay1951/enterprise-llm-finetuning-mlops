import uuid
from typing import List, Dict, Any, Optional


class ComputeProviderError(Exception):
    pass


class ComputeInstanceStatus:
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    TERMINATED = "TERMINATED"
    ERROR = "ERROR"


class ComputeProvider:
    """
    Base abstraction for cloud compute providers (AWS, GCP, RunPod, etc.)
    """

    def create_worker(self, instance_type: str, region: str) -> str:
        raise NotImplementedError

    def terminate_worker(self, instance_id: str):
        raise NotImplementedError

    def start_worker(self, instance_id: str):
        raise NotImplementedError

    def stop_worker(self, instance_id: str):
        raise NotImplementedError

    def get_status(self, instance_id: str) -> str:
        raise NotImplementedError

    def list_instances(self) -> List[Dict[str, Any]]:
        raise NotImplementedError


class LocalProvider(ComputeProvider):
    """
    Implementation for local bare-metal / docker-compose environment.
    Cannot actually provision new hardware, returns mock data.
    """

    def __init__(self):
        self._instances = {}

    def create_worker(self, instance_type: str, region: str) -> str:
        instance_id = f"local-inst-{uuid.uuid4().hex[:8]}"
        self._instances[instance_id] = {
            "instance_id": instance_id,
            "type": instance_type,
            "region": region,
            "status": ComputeInstanceStatus.RUNNING,
        }
        return instance_id

    def terminate_worker(self, instance_id: str):
        if instance_id in self._instances:
            self._instances[instance_id]["status"] = ComputeInstanceStatus.TERMINATED

    def start_worker(self, instance_id: str):
        if instance_id in self._instances:
            self._instances[instance_id]["status"] = ComputeInstanceStatus.RUNNING

    def stop_worker(self, instance_id: str):
        if instance_id in self._instances:
            self._instances[instance_id]["status"] = ComputeInstanceStatus.STOPPED

    def get_status(self, instance_id: str) -> str:
        return self._instances.get(instance_id, {}).get(
            "status", ComputeInstanceStatus.ERROR
        )

    def list_instances(self) -> List[Dict[str, Any]]:
        return list(self._instances.values())


def get_compute_provider(provider_name: str = "local") -> ComputeProvider:
    # Future integration point for AWSProvider, GCPProvider, etc.
    if provider_name == "local":
        return LocalProvider()
    raise ValueError(f"Unknown compute provider: {provider_name}")
