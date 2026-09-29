from unittest.mock import MagicMock, patch

from backend.forgellm_api.db.models.training import TrainingJob
from workers.forgellm_worker.tasks.training import (
    CeleryTrainingProgressCallback,
    run_training_job,
)


@patch("workers.forgellm_worker.tasks.training.ForgeTrainer")
@patch("workers.forgellm_worker.tasks.training.SessionLocal")
def test_celery_run_training_job_invokes_forge_trainer(
    mock_session_local, mock_forge_trainer_cls
):
    db_mock = MagicMock()
    mock_session_local.return_value = db_mock

    # Set up mock job
    job = TrainingJob(
        id="test-job-42",
        project_id="proj-100",
        dataset_version_id="dv-1",
        model_name="Qwen/Qwen2.5-0.5B",
        method="qlora",
        epochs=1.0,
        learning_rate=0.0002,
        lora_rank=16,
        status="queued",
    )
    job.dataset_version = MagicMock(
        processed_path="data/raw/train.jsonl", version_tag="v1.0"
    )
    db_mock.query().filter().first.return_value = job

    # Set up mock ForgeTrainer instance
    mock_trainer_instance = MagicMock()
    mock_forge_trainer_cls.return_value = mock_trainer_instance

    result = run_training_job("test-job-42")

    assert result is True
    assert mock_forge_trainer_cls.called
    assert mock_trainer_instance.train.called
    assert mock_trainer_instance.save_model.called
    assert job.status == "completed"


@patch("workers.forgellm_worker.tasks.training.ForgeTrainer")
@patch("workers.forgellm_worker.tasks.training.SessionLocal")
def test_celery_run_training_job_handles_failure(
    mock_session_local, mock_forge_trainer_cls
):
    db_mock = MagicMock()
    mock_session_local.return_value = db_mock

    job = TrainingJob(
        id="test-job-fail",
        project_id="proj-100",
        dataset_version_id="dv-1",
        model_name="Qwen/Qwen2.5-0.5B",
        method="qlora",
        epochs=1.0,
        learning_rate=0.0002,
        lora_rank=16,
        status="queued",
    )
    job.dataset_version = MagicMock(
        processed_path="data/raw/train.jsonl", version_tag="v1.0"
    )
    db_mock.query().filter().first.return_value = job

    # Simulate runtime failure during training
    mock_trainer_instance = MagicMock()
    mock_trainer_instance.train.side_effect = RuntimeError("CUDA Out Of Memory")
    mock_forge_trainer_cls.return_value = mock_trainer_instance

    result = run_training_job("test-job-fail")

    assert result is False
    assert job.status == "failed"
    assert "CUDA Out Of Memory" in job.error_message


@patch("workers.forgellm_worker.tasks.training.SessionLocal")
def test_celery_run_training_job_cancelled_before_start(mock_session_local):
    db_mock = MagicMock()
    mock_session_local.return_value = db_mock

    job = TrainingJob(
        id="test-job-cancelled",
        project_id="proj-100",
        status="cancelled",
    )
    db_mock.query().filter().first.return_value = job

    result = run_training_job("test-job-cancelled")
    assert result is False


def test_celery_callback_cancellation_during_step():
    db_mock = MagicMock()
    db_factory = MagicMock(return_value=db_mock)

    job = TrainingJob(
        id="test-job-active",
        project_id="proj-100",
        status="cancel_requested",
    )
    db_mock.query().filter().first.return_value = job

    callback = CeleryTrainingProgressCallback(
        job_id="test-job-active", db_factory=db_factory
    )
    control = MagicMock()
    control.should_training_stop = False

    callback.on_step_begin(args=MagicMock(), state=MagicMock(), control=control)

    assert control.should_training_stop is True
    assert job.status == "cancelled"


def test_celery_callback_progress_logging():
    db_mock = MagicMock()
    db_factory = MagicMock(return_value=db_mock)

    job = TrainingJob(
        id="test-job-prog",
        project_id="proj-100",
        status="running",
        current_step=0,
        total_steps=100,
    )
    db_mock.query().filter().first.return_value = job

    callback = CeleryTrainingProgressCallback(
        job_id="test-job-prog", db_factory=db_factory
    )
    state = MagicMock(global_step=10, max_steps=100, epoch=1.0)
    args = MagicMock(learning_rate=0.0002)

    callback.on_log(args=args, state=state, control=MagicMock(), logs={"loss": 0.4251})

    assert job.current_step == 10
    assert job.current_loss == 0.4251
    assert job.current_epoch == 1.0
