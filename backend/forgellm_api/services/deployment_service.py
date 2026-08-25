import logging
from sqlalchemy.orm import Session
from datetime import datetime
from backend.forgellm_api.db.models.deployment import Deployment, DeploymentEvent
from backend.forgellm_api.db.models.model import ModelVersion
from backend.forgellm_api.schemas.deployment import DeploymentCreate
from backend.forgellm_api.services.event_service import event_service
from celery import Celery
from backend.forgellm_api.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery("forgellm_worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

class DeploymentService:
    def __init__(self, db: Session):
        self.db = db

    def get_deployments(self, project_id: str = None, skip: int = 0, limit: int = 100):
        query = self.db.query(Deployment)
        if project_id:
            query = query.filter(Deployment.project_id == project_id)
        return query.order_by(Deployment.created_at.desc()).offset(skip).limit(limit).all()

    def get_deployment(self, deployment_id: str):
        return self.db.query(Deployment).filter(Deployment.id == deployment_id).first()

    def create_deployment(self, project_id: str, deploy_in: DeploymentCreate):
        # 1. Validate Model Version
        model_version = self.db.query(ModelVersion).filter(ModelVersion.id == deploy_in.model_version_id).first()
        if not model_version:
            raise ValueError(f"ModelVersion {deploy_in.model_version_id} not found.")

        # 2. Check if name exists
        existing = self.db.query(Deployment).filter(Deployment.name == deploy_in.name).first()
        if existing:
            raise ValueError(f"Deployment name '{deploy_in.name}' is already taken.")

        # 3. Create record
        config_dict = deploy_in.configuration.dict() if deploy_in.configuration else {}
        
        deployment = Deployment(
            project_id=project_id,
            model_version_id=deploy_in.model_version_id,
            name=deploy_in.name,
            serving_backend=deploy_in.backend,
            device=deploy_in.device,
            configuration=config_dict,
            status="created"
        )
        self.db.add(deployment)
        self.db.commit()
        
        self.log_event(deployment.id, "deployment.created", {"message": "Deployment configured."})
        return deployment

    def start_deployment(self, deployment_id: str):
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            raise ValueError("Deployment not found")
            
        if deployment.status in ["starting", "loading", "ready"]:
            return deployment

        deployment.status = "queued"
        deployment.error_message = None
        self.db.commit()
        self.log_event(deployment.id, "deployment.queued", {"message": "Waiting for inference worker."})
        
        # Dispatch Celery Task to actually start the server
        celery_app.send_task("run_deployment_server", args=[deployment.id])
        return deployment

    def stop_deployment(self, deployment_id: str):
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            raise ValueError("Deployment not found")
            
        deployment.status = "stopping"
        self.db.commit()
        self.log_event(deployment.id, "deployment.stopping", {"message": "Stopping model server."})
        
        # Publish an event to Redis pubsub so the deployment worker knows to terminate the subprocess
        from backend.forgellm_api.realtime.redis_bus import redis_bus
        import asyncio
        import json
        import redis
        
        # Use sync redis client to send stop signal since we are in sync service
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.publish(f"forgellm:deployment_control:{deployment_id}", json.dumps({"command": "stop"}))
        
        return deployment

    def delete_deployment(self, deployment_id: str):
        deployment = self.get_deployment(deployment_id)
        if deployment:
            if deployment.status in ["starting", "loading", "ready"]:
                self.stop_deployment(deployment_id)
            self.db.delete(deployment)
            self.db.commit()
        return True

    def log_event(self, deployment_id: str, event_type: str, data: dict):
        count = self.db.query(DeploymentEvent).filter(DeploymentEvent.deployment_id == deployment_id).count()
        event = DeploymentEvent(
            deployment_id=deployment_id,
            event_type=event_type,
            sequence=count + 1,
            data=data
        )
        self.db.add(event)
        self.db.commit()
        
        # Publish to real-time event bus
        payload = {
            "event_id": event.id,
            "event_type": event_type,
            "deployment_id": deployment_id,
            "timestamp": event.timestamp.isoformat() if event.timestamp else datetime.utcnow().isoformat(),
            "sequence": event.sequence,
            "data": data
        }
        import redis
        import json
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.publish(f"forgellm:deployment:{deployment_id}", json.dumps(payload))
        
        return event

    def get_logs(self, deployment_id: str, limit: int = 500):
        return self.db.query(DeploymentEvent).filter(DeploymentEvent.deployment_id == deployment_id).order_by(DeploymentEvent.sequence.asc()).limit(limit).all()
