from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.forgellm_api.core.security import get_current_user
from backend.forgellm_api.db.models.benchmark import BenchmarkResult, BenchmarkRun
from backend.forgellm_api.db.session import get_db

router = APIRouter(tags=["Benchmarks"])


@router.post("/api/v1/benchmarks")
def create_benchmark(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    run = BenchmarkRun(
        project_id=payload["project_id"], name=payload["name"], status="QUEUED"
    )
    db.add(run)
    db.flush()

    # In a real system, we'd enqueue a celery task here.
    # For now, we simulate QUEUED status.

    db.commit()
    return {"id": run.id, "status": run.status}


@router.get("/api/v1/benchmarks/{id}")
def get_benchmark(
    id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    run = db.query(BenchmarkRun).filter(BenchmarkRun.id == id).first()
    if not run:
        raise HTTPException(404, "Benchmark not found")

    results = (
        db.query(BenchmarkResult).filter(BenchmarkResult.benchmark_run_id == id).all()
    )

    return {
        "id": run.id,
        "name": run.name,
        "status": run.status,
        "results": [
            {
                "model_version_id": r.model_version_id,
                "total_requests": r.total_requests,
                "avg_latency_ms": r.avg_latency_ms,
                "p95_latency_ms": r.p95_latency_ms,
                "ttft_ms": r.ttft_ms,
                "tokens_per_second": r.tokens_per_second,
                "success_rate": r.success_rate,
            }
            for r in results
        ],
    }
