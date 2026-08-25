from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import asyncio
from backend.forgellm_api.realtime.connection_manager import manager
from backend.forgellm_api.realtime.redis_bus import redis_bus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Real-time"])

@router.websocket("/ws/training/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    
    pubsub = None
    try:
        pubsub = await redis_bus.subscribe(job_id)
        
        # We need a loop to read from websocket to detect client disconnects
        async def read_from_socket():
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass
                
        # We need a loop to read from redis and broadcast to sockets
        async def read_from_redis():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await manager.send_to_job(job_id, message["data"])

        # Run both concurrently
        await asyncio.gather(
            read_from_socket(),
            read_from_redis(),
            return_exceptions=True
        )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        await manager.disconnect(websocket, job_id)
        if pubsub:
            await pubsub.unsubscribe(redis_bus.get_channel(job_id))
            await pubsub.close()
