import asyncio
import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Dict

import httpx


class ModelServerClient(ABC):
    @abstractmethod
    async def chat_completion(
        self, endpoint: str, request_body: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def stream_chat_completion(
        self, endpoint: str, request_body: dict[str, Any], headers: dict[str, str]
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def health_check(self, endpoint: str) -> bool:
        pass


class VLLMClient(ModelServerClient):
    """Client for routing to OpenAI-compatible vLLM endpoints."""

    def __init__(self, connect_timeout: float = 5.0, read_timeout: float = 120.0):
        self.timeout = httpx.Timeout(
            connect=connect_timeout, read=read_timeout, write=5.0, pool=5.0
        )

    async def chat_completion(
        self, endpoint: str, request_body: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        url = f"{endpoint.rstrip('/')}/v1/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=request_body, headers=headers)
            response.raise_for_status()
            return response.json()

    async def stream_chat_completion(
        self, endpoint: str, request_body: dict[str, Any], headers: dict[str, str]
    ) -> AsyncGenerator[str, None]:
        url = f"{endpoint.rstrip('/')}/v1/chat/completions"
        request_body["stream"] = True

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST", url, json=request_body, headers=headers
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield line + "\n\n"
                    elif line.strip() == "":
                        continue
                    else:
                        yield f"data: {line}\n\n"

    async def health_check(self, endpoint: str) -> bool:
        url = f"{endpoint.rstrip('/')}/health"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False


class MockModelServerClient(ModelServerClient):
    """Mock client for local testing without GPUs."""

    async def chat_completion(
        self, endpoint: str, request_body: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        await asyncio.sleep(0.5)  # Simulate latency
        return {
            "id": "chatcmpl-mock123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": request_body.get("model", "mock-model"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response from the ForgeLLM gateway.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
        }

    async def stream_chat_completion(
        self, endpoint: str, request_body: dict[str, Any], headers: dict[str, str]
    ) -> AsyncGenerator[str, None]:
        words = ["This ", "is ", "a ", "mock ", "streaming ", "response."]
        for w in words:
            await asyncio.sleep(0.1)
            chunk = {
                "id": "chatcmpl-mock123",
                "object": "chat.completion.chunk",
                "created": 1677652288,
                "model": request_body.get("model", "mock-model"),
                "choices": [
                    {"delta": {"content": w}, "index": 0, "finish_reason": None}
                ],
            }
            yield f"data: {json.dumps(chunk)}\n\n"

        await asyncio.sleep(0.1)
        final_chunk = {
            "id": "chatcmpl-mock123",
            "object": "chat.completion.chunk",
            "created": 1677652288,
            "model": request_body.get("model", "mock-model"),
            "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    async def health_check(self, endpoint: str) -> bool:
        return True


def get_model_client(is_mock: bool = False) -> ModelServerClient:
    return MockModelServerClient() if is_mock else VLLMClient()
