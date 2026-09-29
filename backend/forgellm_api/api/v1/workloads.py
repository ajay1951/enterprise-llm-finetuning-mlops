from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.forgellm_api.db.models.orchestration import (
    ResourceQuota,
    Workload,
    WorkloadReplica,
)
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.services.orchestration_service import orchestration_manager

router = APIRouter(tags=["Orchestration Workloads"])


@router.get("/workloads")
def list_workloads(db: Session = Depends(get_db)):
    # Returns workloads along with their replicas
    workloads = db.query(Workload).all()
    # Pydantic serialization happens automatically in FastAPI if models are defined,
    # for simplicity we return dicts here or rely on FastAPI parsing
    return workloads


@router.post("/workloads")
async def create_workload(req: dict, db: Session = Depends(get_db)):
    try:
        w = await orchestration_manager.create_workload(
            db=db,
            project_id=req["project_id"],
            name=req["name"],
            workload_type=req.get("type", "INFERENCE"),
            desired_replicas=req.get("desired_replicas", 1),
            min_replicas=req.get("min_replicas", 1),
            max_replicas=req.get("max_replicas", 1),
            strategy=req.get("strategy", "ROLLING"),
            resource_reqs=req.get("resource_requirements"),
            model_version_id=req.get("model_version_id"),
        )
        return {"id": w.id, "status": "CREATED"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workloads/{id}/scale")
async def scale_workload(id: str, req: dict, db: Session = Depends(get_db)):
    try:
        w = await orchestration_manager.scale_workload(
            db=db, workload_id=id, replicas=req["replicas"], reason="API Manual Scaling"
        )
        return {"id": w.id, "desired_replicas": w.desired_replicas}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workloads/{id}/stop")
async def stop_workload(id: str, db: Session = Depends(get_db)):
    await orchestration_manager.stop_workload(db, id)
    return {"status": "STOPPING"}


@router.post("/workloads/{id}/restart")
async def restart_workload(id: str, db: Session = Depends(get_db)):
    await orchestration_manager.restart_workload(db, id)
    return {"status": "RESTARTING"}


@router.get("/projects/{project_id}/quota")
def get_quota(project_id: str, db: Session = Depends(get_db)):
    quota = (
        db.query(ResourceQuota).filter(ResourceQuota.project_id == project_id).first()
    )
    if not quota:
        # Return default mock
        return {
            "max_gpus": 2,
            "max_cpu_cores": 16.0,
            "max_ram_gb": 64.0,
            "max_replicas": 4,
        }
    return quota
