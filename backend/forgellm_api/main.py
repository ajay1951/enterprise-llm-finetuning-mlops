import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from backend.forgellm_api.api.v1 import (
    api_keys,
    audit_logs,
    auth,
    benchmarks,
    datasets,
    deployments,
    experiments,
    gateway,
    health,
    inference,
    models_lifecycle,
    organizations,
    projects,
    storage,
    telemetry,
    training,
    workers,
    workloads,
    ws,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.forgellm_api.services.autoscaling_controller import run_autoscaling_loop
from backend.forgellm_api.services.health_service import monitor_workers_health
from backend.forgellm_api.services.reconciliation_controller import (
    run_reconciliation_loop,
)


async def lifespan(app: FastAPI):
    # Startup
    import os

    env = os.getenv("ENVIRONMENT", getattr(settings, "ENVIRONMENT", "development"))
    if env != "test":
        tasks.append(asyncio.create_task(monitor_workers_health()))
        tasks.append(asyncio.create_task(run_reconciliation_loop()))
        tasks.append(asyncio.create_task(run_autoscaling_loop()))
    yield
    # Shutdown
    for t in tasks:
        t.cancel()


app = FastAPI(
    title="ForgeLLM API",
    description="Backend API for ForgeLLM ML Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

from backend.forgellm_api.core.config import get_settings

settings = get_settings()

# CORS Configuration
allow_origins = (
    settings.CORS_ORIGINS if settings.ENVIRONMENT != "development" else ["*"]
)
allow_credentials = False if allow_origins == ["*"] else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root Health probe for Docker/Kubernetes
@app.get("/health", tags=["Health"])
def root_health():
    return {"status": "ok", "service": "ForgeLLM API"}


# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(
    organizations.router, prefix="/api/v1/organizations", tags=["organizations"]
)
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["api_keys"])
app.include_router(audit_logs.router, prefix="/api/v1/audit-logs", tags=["audit_logs"])
app.include_router(health.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1")
app.include_router(workers.router, prefix="/api/v1")
app.include_router(deployments.router, prefix="/api/v1")
app.include_router(storage.router, prefix="/api/v1")
app.include_router(workloads.router, prefix="/api/v1")
app.include_router(
    inference.router
)  # No /api/v1 prefix so it matches /v1/chat/completions directly!
app.include_router(gateway.router)
app.include_router(experiments.router)
app.include_router(models_lifecycle.router)
app.include_router(benchmarks.router)
app.include_router(telemetry.router)
