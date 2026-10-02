from datetime import UTC, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.forgellm_api.core.config import get_settings
from backend.forgellm_api.db.models.events import WorkerMetric
from backend.forgellm_api.db.models.worker import Worker, WorkerGPU
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.schemas.worker import (
    WorkerHeartbeatRequest,
    WorkerRegisterRequest,
    WorkerResponse,
)

router = APIRouter(tags=["Worker Registry"])
settings = get_settings()


def verify_worker_token(x_worker_token: str | None = Header(None)):
    expected_token = getattr(settings, "WORKER_TOKEN", "default-insecure-worker-token")
    if not x_worker_token or x_worker_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid or missing worker token")


@router.post(
    "/workers/register",
    response_model=WorkerResponse,
    dependencies=[Depends(verify_worker_token)],
)
def register_worker(req: WorkerRegisterRequest, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.worker_id == req.worker_id).first()

    if worker:
        worker.status = "ONLINE"
        worker.last_heartbeat = datetime.now(UTC)
        worker.hostname = req.hostname
        worker.worker_type = req.worker_type
        worker.cpu_count = req.cpu_count
        worker.ram_total = req.ram_total
        worker.gpu_count = req.gpu_count
        worker.software_version = req.software_version
        worker.cuda_version = req.cuda_version
        worker.driver_version = req.driver_version
        worker.region = req.region
        worker.zone = req.zone
        worker.metadata_json = req.metadata_json

        # Update GPUs
        for g in req.gpus:
            gpu_rec = (
                db.query(WorkerGPU)
                .filter(WorkerGPU.worker_id == worker.id, WorkerGPU.uuid == g.uuid)
                .first()
            )
            if not gpu_rec:
                gpu_rec = WorkerGPU(
                    worker_id=worker.id, uuid=g.uuid, gpu_index=g.gpu_index, name=g.name
                )
                db.add(gpu_rec)
            gpu_rec.memory_total = g.memory_total
            gpu_rec.status = g.status or "AVAILABLE"

    else:
        worker = Worker(
            worker_id=req.worker_id,
            hostname=req.hostname,
            status="ONLINE",
            worker_type=req.worker_type,
            cpu_count=req.cpu_count,
            ram_total=req.ram_total,
            gpu_count=req.gpu_count,
            software_version=req.software_version,
            cuda_version=req.cuda_version,
            driver_version=req.driver_version,
            region=req.region,
            zone=req.zone,
            metadata_json=req.metadata_json,
            last_heartbeat=datetime.now(UTC),
        )
        db.add(worker)
        db.flush()

        for g in req.gpus:
            gpu_rec = WorkerGPU(
                worker_id=worker.id,
                uuid=g.uuid,
                gpu_index=g.gpu_index,
                name=g.name,
                memory_total=g.memory_total,
                status=g.status or "AVAILABLE",
            )
            db.add(gpu_rec)

    db.commit()
    db.refresh(worker)
    return worker


@router.post(
    "/workers/{worker_id}/heartbeat", dependencies=[Depends(verify_worker_token)]
)
def worker_heartbeat(
    worker_id: str, req: WorkerHeartbeatRequest, db: Session = Depends(get_db)
):
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker.last_heartbeat = datetime.now(UTC)

    worker.status = req.status
    worker.ram_available = req.ram_available

    # Update GPU telemetry
    for g in req.gpus:
        gpu_rec = (
            db.query(WorkerGPU)
            .filter(WorkerGPU.worker_id == worker.id, WorkerGPU.uuid == g.uuid)
            .first()
        )
        if gpu_rec:
            gpu_rec.memory_used = g.memory_used
            gpu_rec.utilization = g.utilization
            gpu_rec.temperature = g.temperature
            gpu_rec.power = g.power
            gpu_rec.status = g.status or gpu_rec.status
            gpu_rec.current_job_id = g.current_job_id

    db.commit()
    return {"status": "ok"}


@router.post("/workers/{worker_id}/drain")
def drain_worker(worker_id: str, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker.status = "DRAINING"

    for gpu in worker.gpus:
        if gpu.status == "AVAILABLE":
            gpu.status = "DRAINING"

    db.commit()
    return {"status": "draining"}


@router.post("/workers/{worker_id}/enable")
def enable_worker(worker_id: str, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    worker.status = "ONLINE"

    for gpu in worker.gpus:
        if gpu.status == "DRAINING":
            gpu.status = "AVAILABLE"

    db.commit()
    return {"status": "online"}


@router.get("/workers", response_model=list[WorkerResponse])
def list_workers(db: Session = Depends(get_db)):
    return db.query(Worker).all()


@router.get("/workers/{worker_id}", response_model=WorkerResponse)
def get_worker(worker_id: str, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@router.get("/workers/{worker_id}/jobs", dependencies=[Depends(verify_worker_token)])
def get_worker_jobs(worker_id: str, db: Session = Depends(get_db)):
    # Mock endpoint for returning pending jobs to the polling worker agent
    return []


@router.get("/workers/{worker_id}/metrics")
def get_worker_metrics(worker_id: str, limit: int = 100, db: Session = Depends(get_db)):
    # Fallback to the old WorkerMetric for phase 5 compatibility
    return (
        db.query(WorkerMetric)
        .filter(WorkerMetric.worker_id == worker_id)
        .order_by(WorkerMetric.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.delete("/workers/{worker_id}")
def delete_worker(worker_id: str, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if worker:
        db.delete(worker)
        db.commit()
    return {"status": "success"}


@router.get("/gpus")
def list_gpus(db: Session = Depends(get_db)):
    return db.query(WorkerGPU).all()
