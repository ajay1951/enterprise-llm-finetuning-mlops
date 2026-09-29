import json
import time
from datetime import datetime, timedelta

import redis.asyncio as redis
from sqlalchemy.orm import Session

from backend.forgellm_api.core.config import get_settings
from backend.forgellm_api.db.models.scheduling import JobAssignment, ResourceReservation
from backend.forgellm_api.db.models.worker import Worker, WorkerGPU

settings = get_settings()


class ResourceScheduler:
    def __init__(self):
        self.redis_client = None

    async def get_redis(self):
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
        return self.redis_client

    async def acquire_gpu_lock(self, gpu_uuid: str, lock_timeout: int = 300) -> bool:
        redis_db = await self.get_redis()
        lock_key = f"forgellm:gpu-lock:{gpu_uuid}"
        # Set if not exists, with expiration
        acquired = await redis_db.set(lock_key, "locked", nx=True, ex=lock_timeout)
        return bool(acquired)

    async def release_gpu_lock(self, gpu_uuid: str):
        redis_db = await self.get_redis()
        lock_key = f"forgellm:gpu-lock:{gpu_uuid}"
        await redis_db.delete(lock_key)

    async def schedule_job(
        self,
        db: Session,
        job_id: str,
        job_type: str,
        required_gpus: int = 1,
        min_vram_gb: float = 0,
        required_cpu: float = 0,
        required_ram_gb: float = 0,
        exclude_worker_ids: list = None,
    ) -> JobAssignment:
        """
        Implements BEST_FIT scheduling. Finds the GPU with the smallest sufficient VRAM to avoid wasting large GPUs on small jobs.
        """
        # Find healthy online workers that match criteria (not draining, not offline)
        threshold_time = datetime.utcnow() - timedelta(minutes=5)

        query = db.query(Worker).filter(
            Worker.status == "ONLINE", Worker.last_heartbeat >= threshold_time
        )
        if exclude_worker_ids:
            query = query.filter(Worker.id.notin_(exclude_worker_ids))

        workers = query.all()

        # If anti-affinity is too strict and we have no workers, fallback to all workers
        if not workers and exclude_worker_ids:
            workers = (
                db.query(Worker)
                .filter(
                    Worker.status == "ONLINE", Worker.last_heartbeat >= threshold_time
                )
                .all()
            )

        if not workers:
            raise Exception("No online workers available for scheduling.")

        eligible_gpus = []
        for worker in workers:
            if required_ram_gb > 0 and worker.ram_available < required_ram_gb:
                continue

            for gpu in worker.gpus:
                if gpu.status == "AVAILABLE":
                    vram_gb = gpu.memory_total / 1024.0
                    if vram_gb >= min_vram_gb:
                        eligible_gpus.append((worker, gpu, vram_gb))

        if len(eligible_gpus) < required_gpus:
            raise Exception(
                f"Insufficient resources. Found {len(eligible_gpus)} eligible GPUs, required {required_gpus} GPUs with at least {min_vram_gb}GB VRAM."
            )

        # Best-fit: Sort by VRAM ascending to find the smallest sufficient GPU
        eligible_gpus.sort(key=lambda x: x[2])

        selected_gpus = []
        selected_worker = None

        for worker, gpu, vram_gb in eligible_gpus:
            # Try to acquire lock
            if await self.acquire_gpu_lock(gpu.uuid):
                selected_gpus.append((worker, gpu))
                if len(selected_gpus) == required_gpus:
                    selected_worker = worker  # In a simple world, all GPUs must come from the same worker if required_gpus > 1 (we'll assume so for now)
                    break
            else:
                continue

        if len(selected_gpus) < required_gpus:
            # Unlock the ones we grabbed
            for w, g in selected_gpus:
                await self.release_gpu_lock(g.uuid)
            raise Exception(
                "Failed to acquire distributed lock for required GPUs. They might be in use."
            )

        # We have our lock(s). Create Assignments and Reservations
        worker = selected_gpus[0][0]  # use first worker for the assignment

        assignment = JobAssignment(
            job_id=job_id, job_type=job_type, worker_id=worker.id, status="ASSIGNED"
        )
        db.add(assignment)

        for w, gpu in selected_gpus:
            gpu.status = "ALLOCATED"
            gpu.current_job_id = job_id

            reservation = ResourceReservation(
                worker_id=w.id,
                gpu_id=gpu.id,
                job_id=job_id,
                status="ACTIVE",
                cpu_cores_reserved=required_cpu,
                ram_gb_reserved=required_ram_gb,
                expires_at=datetime.utcnow()
                + timedelta(days=1),  # arbitrary default timeout
            )
            db.add(reservation)

        db.commit()
        return assignment

    async def release_resources(self, db: Session, job_id: str):
        reservations = (
            db.query(ResourceReservation)
            .filter(
                ResourceReservation.job_id == job_id,
                ResourceReservation.status == "ACTIVE",
            )
            .all()
        )
        for res in reservations:
            res.status = "RELEASED"
            if res.gpu:
                res.gpu.status = "AVAILABLE"
                res.gpu.current_job_id = None
                await self.release_gpu_lock(res.gpu.uuid)

        assignments = (
            db.query(JobAssignment)
            .filter(
                JobAssignment.job_id == job_id,
                JobAssignment.status.in_(["ASSIGNED", "RUNNING"]),
            )
            .all()
        )
        for asg in assignments:
            asg.status = "COMPLETED"
            asg.completed_at = datetime.utcnow()

        db.commit()


scheduler_service = ResourceScheduler()
