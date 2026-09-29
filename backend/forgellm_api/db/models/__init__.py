from backend.forgellm_api.db.models.project import Project
from backend.forgellm_api.db.models.dataset import Dataset, DatasetVersion
from backend.forgellm_api.db.models.training import TrainingJob, Experiment, Checkpoint
from backend.forgellm_api.db.models.model import (
    Model,
    ModelVersion,
    Evaluation,
    EvaluationResult,
    ModelAlias,
    RoutingConfig,
)
from backend.forgellm_api.db.models.worker import Worker, WorkerGPU
from backend.forgellm_api.db.models.orchestration import (
    Workload,
    WorkloadReplica,
    AutoscalingPolicy,
    ScalingEvent,
    ResourceQuota,
)
from backend.forgellm_api.db.models.deployment import Deployment, DeploymentEvent
from backend.forgellm_api.db.models.experiment import (
    GatewayExperiment,
    ExperimentVariant,
)
from backend.forgellm_api.db.models.benchmark import BenchmarkRun, BenchmarkResult
from backend.forgellm_api.db.models.audit import AuditLog
from backend.forgellm_api.db.models.user import User, APIKey
from backend.forgellm_api.db.models.organization import Organization
from backend.forgellm_api.db.models.scheduling import JobAssignment

# This ensures all models are loaded for SQLAlchemy relationship resolution
__all__ = [
    "Project",
    "Dataset",
    "DatasetVersion",
    "TrainingJob",
    "Experiment",
    "Checkpoint",
    "Model",
    "ModelVersion",
    "Evaluation",
    "EvaluationResult",
    "ModelAlias",
    "RoutingConfig",
    "Worker",
    "WorkerGPU",
    "Workload",
    "WorkloadReplica",
    "AutoscalingPolicy",
    "ScalingEvent",
    "ResourceQuota",
    "Deployment",
    "DeploymentEvent",
    "GatewayExperiment",
    "ExperimentVariant",
    "BenchmarkRun",
    "BenchmarkResult",
    "AuditLog",
    "User",
    "APIKey",
    "Organization",
    "JobAssignment",
]
