from unittest.mock import MagicMock

import pytest

from backend.forgellm_api.services.scheduler_service import ResourceScheduler


@pytest.mark.asyncio
async def test_scheduler_best_fit():
    scheduler = ResourceScheduler()
    # Mock Redis lock to always succeed
    scheduler.acquire_gpu_lock = MagicMock(return_value=True)
    scheduler.release_gpu_lock = MagicMock(return_value=True)
    
    # Mock Database Session and Workers
    db = MagicMock()
    
    # Mock Worker 1 (A100 - 80GB)
    worker1 = MagicMock()
    worker1.id = "w1"
    worker1.ram_available = 100
    gpu1 = MagicMock()
    gpu1.uuid = "gpu1"
    gpu1.status = "AVAILABLE"
    gpu1.memory_total = 80 * 1024
    worker1.gpus = [gpu1]
    
    # Mock Worker 2 (RTX4090 - 24GB)
    worker2 = MagicMock()
    worker2.id = "w2"
    worker2.ram_available = 64
    gpu2 = MagicMock()
    gpu2.uuid = "gpu2"
    gpu2.status = "AVAILABLE"
    gpu2.memory_total = 24 * 1024
    worker2.gpus = [gpu2]
    
    # Query return
    db.query().filter().all.return_value = [worker1, worker2]
    
    # Schedule a job requiring 16GB VRAM
    # Best-fit should select Worker 2 (24GB) instead of wasting Worker 1 (80GB)
    assignment = await scheduler.schedule_job(
        db=db,
        job_id="job-123",
        job_type="training",
        required_gpus=1,
        min_vram_gb=16
    )
    
    assert assignment.worker_id == "w2"
    assert gpu2.status == "ALLOCATED"
    assert gpu2.current_job_id == "job-123"
