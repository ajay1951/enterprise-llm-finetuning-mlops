import os
import hashlib
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.forgellm_api.db.models.project import Project
from backend.forgellm_api.db.models.dataset import Dataset, DatasetVersion
from backend.forgellm_api.schemas.dataset import DatasetBase, DatasetResponse
from backend.forgellm_api.storage.base import StorageInterface


class DatasetService:
    def __init__(self, db: Session, storage: StorageInterface):
        self.db = db
        self.storage = storage

    def create_dataset_and_upload(
        self, project_id: str, name: str, description: str, file: UploadFile
    ) -> DatasetResponse:
        # Check project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 1. Create Dataset record
        dataset = Dataset(project_id=project_id, name=name, description=description)
        self.db.add(dataset)
        self.db.flush()

        # 2. Save original file
        dataset_dir = f"projects/{project_id}/datasets/{dataset.id}"
        original_filename = file.filename
        if not original_filename.endswith((".jsonl", ".csv")):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JSONL or CSV supported.",
            )

        file_path = f"{dataset_dir}/original/{original_filename}"

        # Calculate SHA256 while saving
        sha256 = hashlib.sha256()
        file_content = file.file.read()
        sha256.update(file_content)
        file.file.seek(0)

        # Save through storage interface
        self.storage.save(file_path, file.file)

        # 3. Create DatasetVersion record
        version = DatasetVersion(
            dataset_id=dataset.id,
            version_tag="v1",
            original_path=file_path,
            status="pending",
            file_hash=sha256.hexdigest(),
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(dataset)

        return dataset

    def get_datasets(self, project_id: str) -> List[Dataset]:
        return self.db.query(Dataset).filter(Dataset.project_id == project_id).all()

    def get_dataset(self, dataset_id: str) -> Dataset:
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return dataset

    def trigger_validation(self, dataset_id: str):
        # We will dispatch a Celery task here soon!
        pass

    def trigger_prepare(self, dataset_id: str):
        # We will dispatch a Celery task here soon!
        pass
