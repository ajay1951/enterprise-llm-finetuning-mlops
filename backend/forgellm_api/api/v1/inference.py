import time
import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.core.security import get_api_key_context
from backend.forgellm_api.core.rate_limit import RateLimiter
from backend.forgellm_api.core.gateway.router import resolve_model_version, get_healthy_deployments, select_replica, get_fallback_version
from backend.forgellm_api.core.gateway.adapters import get_model_client
from backend.forgellm_api.core.gateway.retry import with_retry_and_fallback
from backend.forgellm_api.core.gateway.metrics import MetricsBuffer

# In a real app we'd inject a configured Redis client, using None for local fallback
import redis
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=1)
    redis_client.ping()
except Exception:
    redis_client = None

logger = logging.getLogger(__name__)
metrics_buffer = MetricsBuffer(redis_client)
router = APIRouter(tags=["AI Gateway"])
rate_limiter = RateLimiter(requests=100, window=60)

@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    db: Session = Depends(get_db),
    api_key_ctx: dict = Depends(get_api_key_context),
    # _rate_limit = Depends(rate_limiter) # Apply API key based rate limiting in middleware/dependency
):
    # Enforce API Key auth and permissions
    if not api_key_ctx or "models:inference" not in api_key_ctx.get("permissions", []):
        raise HTTPException(status_code=403, detail="Forbidden: Missing 'models:inference' permission")
        
    org_id = api_key_ctx.get("organization_id")
    project_id = api_key_ctx.get("project_id")

    # Generate request trace ID
    request_id = f"req_{uuid.uuid4().hex}"
    
    body = await request.json()
    requested_model = body.get("model")
    stream = body.get("stream", False)
    
    if not requested_model:
        raise HTTPException(status_code=400, detail="INVALID_REQUEST: Missing 'model' in request body")

    # 1. Model Resolution & A/B Testing
    try:
        primary_version_id = resolve_model_version(db, project_id, requested_model)
    except HTTPException as e:
        logger.warning(f"[{request_id}] Model resolution failed: {e.detail}")
        raise

    fallback_version_id = get_fallback_version(db, project_id, requested_model)

    async def execute_inference(version_id: str):
        # 2. Replica Selection (LEAST_LOADED)
        deployments = get_healthy_deployments(db, version_id)
        if not deployments:
            raise HTTPException(status_code=503, detail="MODEL_UNAVAILABLE: No healthy replicas available")
            
        replica = select_replica(deployments, strategy="LEAST_LOADED", redis_client=redis_client)
        # Assuming replica.endpoint points to the vLLM container, e.g. "http://vllm_service:8080"
        # For local testing, we fallback to our dedicated inference service port
        endpoint = replica.endpoint or "http://vllm_service:8080"
        
        # 3. Inference execution
        start_time = time.time()
        metrics_buffer.record_request_start(replica.id)
        
        import httpx
        
        try:
            headers = {"X-Request-Id": request_id}
            
            async with httpx.AsyncClient() as client:
                req_kwargs = {
                    "method": "POST",
                    "url": f"{endpoint}/v1/chat/completions",
                    "json": body,
                    "headers": headers,
                    "timeout": 30.0
                }
                
                if stream:
                    # Return an async generator that yields chunks from the httpx stream
                    async def stream_generator():
                        async with client.stream(**req_kwargs) as response:
                            if response.status_code != 200:
                                yield f"data: {{\"error\": \"Inference failed with status {response.status_code}\"}}\n\n"
                                return
                            async for chunk in response.aiter_text():
                                yield chunk
                                
                    return stream_generator(), replica
                else:
                    response = await client.request(**req_kwargs)
                    response.raise_for_status()
                    return response.json(), replica
                    
        except httpx.RequestError as exc:
            logger.error(f"[{request_id}] Request to vLLM failed: {exc}")
            raise HTTPException(status_code=502, detail="Bad Gateway: vLLM service unreachable")
        finally:
            metrics_buffer.record_request_end(replica.id)
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"[{request_id}] Inference on {replica.id} took {latency_ms}ms")

    # Define operations for retry logic
    async def primary_op():
        return await execute_inference(primary_version_id)
        
    async def fallback_op():
        if fallback_version_id:
            logger.info(f"[{request_id}] Triggering fallback to version {fallback_version_id}")
            return await execute_inference(fallback_version_id)
        raise HTTPException(status_code=503, detail="Service Unavailable: Primary failed, no fallback.")

    # 4. Execute with Retry & Fallback
    result, used_replica = await with_retry_and_fallback(primary_op, fallback_op if fallback_version_id else None)
    
    # 5. Record final metrics
    # In a real impl, we'd inspect the stream chunks or final payload to count tokens and TTFT
    # For now, just record success
    metrics_buffer.record_inference_metrics({
        "request_id": request_id,
        "model": requested_model,
        "version_id": used_replica.model_version_id,
        "deployment_id": used_replica.id,
        "project_id": project_id,
        "org_id": org_id,
        "status": "success",
    })

    if stream:
        return StreamingResponse(result, media_type="text/event-stream", headers={"X-Request-Id": request_id})
    else:
        # Inject request ID into headers (FastAPI doesn't easily let us add headers to dict returns without Response object, but this is a simplified version)
        return result

@router.get("/v1/models")
def list_models(
    db: Session = Depends(get_db),
    api_key_ctx: dict = Depends(get_api_key_context)
):
    if not api_key_ctx or "models:inference" not in api_key_ctx.get("permissions", []):
        raise HTTPException(status_code=403, detail="Forbidden: Missing 'models:inference' permission")
        
    project_id = api_key_ctx.get("project_id")
    
    from backend.forgellm_api.db.models.model import Model, ModelAlias
    models = db.query(Model).filter(Model.project_id == project_id).all()
    aliases = db.query(ModelAlias).join(Model).filter(Model.project_id == project_id).all()
    
    data = []
    for m in models:
        data.append({
            "id": m.name,
            "object": "model",
            "owned_by": "ForgeLLM"
        })
    for a in aliases:
        data.append({
            "id": a.alias,
            "object": "model",
            "owned_by": "ForgeLLM"
        })
        
    return {
        "object": "list",
        "data": data
    }

