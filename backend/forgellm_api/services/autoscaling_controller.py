import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.forgellm_api.db.models.orchestration import AutoscalingPolicy, Workload
from backend.forgellm_api.db.session import SessionLocal
from backend.forgellm_api.services.orchestration_service import orchestration_manager


class AutoscalingController:
    """
    Evaluates AutoscalingPolicies against live metrics and triggers orchestration manager to scale workloads.
    """

    async def evaluate_all(self):
        db = SessionLocal()
        try:
            policies = (
                db.query(AutoscalingPolicy)
                .filter(AutoscalingPolicy.enabled == True)
                .all()
            )
            for p in policies:
                await self.evaluate_policy(db, p)
        except Exception as e:
            print(f"Autoscaling error: {e}")
        finally:
            db.close()

    async def evaluate_policy(self, db: Session, policy: AutoscalingPolicy):
        workload = policy.workload
        if not workload or workload.status not in ["READY", "DEGRADED"]:
            return  # Don't autoscale if currently deploying or stopped

        # Get live metrics (Mocked for now since Phase 5 Prometheus/Celery integration isn't fully piped to here)
        current_reqs = self.get_current_requests_per_sec(workload.id)
        current_util = self.get_current_gpu_utilization(workload.id)

        now = datetime.now(UTC)
        last_event = policy.last_scale_event_at or (now - timedelta(days=1))

        # Scale UP logic (if traffic > target OR util > target)
        if (
            current_reqs > policy.target_requests_per_sec
            or current_util > policy.target_gpu_utilization
        ):
            if (now - last_event).total_seconds() >= policy.scale_up_cooldown:
                if workload.desired_replicas < workload.max_replicas:
                    print(
                        f"[Autoscaler] Triggering SCALE UP for {workload.id}. Replicas {workload.desired_replicas} -> {workload.desired_replicas + 1}"
                    )
                    try:
                        await orchestration_manager.scale_workload(
                            db,
                            workload.id,
                            workload.desired_replicas + 1,
                            reason="Autoscaling: High load",
                        )
                        policy.last_scale_event_at = now
                        db.commit()
                    except Exception as e:
                        print(f"Autoscaler scale up failed (Quota?): {e}")

        # Scale DOWN logic (if traffic << target AND util << target)
        elif current_reqs < (policy.target_requests_per_sec * 0.5) and current_util < (
            policy.target_gpu_utilization * 0.5
        ):
            if (now - last_event).total_seconds() >= policy.scale_down_cooldown:
                if workload.desired_replicas > workload.min_replicas:
                    print(
                        f"[Autoscaler] Triggering SCALE DOWN for {workload.id}. Replicas {workload.desired_replicas} -> {workload.desired_replicas - 1}"
                    )
                    try:
                        await orchestration_manager.scale_workload(
                            db,
                            workload.id,
                            workload.desired_replicas - 1,
                            reason="Autoscaling: Low load",
                        )
                        policy.last_scale_event_at = now
                        db.commit()
                    except Exception as e:
                        print(f"Autoscaler scale down failed: {e}")

    def get_current_requests_per_sec(self, workload_id: str) -> float:
        # Placeholder for Prometheus metric
        return random.uniform(0, 20)

    def get_current_gpu_utilization(self, workload_id: str) -> float:
        # Placeholder for NVML metric via ReplicaRegistry
        return random.uniform(0, 100)


autoscaling_controller = AutoscalingController()


async def run_autoscaling_loop():
    while True:
        await autoscaling_controller.evaluate_all()
        await asyncio.sleep(15)
