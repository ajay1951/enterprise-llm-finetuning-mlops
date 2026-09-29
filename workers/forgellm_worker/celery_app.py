import os

from celery import Celery

from backend.forgellm_api.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "forgellm_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "workers.forgellm_worker.tasks.training",
        "workers.forgellm_worker.tasks.deployment",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.CELERY_TASK_TIMEOUT,
)

from celery.signals import worker_process_init


@worker_process_init.connect
def init_worker(**kwargs):
    from backend.forgellm_api.monitoring.heartbeat import heartbeat_thread

    heartbeat_thread.start()
