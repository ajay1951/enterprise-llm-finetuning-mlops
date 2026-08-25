from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.schemas.training import TrainingJobCreate, TrainingJobResponse
from backend.forgellm_api.services.training_service import TrainingService
from backend.forgellm_api.services.event_service import event_service
from backend.forgellm_api.api.dependencies.auth import get_current_user, require_role
from backend.forgellm_api.db.models.project import Project
from fastapi import HTTPException

router = APIRouter(tags=["Training"])

@router.post("/projects/{project_id}/training/jobs", response_model=TrainingJobResponse, status_code=status.HTTP_201_CREATED)
def create_training_job(
    project_id: str, 
    organization_id: str = "org_default",
    job_in: TrainingJobCreate = None, 
    db: Session = Depends(get_db),
    membership = Depends(require_role(["OWNER", "ADMIN", "DEVELOPER"]))
):
    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == organization_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this organization")
    service = TrainingService(db)
    return service.create_job(project_id, job_in)

@router.get("/training/jobs", response_model=List[TrainingJobResponse])
def list_all_jobs(
    organization_id: str = "org_default",
    project_id: str = None, 
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    membership = Depends(require_role(["OWNER", "ADMIN", "DEVELOPER", "VIEWER"]))
):
    # Enforce tenant isolation logic here
    # In a full implementation, the service should filter by organization_id
    service = TrainingService(db)
    return service.get_jobs(project_id=project_id, skip=skip, limit=limit)

@router.get("/training/jobs/{job_id}", response_model=TrainingJobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    service = TrainingService(db)
    return service.get_job(job_id)

@router.post("/training/jobs/{job_id}/cancel", response_model=TrainingJobResponse)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    service = TrainingService(db)
    return service.cancel_job(job_id)

@router.delete("/training/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    service = TrainingService(db)
    return service.delete_job(job_id)

@router.get("/training/jobs/{job_id}/events")
def get_job_events(job_id: str, limit: int = 100, db: Session = Depends(get_db)):
    return event_service.get_events(db, job_id, limit=limit)

@router.get("/training/jobs/{job_id}/metrics")
def get_job_metrics(job_id: str, limit: int = 1000, db: Session = Depends(get_db)):
    return event_service.get_metrics(db, job_id, limit=limit)

@router.get("/training/jobs/{job_id}/logs")
def get_job_logs(job_id: str, limit: int = 500, db: Session = Depends(get_db)):
    return event_service.get_logs(db, job_id, limit=limit)
