from fastapi import FastAPI
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.forgellm_api.api.v1 import (
    health, projects, datasets, training, ws, workers, deployments, 
    inference, storage, workloads, auth, organizations, api_keys, 
    audit_logs, gateway, experiments, models_lifecycle, benchmarks
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.forgellm_api.services.health_service import monitor_workers_health
from backend.forgellm_api.services.reconciliation_controller import run_reconciliation_loop
from backend.forgellm_api.services.autoscaling_controller import run_autoscaling_loop

async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(monitor_workers_health())
    recon_task = asyncio.create_task(run_reconciliation_loop())
    auto_task = asyncio.create_task(run_autoscaling_loop())
    yield
    # Shutdown
    task.cancel()
    recon_task.cancel()
    auto_task.cancel()

app = FastAPI(
    title="ForgeLLM API",
    description="Backend API for ForgeLLM ML Platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
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
app.include_router(inference.router) # No /api/v1 prefix so it matches /v1/chat/completions directly!
app.include_router(gateway.router)
app.include_router(experiments.router)
app.include_router(models_lifecycle.router)
app.include_router(benchmarks.router)
