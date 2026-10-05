import logging
import asyncio
from typing import Dict, Any, AsyncGenerator, List
from .backends.base import ModelServingBackend
from .backends.transformers_backend import TransformersBackend
from .backends.vllm_backend import VLLMBackend

logger = logging.getLogger(__name__)


class InferenceEngine:
    def __init__(self):
        self.backend: ModelServingBackend = None
        self.is_ready = False
        self.config = {}
        # Concurrency control
        self.semaphore = asyncio.Semaphore(1)  # Limit concurrent generations
        self.queue_size = 0
        self.max_queue = 5

    async def initialize(
        self,
        backend_type: str,
        base_model: str,
        adapter_path: str = None,
        device: str = "cuda",
        config: dict = None,
    ):
        self.config = config or {}
        max_concurrent = self.config.get("max_concurrent_requests", 1)
        self.semaphore = asyncio.Semaphore(max_concurrent)

        if backend_type == "transformers":
            self.backend = TransformersBackend()
        elif backend_type == "vllm":
            self.backend = VLLMBackend()
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

        success = await self.backend.load_model(
            base_model, adapter_path, device, self.config
        )
        self.is_ready = success
        return success

    async def shutdown(self):
        if self.backend:
            await self.backend.unload_model()
            self.backend = None
        self.is_ready = False

    async def generate_stream(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        if not self.is_ready:
            raise RuntimeError("Model is not ready.")

        if self.queue_size >= self.max_queue:
            raise RuntimeError("Inference queue is full.")

        self.queue_size += 1
        try:
            async with self.semaphore:
                # Merge kwargs with default config
                gen_kwargs = {**self.config, **kwargs}
                async for token in self.backend.generate_stream(messages, **gen_kwargs):
                    yield token
        finally:
            self.queue_size -= 1

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.is_ready:
            raise RuntimeError("Model is not ready.")

        if self.queue_size >= self.max_queue:
            raise RuntimeError("Inference queue is full.")

        self.queue_size += 1
        try:
            async with self.semaphore:
                gen_kwargs = {**self.config, **kwargs}
                return await self.backend.generate(messages, **gen_kwargs)
        finally:
            self.queue_size -= 1


engine = InferenceEngine()
