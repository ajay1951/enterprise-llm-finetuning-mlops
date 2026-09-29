import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from backend.forgellm_api.db.models.orchestration import Workload, WorkloadReplica
from backend.forgellm_api.db.models.worker import Worker
from backend.forgellm_api.db.session import SessionLocal
from backend.forgellm_api.services.orchestration_service import orchestration_manager
from backend.forgellm_api.services.scheduler_service import scheduler_service


class ReconciliationController:
    async def reconcile_all(self):
        db = SessionLocal()
        try:
            workloads = db.query(Workload).all()
            for w in workloads:
                await self.reconcile_workload(db, w)
            db.commit()
        except Exception as e:
            print(f"Reconciliation error: {e}")
        finally:
            db.close()

    async def reconcile_workload(self, db: Session, workload: Workload):
        if workload.status == "STOPPED":
            workload.desired_replicas = 0

        # Get active replicas (not FAILED or STOPPED)
        active_replicas = [
            r
            for r in workload.replicas
            if r.status not in ["FAILED", "STOPPED", "STOPPING"]
        ]

        # 1. Automatic Failure Recovery (Worker offline check)
        for r in active_replicas:
            if r.worker_id:
                worker = db.query(Worker).filter(Worker.id == r.worker_id).first()
                if not worker or worker.status != "ONLINE":
                    print(
                        f"Replica {r.id} is on offline worker {r.worker_id}. Marking FAILED."
                    )
                    r.status = "FAILED"
                    # Release lock
                    if r.gpu_id:
                        await scheduler_service.release_resources(
                            db, f"workload-{workload.id}"
                        )
                        r.gpu_id = None

        # Refresh active replicas after potential failures
        active_replicas = [
            r
            for r in workload.replicas
            if r.status not in ["FAILED", "STOPPED", "STOPPING"]
        ]
        ready_replicas = [r for r in active_replicas if r.status == "READY"]

        # 2. Desired vs Actual logic
        actual_count = len(active_replicas)
        desired = workload.desired_replicas

        if actual_count < desired:
            # Need more replicas
            needed = desired - actual_count
            print(f"Workload {workload.id} scaling UP: {actual_count} -> {desired}")
            for _ in range(needed):
                await orchestration_manager.create_replica(db, workload)

        elif actual_count > desired:
            # Need to remove replicas (Graceful shutdown)
            excess = actual_count - desired
            print(f"Workload {workload.id} scaling DOWN: {actual_count} -> {desired}")
            for r in active_replicas[:excess]:
                r.status = (
                    "STOPPING"  # Worker agent will see this and cleanly shut down
                )

        # 3. Rolling Deployments & Status
        if workload.status == "DEPLOYING":
            # If rolling update is complete (all ready replicas are on the new version)
            # In a full implementation, we'd check replica revisions.
            pass

        if actual_count == desired and len(ready_replicas) == desired:
            if workload.status != "STOPPED":
                workload.status = "READY"

        elif len(ready_replicas) > 0 and len(ready_replicas) < desired:
            workload.status = "DEGRADED"


reconciliation_controller = ReconciliationController()


async def run_reconciliation_loop():
    while True:
        await reconciliation_controller.reconcile_all()
        await asyncio.sleep(10)
