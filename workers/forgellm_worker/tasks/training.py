from workers.forgellm_worker.celery_app import celery_app
from backend.forgellm_api.db.session import SessionLocal
from backend.forgellm_api.db.models.training import TrainingJob
from backend.forgellm_api.services.event_service import event_service
import logging
import time
import uuid

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="run_training_job")
def run_training_job(self, job_id: str):
    logger.info(f"Starting training job {job_id}")
    
    db = SessionLocal()
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
        
        sequence = 1
        event_service.publish_and_persist_event(db, job_id, "training.started", sequence, {"status": "running"})
        sequence += 1
        event_service.publish_log(db, job_id, sequence, "INFO", "Training started")
        sequence += 1

        # For now, simulate training steps to verify state transitions.
        try:
            total_steps = 100
            job.total_steps = total_steps
            event_service.publish_log(db, job_id, sequence, "INFO", f"Prepared model for {total_steps} steps")
            sequence += 1
            
            for step in range(1, total_steps + 1):
                # Check for cancellation
                db.refresh(job)
                if job.status == "cancel_requested":
                    job.status = "cancelled"
                    db.commit()
                    event_service.publish_and_persist_event(db, job_id, "training.cancelled", sequence, {"status": "cancelled"})
                    sequence += 1
                    event_service.publish_log(db, job_id, sequence, "WARNING", "Training cancelled by user")
                    logger.info(f"Job {job_id} cancelled during training.")
                    return False
                
                # Simulate work
                time.sleep(0.5)
                
                # Update progress
                current_loss = 1.0 / step
                job.current_step = step
                job.current_epoch = step / total_steps
                job.current_loss = current_loss
                db.commit()
                
                # Publish metric (throttle to ~2 per second due to sleep(0.5))
                metric_data = {
                    "step": step,
                    "epoch": step / total_steps,
                    "loss": current_loss,
                    "learning_rate": 0.0002,
                    "samples_per_second": 12.5,
                    "tokens_per_second": 4500.0
                }
                event_service.publish_metric(db, job_id, sequence, metric_data, persist=True)
                sequence += 1
                
                event_service.publish_and_persist_event(db, job_id, "training.progress", sequence, metric_data)
                sequence += 1

                if step % 20 == 0:
                    event_service.publish_log(db, job_id, sequence, "INFO", f"Step {step} / {total_steps} completed. Loss: {current_loss:.4f}")
                    sequence += 1
                
            job.status = "completed"
            db.commit()
            
            event_service.publish_and_persist_event(db, job_id, "training.completed", sequence, {"status": "completed"})
            sequence += 1
            event_service.publish_log(db, job_id, sequence, "INFO", "Training completed successfully.")
            
            logger.info(f"Job {job_id} completed successfully.")
            return True
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            
            event_service.publish_and_persist_event(db, job_id, "training.failed", sequence, {"status": "failed", "error": str(e)})
            sequence += 1
            event_service.publish_log(db, job_id, sequence, "ERROR", f"Training failed: {str(e)}")
            
            logger.error(f"Job {job_id} failed: {str(e)}")
            return False
            
    finally:
        from backend.forgellm_api.monitoring.heartbeat import heartbeat_thread
        heartbeat_thread.clear_active_job()
        db.close()
