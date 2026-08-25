import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MetricsBuffer:
    """
    Buffers inference metrics in Redis for high-performance writes,
    to be flushed to PostgreSQL asynchronously or via a cron job.
    """
    def __init__(self, redis_client):
        self.redis = redis_client

    def record_request_start(self, deployment_id: str):
        if not self.redis: return
        key = f"deployment:load:{deployment_id}"
        try:
            self.redis.incr(key)
        except Exception as e:
            logger.error(f"Failed to inc load: {e}")

    def record_request_end(self, deployment_id: str):
        if not self.redis: return
        key = f"deployment:load:{deployment_id}"
        try:
            # Prevent negative load
            if int(self.redis.get(key) or 0) > 0:
                self.redis.decr(key)
        except Exception as e:
            logger.error(f"Failed to dec load: {e}")

    def record_inference_metrics(self, data: Dict[str, Any]):
        """
        data includes: request_id, model, version_id, deployment_id, 
        project_id, org_id, latency_ms, ttft_ms, tokens, status
        """
        if not self.redis: return
        try:
            # Push to a Redis list for batch processing
            self.redis.lpush("gateway:metrics:queue", json.dumps(data))
            
            # Also maintain basic counters for real-time dashboard
            status = data.get("status", "error")
            org_id = data.get("org_id")
            proj_id = data.get("project_id")
            
            if org_id:
                self.redis.incr(f"metrics:org:{org_id}:requests:total")
                self.redis.incr(f"metrics:org:{org_id}:requests:{status}")
            
            if proj_id:
                self.redis.incr(f"metrics:proj:{proj_id}:requests:total")
                self.redis.incr(f"metrics:proj:{proj_id}:requests:{status}")
                
        except Exception as e:
            logger.error(f"Failed to buffer metrics: {e}")
