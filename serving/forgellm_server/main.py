from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
import json
import asyncio
import logging

from .engine import engine
from .schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    CompletionRequest,
)

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ForgeLLM Internal Model Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/ready")
def readiness_check():
    if engine.is_ready:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Model not loaded or warming up")


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    if not engine.is_ready:
        raise HTTPException(status_code=503, detail="Model is not ready")

    messages_dict = [{"role": m.role, "content": m.content} for m in req.messages]

    if req.stream:

        async def event_generator():
            request_id = f"chatcmpl-{uuid.uuid4().hex}"
            created_time = int(time.time())

            try:
                async for token in engine.generate_stream(
                    messages=messages_dict,
                    temperature=req.temperature,
                    top_p=req.top_p,
                    max_tokens=req.max_tokens,
                ):
                    if await request.is_disconnected():
                        logger.warning("Client disconnected during stream")
                        break

                    chunk = {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": req.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": token},
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"

                # Final chunk
                final_chunk = {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            except ValueError as e:  # Context length error etc
                error_chunk = {"error": str(e)}
                yield f"data: {json.dumps(error_chunk)}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_chunk = {"error": "Internal server error during generation"}
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    else:
        try:
            response_text = await engine.generate(
                messages=messages_dict,
                temperature=req.temperature,
                top_p=req.top_p,
                max_tokens=req.max_tokens,
            )

            return ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex}",
                created=int(time.time()),
                model=req.model,
                choices=[
                    ChatCompletionResponseChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=response_text),
                        finish_reason="stop",
                    )
                ],
                usage={
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },  # Usage counting could be added to backend
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.post("/v1/completions")
async def completions(req: CompletionRequest, request: Request):
    # Map completion to chat completion for models using chat templates
    messages = [{"role": "user", "content": req.prompt}]
    chat_req = ChatCompletionRequest(
        model=req.model,
        messages=[ChatMessage(**m) for m in messages],
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
        stream=req.stream,
    )
    return await chat_completions(chat_req, request)
