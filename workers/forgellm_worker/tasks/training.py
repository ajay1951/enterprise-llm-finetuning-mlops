import logging
import os

import yaml
from transformers import TrainerCallback

from backend.forgellm_api.db.models.training import Checkpoint, Experiment, TrainingJob
from backend.forgellm_api.db.session import SessionLocal
from backend.forgellm_api.services.event_service import event_service
from forgellm.training.trainer import ForgeTrainer
from workers.forgellm_worker.celery_app import celery_app

logger = logging.getLogger(__name__)


class CeleryTrainingProgressCallback(TrainerCallback):
    """Bridge Hugging Face Trainer step logs to Celery events and DB progress."""

    def __init__(self, job_id: str, db_factory):
        self.job_id = job_id
        self.db_factory = db_factory
        self.sequence = 10

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return
        db = self.db_factory()
        try:
            job = db.query(TrainingJob).filter(TrainingJob.id == self.job_id).first()
            if not job:
                return

            step = state.global_step
            total_steps = state.max_steps if state.max_steps > 0 else job.total_steps
            epoch = state.epoch if state.epoch is not None else 0.0
            loss = logs.get("loss") or logs.get("train_loss")

            job.current_step = step
            if total_steps > 0:
                job.total_steps = total_steps
            job.current_epoch = epoch
            if loss is not None:
                job.current_loss = float(loss)
            db.commit()

            metric_data = {
                "step": step,
                "epoch": epoch,
                "loss": float(loss) if loss is not None else job.current_loss,
                "learning_rate": logs.get("learning_rate", args.learning_rate),
            }
            event_service.publish_metric(
                db, self.job_id, self.sequence, metric_data, persist=True
            )
            self.sequence += 1
            event_service.publish_and_persist_event(
                db, self.job_id, "training.progress", self.sequence, metric_data
            )
            self.sequence += 1
        except Exception as e:
            logger.warning(f"Error logging progress in callback: {e}")
        finally:
            db.close()

    def on_step_begin(self, args, state, control, **kwargs):
        db = self.db_factory()
        try:
            job = db.query(TrainingJob).filter(TrainingJob.id == self.job_id).first()
            if job and job.status == "cancel_requested":
                control.should_training_stop = True
                job.status = "cancelled"
                db.commit()
                event_service.publish_and_persist_event(
                    db,
                    self.job_id,
                    "training.cancelled",
                    self.sequence,
                    {"status": "cancelled"},
                )
                self.sequence += 1
                event_service.publish_log(
                    db,
                    self.job_id,
                    self.sequence,
                    "WARNING",
                    "Training cancelled by user request",
                )
                logger.info(f"Job {self.job_id} cancelled during training.")
        except Exception as e:
            logger.warning(f"Error checking cancel status: {e}")
        finally:
            db.close()


@celery_app.task(bind=True, name="run_training_job")
def run_training_job(self, job_id: str):
    logger.info(f"Starting training job {job_id}")

    db = SessionLocal()
    sequence = 1
    job = None
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return False

        if job.status == "cancelled":
            logger.info(f"Job {job_id} was cancelled before starting.")
            return False

        # Update status to running
        job.status = "running"
        db.commit()

        from backend.forgellm_api.monitoring.heartbeat import heartbeat_thread

        heartbeat_thread.set_active_job(job_id)

        event_service.publish_and_persist_event(
            db, job_id, "training.started", sequence, {"status": "running"}
        )
        sequence += 1
        event_service.publish_log(
            db, job_id, sequence, "INFO", f"Training started for job {job_id}"
        )
        sequence += 1

        output_dir = os.path.join("outputs", f"job_{job_id}")
        os.makedirs(output_dir, exist_ok=True)

        # Resolve dataset paths
        train_path = ""
        val_path = ""
        if job.dataset_version:
            train_path = (
                job.dataset_version.processed_path
                or job.dataset_version.original_path
                or ""
            )
        if not train_path or not os.path.exists(train_path):
            # Fallback to default raw train if specified path is not found
            if os.path.exists("data/raw/train.jsonl"):
                train_path = "data/raw/train.jsonl"

        config_dict = {
            "model": {
                "name": job.model_name or "Qwen/Qwen2.5-0.5B",
                "model_version": "latest",
                "trust_remote_code": True,
            },
            "dataset": {
                "train_file": train_path or "data/raw/train.jsonl",
                "val_file": val_path if val_path and os.path.exists(val_path) else None,
                "version": job.dataset_version.version_tag
                if job.dataset_version
                else "v1.0",
                "max_seq_length": 2048,
            },
            "training": {
                "experiment_name": f"project_{job.project_id}",
                "mlflow_tracking_uri": os.getenv(
                    "MLFLOW_TRACKING_URI", "http://localhost:5000"
                ),
                "output_dir": output_dir,
                "num_train_epochs": max(1, int(job.epochs or 1)),
                "learning_rate": job.learning_rate or 0.0002,
                "logging_steps": 10,
                "save_steps": 100,
                "eval_steps": 0,
            },
            "lora": {
                "r": job.lora_rank or 16,
                "alpha": (job.lora_rank or 16) * 2,
                "dropout": 0.05,
                "target_modules": ["q_proj", "v_proj"],
            },
            "quantization": {
                "enabled": (job.method == "qlora"),
                "bits": 4,
            },
        }

        config_yaml_path = os.path.join(output_dir, "config.yaml")
        with open(config_yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_dict, f)

        # Flow: API -> Celery -> ForgeTrainer -> MLflow -> Model Artifact
        trainer = ForgeTrainer(config_yaml_path)
        if train_path and os.path.exists(train_path):
            trainer.prepare_dataset(train_path, val_path)

        callback = CeleryTrainingProgressCallback(job_id, SessionLocal)
        trainer.train(callbacks=[callback])

        adapter_path = os.path.join(output_dir, "adapter")
        trainer.save_model(adapter_path)

        # Persist experiment and checkpoint records
        experiment = (
            db.query(Experiment).filter(Experiment.training_job_id == job_id).first()
        )
        if not experiment:
            experiment = Experiment(
                training_job_id=job_id,
                configuration=config_dict,
                metrics={"final_loss": job.current_loss},
            )
            db.add(experiment)
            db.flush()

        checkpoint = Checkpoint(
            experiment_id=experiment.id,
            step=job.current_step or 1,
            path=adapter_path,
        )
        db.add(checkpoint)

        job.status = "completed"
        db.commit()

        event_service.publish_and_persist_event(
            db, job_id, "training.completed", sequence, {"status": "completed"}
        )
        sequence += 1
        event_service.publish_log(
            db,
            job_id,
            sequence,
            "INFO",
            "Training completed successfully via ForgeTrainer.",
        )

        logger.info(f"Job {job_id} completed successfully via ForgeTrainer.")
        return True

    except Exception as e:
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()

        event_service.publish_and_persist_event(
            db,
            job_id,
            "training.failed",
            sequence,
            {"status": "failed", "error": str(e)},
        )
        sequence += 1
        event_service.publish_log(
            db, job_id, sequence, "ERROR", f"Training failed: {e!s}"
        )

        logger.error(f"Job {job_id} failed: {e!s}")
        return False

    finally:
        from backend.forgellm_api.monitoring.heartbeat import heartbeat_thread

        heartbeat_thread.clear_active_job()
        db.close()
