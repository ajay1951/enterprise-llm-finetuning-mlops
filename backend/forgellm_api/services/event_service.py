import json
import logging
import uuid
from datetime import UTC, datetime

import redis
from sqlalchemy.orm import Session

from backend.forgellm_api.core.config import get_settings
from backend.forgellm_api.db.models.events import JobEvent, TrainingLog, TrainingMetric

logger = logging.getLogger(__name__)
settings = get_settings()


class EventService:
    def __init__(self):
        self.redis_client = None

    def _get_redis(self):
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
        return self.redis_client

    def _publish_safe(self, channel: str, message: str):
        try:
            self._get_redis().publish(channel, message)
        except Exception as e:
            logger.debug(f"Could not publish to Redis: {e}")

    def publish_and_persist_event(
        self, db: Session, job_id: str, event_type: str, sequence: int, data: dict
    ):
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        # 1. Persist to DB
        job_event = JobEvent(
            id=event_id,
            job_id=job_id,
            event_type=event_type,
            sequence=sequence,
            timestamp=timestamp,
            data=data,
        )
        db.add(job_event)
        db.commit()

        # 2. Publish to Redis
        payload = {
            "event_id": event_id,
            "event_type": event_type,
            "job_id": job_id,
            "timestamp": timestamp.isoformat(),
            "sequence": sequence,
            "data": data,
        }
        channel = f"forgellm:job:{job_id}"
        self._publish_safe(channel, json.dumps(payload))

    def publish_metric(
        self,
        db: Session,
        job_id: str,
        sequence: int,
        metric_data: dict,
        persist: bool = False,
    ):
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        if persist:
            metric = TrainingMetric(
                id=event_id,
                job_id=job_id,
                sequence=sequence,
                timestamp=timestamp,
                step=metric_data.get("step", 0),
                epoch=metric_data.get("epoch"),
                loss=metric_data.get("loss"),
                learning_rate=metric_data.get("learning_rate"),
                samples_per_second=metric_data.get("samples_per_second"),
                tokens_per_second=metric_data.get("tokens_per_second"),
            )
            db.add(metric)
            db.commit()

        payload = {
            "event_id": event_id,
            "event_type": "training.metric",
            "job_id": job_id,
            "timestamp": timestamp.isoformat(),
            "sequence": sequence,
            "data": metric_data,
        }
        channel = f"forgellm:job:{job_id}"
        self._publish_safe(channel, json.dumps(payload))

    def publish_log(
        self, db: Session, job_id: str, sequence: int, level: str, message: str
    ):
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        log_entry = TrainingLog(
            id=event_id,
            job_id=job_id,
            sequence=sequence,
            timestamp=timestamp,
            level=level,
            message=message,
        )
        db.add(log_entry)
        db.commit()

        payload = {
            "event_id": event_id,
            "event_type": "training.log",
            "job_id": job_id,
            "timestamp": timestamp.isoformat(),
            "sequence": sequence,
            "data": {"level": level, "message": message},
        }
        channel = f"forgellm:job:{job_id}"
        self._publish_safe(channel, json.dumps(payload))

    def get_events(self, db: Session, job_id: str, limit: int = 100):
        return (
            db.query(JobEvent)
            .filter(JobEvent.job_id == job_id)
            .order_by(JobEvent.sequence.asc())
            .limit(limit)
            .all()
        )

    def get_metrics(self, db: Session, job_id: str, limit: int = 100):
        return (
            db.query(TrainingMetric)
            .filter(TrainingMetric.job_id == job_id)
            .order_by(TrainingMetric.sequence.asc())
            .limit(limit)
            .all()
        )

    def get_logs(self, db: Session, job_id: str, limit: int = 500):
        return (
            db.query(TrainingLog)
            .filter(TrainingLog.job_id == job_id)
            .order_by(TrainingLog.sequence.asc())
            .limit(limit)
            .all()
        )


event_service = EventService()
