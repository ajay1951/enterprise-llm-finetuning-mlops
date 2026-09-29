from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.forgellm_api.db.models import *  # Ensure all models are loaded
from backend.forgellm_api.db.models.training import TrainingJob
from backend.forgellm_api.db.session import Base
from backend.forgellm_api.schemas.project import ProjectCreate
from backend.forgellm_api.schemas.training import TrainingJobCreate
from backend.forgellm_api.services.dataset_service import DatasetService
from backend.forgellm_api.services.project_service import ProjectService
from backend.forgellm_api.services.training_service import TrainingService
from workers.forgellm_worker.tasks.training import run_training_job

# Use SQLite for isolated integration tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_full_pipeline_end_to_end():
    db = TestingSessionLocal()
    try:
        # 1. Create Project
        proj_service = ProjectService(db, "org_default")
        project = proj_service.create_project(
            ProjectCreate(
                name="Integration Test Project", description="Testing pipeline"
            )
        )
        assert project.id is not None

        # 2. Upload Dataset
        mock_storage = MagicMock()
        mock_storage.save.return_value = "projects/p1/datasets/d1/original/test.jsonl"
        ds_service = DatasetService(db, mock_storage)

        mock_file = MagicMock()
        mock_file.filename = "test.jsonl"
        mock_file.file.read.return_value = (
            b'{"messages": [{"role": "user", "content": "hi"}]}'
        )
        dataset = ds_service.create_dataset_and_upload(
            project_id=project.id,
            name="Test Dataset",
            description="Test Data",
            file=mock_file,
        )
        assert len(dataset.versions) == 1
        version_id = dataset.versions[0].id

        # 3. Create Training Job
        training_service = TrainingService(db)
        with patch("workers.forgellm_worker.tasks.training.run_training_job.delay"):
            job = training_service.create_job(
                project_id=project.id,
                job_in=TrainingJobCreate(
                    dataset_version_id=version_id,
                    model_name="Qwen/Qwen2.5-0.5B",
                    method="qlora",
                ),
            )
            assert job.id is not None
            assert job.status == "queued"

        # 4. Celery Worker Execution -> ForgeTrainer -> Model Artifact
        with (
            patch(
                "workers.forgellm_worker.tasks.training.SessionLocal",
                TestingSessionLocal,
            ),
            patch(
                "workers.forgellm_worker.tasks.training.ForgeTrainer"
            ) as mock_trainer_cls,
        ):
            mock_trainer = mock_trainer_cls.return_value
            result = run_training_job(job.id)
            assert result is True
            assert mock_trainer.train.called
            assert mock_trainer.save_model.called

        # 5. Verify DB state transition
        db.refresh(job)
        assert job.status == "completed"
    finally:
        db.close()
