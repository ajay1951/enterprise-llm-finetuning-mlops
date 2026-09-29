import os
import logging
import asyncio
from typing import Dict, Any, AsyncGenerator, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import boto3
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurable Environment Variables
MODEL_NAME = os.environ.get("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")
MODEL_ARTIFACT_URI = os.environ.get("MODEL_ARTIFACT_URI", "")
CPU_MODE = os.environ.get("CPU_MODE", "true").lower() == "true"
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")

engine = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    # 1. Download Model from S3 if configured
    if MODEL_ARTIFACT_URI.startswith("s3://"):
        logger.info(f"Downloading model from {MODEL_ARTIFACT_URI}...")
        # (In a real impl, we'd use boto3 to download the folder to /tmp/model)
        # For this resume project, we'll assume the local path or HF fallback.
        local_model_path = MODEL_NAME  # fallback to huggingface hub for CPU test
    else:
        local_model_path = MODEL_NAME

    # 2. Initialize vLLM Engine
    try:
        if CPU_MODE:
            logger.info(
                "Initializing vLLM in CPU Mode. This is for development/validation only."
            )
            # Note: vLLM CPU support requires a specific build, or we use a mocked/lite engine.
            # We will use the vLLM AsyncLLMEngine if installed with CPU flags,
            # otherwise we mock it gracefully for the CPU-only portfolio constraint.
            logger.warning("Mocking vLLM engine for CPU Free-Tier compatibility.")
            engine = "mock_cpu_engine"
        else:
            from vllm.engine.arg_utils import AsyncEngineArgs
            from vllm.engine.async_llm_engine import AsyncLLMEngine

            engine_args = AsyncEngineArgs(
                model=local_model_path, trust_remote_code=True
            )
            engine = AsyncLLMEngine.from_engine_args(engine_args)
            logger.info("vLLM Engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize vLLM engine: {e}")
        engine = None

    yield
    # Shutdown
    engine = None


app = FastAPI(title="ForgeLLM Inference API", lifespan=lifespan)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "vllm-inference"}


@app.get("/ready")
def readiness_check():
    if engine is None:
        raise HTTPException(status_code=503, detail="Model engine not loaded")
    return {"status": "ready"}


@app.get("/model-info")
def model_info():
    return {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "model_artifact_uri": MODEL_ARTIFACT_URI,
        "cpu_mode": CPU_MODE,
        "backend": "vllm",
    }


async def _stream_mock_response(prompt: str) -> AsyncGenerator[str, None]:
    """Mock streaming generator for CPU Free-Tier mode"""
    response_tokens = [
        "This ",
        "is ",
        "a ",
        "mocked ",
        "response ",
        "from ",
        "the ",
        "vLLM ",
        "CPU ",
        "Engine.",
    ]
    for token in response_tokens:
        yield f'data: {{"choices": [{{"delta": {{"content": "{token}"}}}}]}}\n\n'
        await asyncio.sleep(0.1)
    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if engine is None:
        raise HTTPException(status_code=503, detail="Inference engine not ready")

    if request.max_tokens > 2048:
        raise HTTPException(
            status_code=400, detail="max_tokens exceeds safe limit of 2048"
        )

    prompt = "\n".join([f"{m.role}: {m.content}" for m in request.messages])
    request_id = os.urandom(8).hex()

    if CPU_MODE:
        # Fallback for free-tier portfolio testing
        if request.stream:
            return StreamingResponse(
                _stream_mock_response(prompt), media_type="text/event-stream"
            )
        else:
            return {
                "id": f"chatcmpl-{request_id}",
                "object": "chat.completion",
                "model": MODEL_NAME,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "This is a mocked response from the vLLM CPU Engine.",
                        },
                        "finish_reason": "stop",
                    }
                ],
            }

    # Real GPU vLLM Inference
    from vllm import SamplingParams

    sampling_params = SamplingParams(
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens,
    )

    results_generator = engine.generate(prompt, sampling_params, request_id)

    if request.stream:

        async def stream_results() -> AsyncGenerator[str, None]:
            async for request_output in results_generator:
                text = request_output.outputs[0].text
                yield f'data: {{"choices": [{{"delta": {{"content": "{text}"}}}}]}}\n\n'
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_results(), media_type="text/event-stream")

    else:
        final_output = None
        async for request_output in results_generator:
            final_output = request_output

        return {
            "id": f"chatcmpl-{request_id}",
            "object": "chat.completion",
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": final_output.outputs[0].text if final_output else "",
                    },
                    "finish_reason": "stop",
                }
            ],
        }
