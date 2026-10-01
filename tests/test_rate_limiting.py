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
    pipe_mock = MagicMock()
    pipe_mock.execute = AsyncMock(return_value=[None, 5, None, None])
    pipe_mock.__aenter__.return_value = pipe_mock
    pipe_mock.__aexit__.return_value = None
    mock_redis.pipeline = MagicMock(return_value=pipe_mock)

    limiter = RateLimiter(requests=10, window=60)

    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {}

    res = await limiter(mock_request)
    assert res is True


@pytest.mark.asyncio
async def test_rate_limiter_exceeded(mock_redis):
    pipe_mock = MagicMock()
    pipe_mock.execute = AsyncMock(return_value=[None, 11, None, None])
    pipe_mock.__aenter__.return_value = pipe_mock
    pipe_mock.__aexit__.return_value = None
    mock_redis.pipeline = MagicMock(return_value=pipe_mock)

    limiter = RateLimiter(requests=10, window=60)

    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {}

    with pytest.raises(HTTPException) as excinfo:
        await limiter(mock_request)

    assert excinfo.value.status_code == 429
    assert (
        "Too Many Requests" in excinfo.value.detail
        or "Rate limit" in excinfo.value.detail
    )
