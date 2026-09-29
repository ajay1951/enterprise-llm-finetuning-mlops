import asyncio
import logging
from typing import Dict, List, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # job_id -> list of active websockets
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        async with self.lock:
            if job_id not in self.active_connections:
                self.active_connections[job_id] = []
            self.active_connections[job_id].append(websocket)
        logger.info(
            f"Client connected to job {job_id}. Total clients for job: {len(self.active_connections[job_id])}"
        )

    async def disconnect(self, websocket: WebSocket, job_id: str):
        async with self.lock:
            if job_id in self.active_connections:
                if websocket in self.active_connections[job_id]:
                    self.active_connections[job_id].remove(websocket)
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]
        logger.info(f"Client disconnected from job {job_id}.")

    async def send_to_job(self, job_id: str, message: str):
        if job_id in self.active_connections:
            # We copy the list to avoid runtime errors if a socket disconnects while iterating
            connections = list(self.active_connections[job_id])
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning(f"Error sending to websocket: {e}")
                    await self.disconnect(connection, job_id)


manager = ConnectionManager()
