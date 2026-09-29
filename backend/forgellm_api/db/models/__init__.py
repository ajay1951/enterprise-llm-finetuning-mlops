from backend.forgellm_api.db.models.audit import AuditLog
from backend.forgellm_api.db.models.benchmark import BenchmarkResult, BenchmarkRun
from backend.forgellm_api.db.models.dataset import Dataset, DatasetVersion
from backend.forgellm_api.db.models.deployment import Deployment, DeploymentEvent
from backend.forgellm_api.db.models.experiment import (
    ExperimentVariant,
    GatewayExperiment,
)
from backend.forgellm_api.db.models.model import (
    Evaluation,
    EvaluationResult,
    Model,
    ModelAlias,
    ModelVersion,
    RoutingConfig,
)
from backend.forgellm_api.db.models.orchestration import (
    AutoscalingPolicy,
    ResourceQuota,
    ScalingEvent,
    Workload,
    WorkloadReplica,
)
from backend.forgellm_api.db.models.organization import Organization
from backend.forgellm_api.db.models.project import Project
from backend.forgellm_api.db.models.scheduling import (
    ComputeInstance,
    JobAssignment,
    ResourceReservation,
)
from backend.forgellm_api.db.models.training import Checkpoint, Experiment, TrainingJob
from backend.forgellm_api.db.models.user import APIKey, User
from backend.forgellm_api.db.models.worker import Worker, WorkerGPU

# This ensures all models are loaded for SQLAlchemy relationship resolution
__all__ = [
    "APIKey",
    "AuditLog",
    "AutoscalingPolicy",
    "BenchmarkResult",
    "BenchmarkRun",
    "Checkpoint",
    "ComputeInstance",
    "Dataset",
    "DatasetVersion",
    "Deployment",
    "DeploymentEvent",
    "Evaluation",
    "EvaluationResult",
    "Experiment",
    "ExperimentVariant",
    "GatewayExperiment",
    "JobAssignment",
    "Model",
    "ModelAlias",
    "ModelVersion",
    "Organization",
    "Project",
    "ResourceQuota",
    "ResourceReservation",
    "RoutingConfig",
    "ScalingEvent",
    "TrainingJob",
    "User",
    "Worker",
    "WorkerGPU",
    "Workload",
    "WorkloadReplica",
]
