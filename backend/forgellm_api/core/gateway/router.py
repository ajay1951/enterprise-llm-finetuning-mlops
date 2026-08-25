from typing import Optional, List, Dict
import random
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.forgellm_api.db.models.model import Model, ModelAlias, ModelVersion, RoutingConfig
from backend.forgellm_api.db.models.experiment import GatewayExperiment, ExperimentVariant
from backend.forgellm_api.db.models.deployment import Deployment, DeploymentEvent

logger = logging.getLogger(__name__)

def resolve_model_version(db: Session, project_id: str, requested_model: str) -> str:
    """
    Resolves the requested model string (name or alias) to a specific model_version_id.
    Handles Alias resolution, A/B Testing resolution, and default Primary routing.
    """
    # 1. Check if it's an alias
    alias = db.query(ModelAlias).join(Model).filter(
        Model.project_id == project_id,
        ModelAlias.alias == requested_model
    ).first()
    
    if alias:
        return alias.model_version_id

    # 2. Check if it's a direct model name
    model = db.query(Model).filter(
        Model.project_id == project_id,
        Model.name == requested_model
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail=f"Model or alias '{requested_model}' not found.")

    # 3. Check for Active Experiments (A/B Testing)
    active_experiment = db.query(GatewayExperiment).filter(
        GatewayExperiment.model_id == model.id,
        GatewayExperiment.status == "RUNNING"
    ).first()
    
    if active_experiment:
        variants = db.query(ExperimentVariant).filter(
            ExperimentVariant.experiment_id == active_experiment.id
        ).all()
        
        if variants:
            # Weighted random selection
            total_weight = sum(v.weight for v in variants)
            if total_weight > 0:
                rand_val = random.uniform(0, total_weight)
                cumulative = 0
                for v in variants:
                    cumulative += v.weight
                    if rand_val <= cumulative:
                        return v.model_version_id

    # 4. Fallback to RoutingConfig Primary Version
    routing = db.query(RoutingConfig).filter(RoutingConfig.model_id == model.id).first()
    if routing and routing.primary_version_id:
        return routing.primary_version_id

    # 5. Fallback to most recent PRODUCTION or STAGED version
    latest_version = db.query(ModelVersion).filter(
        ModelVersion.model_id == model.id,
        ModelVersion.lifecycle_status.in_(["PRODUCTION", "STAGED", "READY"])
    ).order_by(ModelVersion.created_at.desc()).first()
    
    if latest_version:
        return latest_version.id
        
    raise HTTPException(status_code=404, detail="No valid model version found to route this request.")

def get_fallback_version(db: Session, project_id: str, requested_model: str) -> Optional[str]:
    """Retrieves the fallback version if configured."""
    model = db.query(Model).filter(
        Model.project_id == project_id,
        Model.name == requested_model
    ).first()
    if not model:
        return None
    routing = db.query(RoutingConfig).filter(RoutingConfig.model_id == model.id).first()
    if routing and routing.fallback_version_id:
        return routing.fallback_version_id
    return None


def get_healthy_deployments(db: Session, version_id: str) -> List[Deployment]:
    deployments = db.query(Deployment).filter(
        Deployment.model_version_id == version_id,
        Deployment.status == "ready",
        Deployment.health_status == "healthy"
    ).all()
    return deployments


def select_replica(deployments: List[Deployment], strategy: str = "LEAST_LOADED", redis_client=None) -> Deployment:
    """
    Selects a replica based on the strategy.
    LEAST_LOADED uses Redis to track active requests.
    """
    if not deployments:
        raise HTTPException(status_code=503, detail="No healthy replicas available for this model version.")

    if strategy == "ROUND_ROBIN" or not redis_client:
        return random.choice(deployments)

    if strategy == "LEAST_LOADED":
        # In a real impl, we fetch the active request count for each deployment ID from Redis
        try:
            keys = [f"deployment:load:{d.id}" for d in deployments]
            loads = redis_client.mget(keys)
            
            best_deployment = deployments[0]
            min_load = float('inf')
            
            for d, load_str in zip(deployments, loads):
                load = int(load_str) if load_str else 0
                if load < min_load:
                    min_load = load
                    best_deployment = d
            
            return best_deployment
        except Exception:
            # Fallback to random if Redis fails
            return random.choice(deployments)
    
    return random.choice(deployments)
