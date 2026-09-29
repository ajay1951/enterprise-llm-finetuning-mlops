import asyncio
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.forgellm_api.db.models.orchestration import (
    ResourceQuota,
    ScalingEvent,
    Workload,
    WorkloadReplica,
)
from backend.forgellm_api.db.models.worker import Worker, WorkerGPU
from backend.forgellm_api.db.session import SessionLocal
from backend.forgellm_api.services.scheduler_service import scheduler_service


class ResourceQuotaError(Exception):
    pass


class OrchestrationManager:
    """
    Manages the lifecycle of workloads and delegates resource reservation to the Scheduler.
    """

    async def create_workload(
        self,
        db: Session,
        project_id: str,
        name: str,
        workload_type: str,
        desired_replicas: int = 1,
        min_replicas: int = 1,
        max_replicas: int = 1,
        strategy: str = "ROLLING",
        resource_reqs: dict = None,
        model_version_id: str = None,
    ) -> Workload:

        self.check_quota(db, project_id, desired_replicas, resource_reqs)

        workload = Workload(
            project_id=project_id,
            name=name,
            type=workload_type,
            desired_replicas=desired_replicas,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            strategy=strategy,
            resource_requirements=resource_reqs or {"gpu": 1},
            model_version_id=model_version_id,
        )
        db.add(workload)
        db.commit()
        db.refresh(workload)
        return workload

    def check_quota(
        self, db: Session, project_id: str, added_replicas: int, resource_reqs: dict
    ):
        quota = (
            db.query(ResourceQuota)
            .filter(ResourceQuota.project_id == project_id)
            .first()
        )
        if not quota:
            return  # No quota explicitly set

        current_workloads = (
            db.query(Workload).filter(Workload.project_id == project_id).all()
        )
        current_replicas = sum(w.desired_replicas for w in current_workloads)

        if current_replicas + added_replicas > quota.max_replicas:
            raise ResourceQuotaError(
                f"Project quota allows {quota.max_replicas} replicas. Adding {added_replicas} exceeds this (Current: {current_replicas})."
            )

        # Simplistic GPU quota check
        req_gpu = (resource_reqs or {}).get("gpu", 1)
        current_gpus = sum(
            w.desired_replicas * (w.resource_requirements or {}).get("gpu", 1)
            for w in current_workloads
        )

        if current_gpus + (added_replicas * req_gpu) > quota.max_gpus:
            raise ResourceQuotaError(
                f"Project quota allows {quota.max_gpus} GPUs. Adding {added_replicas * req_gpu} exceeds this (Current: {current_gpus})."
            )

    async def scale_workload(
        self,
        db: Session,
        workload_id: str,
        replicas: int,
        reason: str = "Manual scaling",
    ):
        workload = db.query(Workload).filter(Workload.id == workload_id).first()
        if not workload:
            raise ValueError("Workload not found")

        if replicas < workload.min_replicas or replicas > workload.max_replicas:
            raise ValueError(
                f"Requested replicas ({replicas}) outside bounds [{workload.min_replicas}, {workload.max_replicas}]"
            )

        # Check quota diff
        diff = replicas - workload.desired_replicas
        if diff > 0:
            self.check_quota(
                db, workload.project_id, diff, workload.resource_requirements
            )
            event_type = "SCALE_UP"
        elif diff < 0:
            event_type = "SCALE_DOWN"
        else:
            return workload

        event = ScalingEvent(
            workload_id=workload.id,
            event_type=event_type,
            previous_replicas=workload.desired_replicas,
            new_replicas=replicas,
            reason=reason,
        )
        db.add(event)

        workload.desired_replicas = replicas
        workload.status = "SCALING"
        db.commit()
        db.refresh(workload)
        return workload

    async def restart_workload(self, db: Session, workload_id: str):
        # Simply marking all replicas as FAILED will trigger the reconciliation loop to restart them
        replicas = (
            db.query(WorkloadReplica)
            .filter(
                WorkloadReplica.workload_id == workload_id,
                WorkloadReplica.status.in_(["READY", "PENDING", "STARTING"]),
            )
            .all()
        )
        for r in replicas:
            r.status = "FAILED"
        db.commit()

    async def update_workload(
        self, db: Session, workload_id: str, new_model_version_id: str
    ):
        workload = db.query(Workload).filter(Workload.id == workload_id).first()
        if not workload:
            raise ValueError("Workload not found")

        workload.model_version_id = new_model_version_id
        workload.status = "DEPLOYING"
        db.commit()
        # Rolling update is handled by the reconciliation loop matching active replica model_version against the workload

    async def stop_workload(self, db: Session, workload_id: str):
        workload = db.query(Workload).filter(Workload.id == workload_id).first()
        if workload:
            workload.desired_replicas = 0
            workload.status = "STOPPED"
            db.commit()

    async def create_replica(self, db: Session, workload: Workload):
        # 1. Schedule resources
        reqs = workload.resource_requirements or {}
        req_gpu = reqs.get("gpu", 1)
        min_vram = reqs.get("min_vram_gb", 0)

        # Anti-affinity: Try to find a worker that doesn't already have a replica for this workload
        existing_replicas = (
            db.query(WorkloadReplica)
            .filter(
                WorkloadReplica.workload_id == workload.id,
                WorkloadReplica.status.in_(["READY", "STARTING"]),
            )
            .all()
        )
        exclude_worker_ids = [r.worker_id for r in existing_replicas if r.worker_id]

        try:
            assignment = await scheduler_service.schedule_job(
                db=db,
                job_id=f"workload-{workload.id}",  # Logical lock identifier
                job_type="INFERENCE",
                required_gpus=req_gpu,
                min_vram_gb=min_vram,
                exclude_worker_ids=exclude_worker_ids,
            )
            worker_id = assignment.worker_id

            # Find the locked GPU
            gpu = (
                db.query(WorkerGPU)
                .filter(
                    WorkerGPU.current_job_id == f"workload-{workload.id}",
                    WorkerGPU.worker_id == worker_id,
                )
                .first()
            )

            replica = WorkloadReplica(
                workload_id=workload.id,
                worker_id=worker_id,
                gpu_id=gpu.id if gpu else None,
                status="STARTING",
                endpoint=None,  # Worker agent will patch this when ready
            )
            db.add(replica)
            db.commit()
            return replica

        except Exception as e:
            print(f"Failed to schedule replica for {workload.id}: {e}")
            return None


orchestration_manager = OrchestrationManager()
