from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import HTTPException

from backend.forgellm_api.core.gateway.retry import with_retry_and_fallback
from backend.forgellm_api.core.gateway.router import select_replica
from backend.forgellm_api.db.models.deployment import Deployment


@pytest.mark.asyncio
async def test_retry_success_after_failure():
    attempts = 0

    async def flaky_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise httpx.ConnectError("Connection refused")
        return "SUCCESS"

    result, _ = await with_retry_and_fallback(
        flaky_operation, max_retries=2, base_delay=0.01
    )

    assert result == "SUCCESS"
    assert attempts == 2


@pytest.mark.asyncio
async def test_fallback_triggers_after_max_retries():
    attempts = 0

    async def failing_operation():
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("Connection refused")

    async def fallback_operation():
        return "FALLBACK_SUCCESS", None

    result, _ = await with_retry_and_fallback(
        failing_operation, fallback_operation, max_retries=2, base_delay=0.01
    )

    assert result == "FALLBACK_SUCCESS"
    assert attempts == 3  # Initial attempt + 2 retries


@pytest.mark.asyncio
async def test_http_4xx_does_not_retry():
    attempts = 0

    async def failing_operation():
        nonlocal attempts
        attempts += 1
        raise HTTPException(status_code=400, detail="Bad Request")

    with pytest.raises(HTTPException) as exc:
        await with_retry_and_fallback(failing_operation, max_retries=2, base_delay=0.01)

    assert exc.value.status_code == 400
    assert attempts == 1  # No retries for 400


def test_least_loaded_routing_strategy():
    dep1 = Deployment(id="dep1")
    dep2 = Deployment(id="dep2")
    dep3 = Deployment(id="dep3")

    mock_redis = MagicMock()
    # Mock redis returning active load: dep1=5, dep2=1, dep3=10
    mock_redis.mget.return_value = ["5", "1", "10"]

    chosen = select_replica(
        [dep1, dep2, dep3], strategy="LEAST_LOADED", redis_client=mock_redis
    )

    assert chosen.id == "dep2"
