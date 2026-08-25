import time
from fastapi import Request, HTTPException, status
import redis.asyncio as redis
from backend.forgellm_api.core.config import get_settings

settings = get_settings()

redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
RATE_LIMIT_REQUESTS = getattr(settings, "RATE_LIMIT_REQUESTS", 100)
RATE_LIMIT_WINDOW_SECONDS = getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)

# Global redis client for dependency
redis_client = redis.from_url(redis_url, decode_responses=True)

class RateLimiter:
    def __init__(self, requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW_SECONDS):
        self.requests = requests
        self.window = window

    async def __call__(self, request: Request):
        # Identify the client by API key if present, otherwise IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        auth_header = request.headers.get("Authorization")
        
        identifier = client_ip
        if auth_header and auth_header.startswith("Bearer sk-"):
            identifier = auth_header.split(" ")[1] # use API key as identifier
            
        key = f"rate_limit:{identifier}"
        now = int(time.time())
        window_start = now - self.window
        
        async with redis_client.pipeline(transaction=True) as pipe:
            # Clean up old requests
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current requests in window
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {str(now) + "-" + str(id(request)): now})
            # Set expiry on the key to avoid memory leak
            pipe.expire(key, self.window)
            
            results = await pipe.execute()
            
        request_count = results[1]
        
        if request_count >= self.requests:
            retry_after = self.window - (now - window_start) # Rough estimate
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests",
                headers={"Retry-After": str(max(1, retry_after))}
            )
        return True

rate_limit = RateLimiter()
