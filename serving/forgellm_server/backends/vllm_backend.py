import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List

import httpx

from .base import ModelServingBackend

logger = logging.getLogger(__name__)


class VLLMBackend(ModelServingBackend):
    """vLLM Model Serving Backend supporting both in-process AsyncLLMEngine

    and remote Dockerized OpenAI-compatible vLLM endpoints.
    """

    def __init__(self):
        self.model_name: str = ""
        self.adapter_path: str | None = None
        self.device: str = "cuda"
        self.config: dict[str, Any] = {}
        self.client: httpx.AsyncClient | None = None
        self.endpoint_url: str = "http://localhost:8000/v1"
        self.engine: Any = None
        self.use_remote_server: bool = True
        self.is_loaded: bool = False

    async def load_model(
        self,
        base_model: str,
        adapter_path: str = None,
        device: str = "cuda",
        config: dict = None,
    ) -> bool:
        """Initialize vLLM engine or establish connection to vLLM server."""
        try:
            self.model_name = base_model
            self.adapter_path = adapter_path
            self.device = device
            self.config = config or {}
            self.endpoint_url = self.config.get(
                "vllm_endpoint", "http://localhost:8000/v1"
            )

            # Check if in-process vLLM is requested and available
            in_process = self.config.get("in_process", False)
            if in_process:
                try:
                    from vllm.engine.arg_utils import AsyncEngineArgs
                    from vllm.engine.async_llm_engine import AsyncLLMEngine

                    engine_args = AsyncEngineArgs(
                        model=base_model,
                        gpu_memory_utilization=self.config.get(
                            "gpu_memory_utilization", 0.9
                        ),
                        max_model_len=self.config.get("max_model_len", 2048),
                        tensor_parallel_size=self.config.get(
                            "tensor_parallel_size", 1
                        ),
                        dtype=self.config.get("dtype", "auto"),
                        trust_remote_code=True,
                    )
                    self.engine = AsyncLLMEngine.from_engine_args(engine_args)
                    self.use_remote_server = False
                    logger.info("Initialized in-process vLLM AsyncLLMEngine.")
                except ImportError:
                    logger.info(
                        "vLLM library not natively installed in host environment. Operating in client/server mode."
                    )
                    self.use_remote_server = True
            else:
                self.use_remote_server = True

            timeout = httpx.Timeout(
                self.config.get("request_timeout", 30.0), connect=5.0
            )
            self.client = httpx.AsyncClient(timeout=timeout)
            self.is_loaded = True
            logger.info(
                f"vLLM backend loaded for model {base_model} (mode: {'remote' if self.use_remote_server else 'in-process'})."
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load vLLM backend: {e}")
            self.is_loaded = False
            return False

    async def unload_model(self):
        """Free resources and close HTTP connections."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.engine = None
        self.is_loaded = False
        logger.info("vLLM backend unloaded.")

    async def generate_stream(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate text token-by-token using vLLM streaming."""
        if not self.is_loaded:
            raise RuntimeError("vLLM backend is not loaded.")

        temperature = kwargs.get("temperature", 0.0)
        max_tokens = kwargs.get("max_tokens", 256)
        top_p = kwargs.get("top_p", 1.0)

        if self.use_remote_server:
            if not self.client:
                raise RuntimeError("vLLM HTTP client is not initialized.")

            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "stream": True,
            }

            try:
                async with self.client.stream(
                    "POST", f"{self.endpoint_url}/chat/completions", json=payload
                ) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        raise RuntimeError(
                            f"vLLM server returned error {response.status_code}: {err_text.decode('utf-8', errors='ignore')}"
                        )

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                yield token
                        except Exception:
                            continue
            except httpx.RequestError as e:
                raise RuntimeError(
                    f"vLLM server connection error at {self.endpoint_url}: {e}"
                ) from e
        else:
            # In-process engine streaming
            from vllm import SamplingParams

            sampling_params = SamplingParams(
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )
            # Format prompt
            prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
            request_id = f"req-{asyncio.get_event_loop().time()}"
            results_generator = self.engine.generate(
                prompt, sampling_params, request_id
            )

            previous_text = ""
            async for request_output in results_generator:
                text = request_output.outputs[0].text
                new_token = text[len(previous_text) :]
                previous_text = text
                if new_token:
                    yield new_token

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate complete response in one call."""
        tokens = []
        async for token in self.generate_stream(messages, **kwargs):
            tokens.append(token)
        return "".join(tokens)
