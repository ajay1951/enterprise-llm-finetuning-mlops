from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from backend.forgellm_api.core.rate_limit import RateLimiter


@pytest.fixture
def mock_redis():
    with patch("backend.forgellm_api.core.rate_limit.redis_client") as mock:
        yield mock

@pytest.mark.asyncio
async def test_rate_limiter_success(mock_redis):
    pipe_mock = AsyncMock()
    pipe_mock.execute.return_value = [None, None, None, 5]
    mock_redis.pipeline.return_value = pipe_mock

    limiter = RateLimiter(requests=10, window=60)
    
    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"

    await limiter(mock_request)

@pytest.mark.asyncio
async def test_rate_limiter_exceeded(mock_redis):
    pipe_mock = AsyncMock()
    pipe_mock.execute.return_value = [None, None, None, 11]
    mock_redis.pipeline.return_value = pipe_mock

    limiter = RateLimiter(requests=10, window=60)
    
    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"

    with pytest.raises(HTTPException) as excinfo:
        await limiter(mock_request)
    
    assert excinfo.value.status_code == 429
    assert "Rate limit exceeded" in excinfo.value.detail
