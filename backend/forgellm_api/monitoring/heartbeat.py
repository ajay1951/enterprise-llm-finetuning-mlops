import threading
import time
import socket
import logging
import json
import redis
from backend.forgellm_api.core.config import get_settings
from backend.forgellm_api.monitoring.gpu import gpu_monitor
from backend.forgellm_api.monitoring.system import sys_monitor
from backend.forgellm_api.db.session import SessionLocal
from backend.forgellm_api.db.models.worker import Worker
from backend.forgellm_api.db.models.events import WorkerMetric
from datetime import datetime

logger = logging.getLogger(__name__)
settings = get_settings()

class WorkerHeartbeatThread(threading.Thread):
    def __init__(self, interval=15):
        super().__init__(daemon=True)
        self.interval = interval
        self.worker_id = socket.gethostname()
        self.active_job_id = None
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def run(self):
        logger.info(f"Started worker heartbeat thread for {self.worker_id}")
        while True:
            try:
                self._send_heartbeat()
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")
            time.sleep(self.interval)

    def set_active_job(self, job_id: str):
        self.active_job_id = job_id

    def clear_active_job(self):
        self.active_job_id = None

    def _send_heartbeat(self):
        gpu_metrics = gpu_monitor.get_metrics()
        sys_metrics = sys_monitor.get_metrics()
        
        status = "busy" if self.active_job_id else "idle"
        
        # Publish transient heartbeat to redis pubsub
        heartbeat_data = {
            "event_type": "worker.heartbeat",
            "worker_id": self.worker_id,
            "status": status,
            "job_id": self.active_job_id,
            "gpu_count": len(gpu_metrics),
            "cpu_percent": sys_metrics.get("cpu_percent"),
            "ram_used_gb": sys_metrics.get("ram_used_gb"),
            "gpu_metrics": gpu_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.redis_client.publish("forgellm:workers:heartbeat", json.dumps(heartbeat_data))

        # Also persist latest state to DB so the dashboard has immediate state on reload
        db = SessionLocal()
        try:
            worker = db.query(Worker).filter(Worker.id == self.worker_id).first()
            if not worker:
                worker = Worker(id=self.worker_id)
                db.add(worker)
                db.flush()
            
            worker.status = status
            worker.last_heartbeat = datetime.utcnow()
            worker.gpu_count = len(gpu_metrics)
            worker.ram_total_gb = sys_metrics.get("ram_total_gb")
            worker.active_job_id = self.active_job_id
            
            metric = WorkerMetric(
                worker_id=self.worker_id,
                cpu_percent=sys_metrics.get("cpu_percent"),
                ram_used_gb=sys_metrics.get("ram_used_gb"),
                gpu_metrics=gpu_metrics
            )
            db.add(metric)
            db.commit()
        except Exception as e:
            logger.error(f"DB Error saving heartbeat: {e}")
            db.rollback()
        finally:
            db.close()

# Global instance for the worker process
heartbeat_thread = WorkerHeartbeatThread()
