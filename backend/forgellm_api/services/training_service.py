from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List

from backend.forgellm_api.db.models.project import Project
from backend.forgellm_api.db.models.dataset import DatasetVersion
from backend.forgellm_api.db.models.training import TrainingJob
from backend.forgellm_api.schemas.training import TrainingJobCreate
from workers.forgellm_worker.tasks.training import run_training_job


class TrainingService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, project_id: str, job_in: TrainingJobCreate) -> TrainingJob:
        # Validate project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate dataset version
        ds_version = (
            self.db.query(DatasetVersion)
            .filter(DatasetVersion.id == job_in.dataset_version_id)
            .first()
        )
        if not ds_version:
            raise HTTPException(status_code=404, detail="Dataset version not found")

        # Create record
        job = TrainingJob(
            project_id=project_id,
            dataset_version_id=job_in.dataset_version_id,
            model_name=job_in.model_name,
            method=job_in.method,
            preset=job_in.preset,
            epochs=job_in.epochs,
            learning_rate=job_in.learning_rate,
            lora_rank=job_in.lora_rank,
            status="queued",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # Dispatch Celery Task
        run_training_job.delay(job.id)

        return job

    def get_jobs(
        self, project_id: str = None, skip: int = 0, limit: int = 100
    ) -> List[TrainingJob]:
        query = self.db.query(TrainingJob)
        if project_id:
            query = query.filter(TrainingJob.project_id == project_id)
        return query.offset(skip).limit(limit).all()

    def get_job(self, job_id: str) -> TrainingJob:
        job = self.db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")
        return job

    def cancel_job(self, job_id: str) -> TrainingJob:
        job = self.get_job(job_id)

        if job.status not in ["queued", "running"]:
            raise HTTPException(
                status_code=409, detail=f"Cannot cancel job in {job.status} status."
            )

        # The celery worker will notice this state change on its next iteration and gracefully stop.
        job.status = "cancel_requested"
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job_id: str):
        job = self.get_job(job_id)
        if job.status in ["running"]:
            raise HTTPException(
                status_code=409, detail="Cannot delete a running job. Cancel it first."
            )

        self.db.delete(job)
        self.db.commit()
        return {"status": "success", "message": "Job deleted"}
