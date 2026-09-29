import pytest
from fastapi.testclient import TestClient

from backend.forgellm_api.db.models import *  # Ensure all models are loaded
from backend.forgellm_api.db.models.training import TrainingJob
from backend.forgellm_api.db.session import Base, SessionLocal, engine
from backend.forgellm_api.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_full_pipeline():
    # 1. Create Project
    res = client.post(
        "/api/v1/projects/",
        json={
            "name": "Integration Test Project",
            "description": "Testing the pipeline",
        },
    )
    assert res.status_code == 201
    project_id = res.json()["id"]

    # 2. Upload Dataset
    # Mocking file upload
    file_content = b'{"messages": [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]}'
    res = client.post(
        f"/api/v1/projects/{project_id}/datasets/",
        data={"name": "Test Dataset", "description": "Test Data"},
        files={"file": ("test.jsonl", file_content, "application/json")},
    )
    assert res.status_code == 201
    dataset = res.json()
    assert len(dataset["versions"]) == 1
    version_id = dataset["versions"][0]["id"]

    # 3. Create Training Job
    res = client.post(
        f"/api/v1/projects/{project_id}/training/jobs",
        json={
            "dataset_version_id": version_id,
            "model_name": "Qwen/Qwen2.5-0.5B",
            "method": "qlora",
        },
    )
    assert res.status_code == 201
    job_id = res.json()["id"]
    assert res.json()["status"] == "queued"

    # 4. Mock Celery Task Execution
    # Since we use celery locally, we can just call the task directly
    # to simulate a worker picking it up.
    # In a real test, you might use CELERY_ALWAYS_EAGER=True
    from workers.forgellm_worker.tasks.training import run_training_job

    result = run_training_job.apply(args=[job_id])
    assert result.successful()

    # Wait for DB to reflect the completed state
    db = SessionLocal()
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    assert job.status == "completed"
    assert job.current_step == 10
    db.close()
