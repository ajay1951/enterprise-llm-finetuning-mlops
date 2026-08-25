from abc import ABC, abstractmethod
from typing import Dict, Any

class OrchestratorProvider(ABC):
    """
    Abstract base class for container orchestration.
    Allows ForgeLLM to schedule inference workloads locally (Docker/Process) or via Kubernetes.
    """
    
    @abstractmethod
    async def create_deployment(self, name: str, image: str, replicas: int, env: Dict[str, str], resources: Dict[str, Any]):
        pass
        
    @abstractmethod
    async def delete_deployment(self, name: str):
        pass
        
    @abstractmethod
    async def scale_deployment(self, name: str, replicas: int):
        pass

class LocalOrchestrator(OrchestratorProvider):
    """
    Local implementation that relies on the ForgeLLM worker agent architecture 
    to spawn model servers on bare-metal or local docker environments.
    """
    async def create_deployment(self, name: str, image: str, replicas: int, env: Dict[str, str], resources: Dict[str, Any]):
        # Locally, this maps to Workloads + Worker Agents handling the execution
        print(f"[LocalOrchestrator] Deployment {name} requested with {replicas} replicas.")
        
    async def delete_deployment(self, name: str):
        print(f"[LocalOrchestrator] Deleting deployment {name}.")
        
    async def scale_deployment(self, name: str, replicas: int):
        print(f"[LocalOrchestrator] Scaling deployment {name} to {replicas}.")

class KubernetesOrchestrator(OrchestratorProvider):
    """
    Future implementation to talk to K8s API directly.
    """
    async def create_deployment(self, name: str, image: str, replicas: int, env: Dict[str, str], resources: Dict[str, Any]):
        raise NotImplementedError("Kubernetes orchestration not yet fully implemented.")
        
    async def delete_deployment(self, name: str):
        raise NotImplementedError("Kubernetes orchestration not yet fully implemented.")
        
    async def scale_deployment(self, name: str, replicas: int):
        raise NotImplementedError("Kubernetes orchestration not yet fully implemented.")
