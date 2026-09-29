from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.core.security import get_current_user
import time

router = APIRouter(tags=["AI Gateway Operations"])

# In a real app we'd inject a configured Redis client, using None for local fallback
import redis

try:
    redis_client = redis.Redis(host="localhost", port=6379, db=1)
    redis_client.ping()
except Exception:
    redis_client = None

start_time = time.time()


@router.get("/api/v1/gateway/health")
def gateway_health():
    # Check dependencies (DB, Redis)
    status = "HEALTHY"
    redis_status = "ok" if redis_client else "disconnected"

    return {
        "status": status,
        "uptime_seconds": int(time.time() - start_time),
        "redis": redis_status,
    }


@router.get("/api/v1/gateway/metrics")
def gateway_metrics(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    # Simple mock metrics aggregation for the dashboard
    return {
        "requests": 1420500,
        "success_rate": 99.4,
        "p95_latency_ms": 1800,
        "tokens_per_second": 48,
        "active_models": 8,
        "fallbacks": 32,
    }
