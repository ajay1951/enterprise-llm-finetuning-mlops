import redis.asyncio as redis
import json
import logging
from backend.forgellm_api.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RedisEventBus:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._redis = None

    async def connect(self):
        if not self._redis:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Connected to Redis Event Bus")

    async def disconnect(self):
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    def get_channel(self, job_id: str) -> str:
        return f"forgellm:job:{job_id}"

    async def publish(self, job_id: str, event_data: dict):
        if not self._redis:
            await self.connect()
        channel = self.get_channel(job_id)
        message = json.dumps(event_data)
        await self._redis.publish(channel, message)

    async def subscribe(self, job_id: str):
        if not self._redis:
            await self.connect()
        pubsub = self._redis.pubsub()
        channel = self.get_channel(job_id)
        await pubsub.subscribe(channel)
        return pubsub

redis_bus = RedisEventBus()
