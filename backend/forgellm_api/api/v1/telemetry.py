import asyncio
import json
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry Stream"])

@router.get("/stream/{job_id}")
async def stream_training_telemetry(job_id: str):
    """Stream real-time training telemetry, loss curves, and GPU metrics via Server-Sent Events (SSE)."""
    
    async def event_generator():
        # Simulated live metric stream for training job telemetry
        epochs = 5
        steps_per_epoch = 10
        total_steps = epochs * steps_per_epoch
        initial_loss = 2.45

        for step in range(1, total_steps + 1):
            epoch = (step - 1) // steps_per_epoch + 1
            loss = round(max(0.12, initial_loss * (0.85 ** step) + 0.05), 4)
            gpu_mem_mb = round(3200 + (step * 15) % 800, 1)

            data = {
                "job_id": job_id,
                "step": step,
                "total_steps": total_steps,
                "epoch": epoch,
                "total_epochs": epochs,
                "loss": loss,
                "learning_rate": round(2e-4 * (1 - step / total_steps), 6),
                "gpu_memory_used_mb": gpu_mem_mb,
                "timestamp": time.time()
            }

            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.5)

        yield f"data: {json.dumps({'job_id': job_id, 'status': 'completed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
