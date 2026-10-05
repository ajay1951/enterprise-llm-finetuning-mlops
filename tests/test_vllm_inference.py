from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from serving.forgellm_server.backends.vllm_backend import VLLMBackend
from serving.forgellm_server.engine import InferenceEngine


@pytest.mark.asyncio
async def test_vllm_backend_load_and_unload():
    backend = VLLMBackend()
    success = await backend.load_model(
        base_model="Qwen/Qwen2.5-0.5B",
        device="cuda",
        config={"vllm_endpoint": "http://localhost:8000/v1", "request_timeout": 15.0},
    )
    assert success is True
    assert backend.is_loaded is True
    assert backend.model_name == "Qwen/Qwen2.5-0.5B"
    assert backend.endpoint_url == "http://localhost:8000/v1"

    await backend.unload_model()
    assert backend.is_loaded is False
    assert backend.client is None


@pytest.mark.asyncio
async def test_vllm_backend_generate_stream_success():
    backend = VLLMBackend()
    await backend.load_model(base_model="Qwen/Qwen2.5-0.5B")

    # Mock SSE stream lines
    mock_lines = [
        'data: {"choices": [{"delta": {"content": "Forge"}}]}',
        'data: {"choices": [{"delta": {"content": "LLM"}}]}',
        'data: {"choices": [{"delta": {"content": " is ready."}}]}',
        "data: [DONE]",
    ]

    async def mock_aiter_lines():
        for line in mock_lines:
            yield line

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = mock_aiter_lines
    mock_response.__aenter__.return_value = mock_response

    backend.client = MagicMock()
    backend.client.stream.return_value = mock_response

    tokens = []
    messages = [{"role": "user", "content": "What is ForgeLLM?"}]
    async for token in backend.generate_stream(messages, temperature=0.0):
        tokens.append(token)

    assert tokens == ["Forge", "LLM", " is ready."]


@pytest.mark.asyncio
async def test_vllm_backend_generate_batch_success():
    backend = VLLMBackend()
    await backend.load_model(base_model="Qwen/Qwen2.5-0.5B")

    mock_lines = [
        'data: {"choices": [{"delta": {"content": "Hello "}}]}',
        'data: {"choices": [{"delta": {"content": "World!"}}]}',
        "data: [DONE]",
    ]

    async def mock_aiter_lines():
        for line in mock_lines:
            yield line

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = mock_aiter_lines
    mock_response.__aenter__.return_value = mock_response

    backend.client = MagicMock()
    backend.client.stream.return_value = mock_response

    messages = [{"role": "user", "content": "Hi"}]
    result = await backend.generate(messages)
    assert result == "Hello World!"


@pytest.mark.asyncio
async def test_vllm_backend_server_error_handling():
    backend = VLLMBackend()
    await backend.load_model(base_model="Qwen/Qwen2.5-0.5B")

    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.aread = AsyncMock(return_value=b"Internal GPU Error")
    mock_response.__aenter__.return_value = mock_response

    backend.client = MagicMock()
    backend.client.stream.return_value = mock_response

    messages = [{"role": "user", "content": "Test"}]
    with pytest.raises(RuntimeError) as exc_info:
        async for _ in backend.generate_stream(messages):
            pass

    assert "vLLM server returned error 500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_vllm_backend_connection_error_handling():
    backend = VLLMBackend()
    await backend.load_model(base_model="Qwen/Qwen2.5-0.5B")

    backend.client = MagicMock()
    backend.client.stream.side_effect = httpx.ConnectError("Connection refused")

    messages = [{"role": "user", "content": "Test"}]
    with pytest.raises(RuntimeError) as exc_info:
        async for _ in backend.generate_stream(messages):
            pass

    assert "vLLM server connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_vllm_backend_unloaded_error():
    backend = VLLMBackend()
    messages = [{"role": "user", "content": "Test"}]
    with pytest.raises(RuntimeError) as exc_info:
        async for _ in backend.generate_stream(messages):
            pass

    assert "vLLM backend is not loaded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_engine_vllm_backend_selection():
    engine = InferenceEngine()
    with patch.object(VLLMBackend, "load_model", AsyncMock(return_value=True)):
        success = await engine.initialize(
            backend_type="vllm",
            base_model="Qwen/Qwen2.5-0.5B",
            config={"vllm_endpoint": "http://localhost:8000/v1"},
        )
        assert success is True
        assert isinstance(engine.backend, VLLMBackend)
        assert engine.is_ready is True

    await engine.shutdown()
    assert engine.is_ready is False
