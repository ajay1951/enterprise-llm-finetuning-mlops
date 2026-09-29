import asyncio
from datetime import datetime, timedelta
from backend.forgellm_api.db.session import SessionLocal
from backend.forgellm_api.db.models.worker import Worker
from backend.forgellm_api.services.scheduler_service import scheduler_service


async def monitor_workers_health():
    """
    Background task to periodically check for offline workers and release their resources.
    """
    while True:
        try:
            db = SessionLocal()
            threshold = datetime.utcnow() - timedelta(minutes=5)

            # Find workers that missed heartbeats
            dead_workers = (
                db.query(Worker)
                .filter(
                    Worker.status.in_(["ONLINE", "BUSY", "DRAINING"]),
                    Worker.last_heartbeat < threshold,
                )
                .all()
            )

            for w in dead_workers:
                print(f"Worker {w.worker_id} went offline. Releasing resources...")
                w.status = "OFFLINE"
                for gpu in w.gpus:
                    gpu.status = "ERROR"
                    if gpu.current_job_id:
                        await scheduler_service.release_resources(
                            db, gpu.current_job_id
                        )

            db.commit()
            db.close()
        except Exception as e:
            print(f"Health monitor error: {e}")

        await asyncio.sleep(60)
