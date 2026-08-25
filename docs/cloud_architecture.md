# ForgeLLM Phase 7: Cloud & Distributed GPU Architecture

ForgeLLM has evolved from a single-machine local application to a robust distributed LLM control plane.

## Overview

The platform is strictly divided into two distinct logical zones:
1. **Control Plane**: Handles user interactions, scheduling, metadata persistence, and orchestration. (FastAPI + PostgreSQL + Redis + Scheduler Service)
2. **Worker Plane**: Standalone, disposable compute nodes that execute heavy ML workloads. (ForgeLLM Worker Agents running on raw EC2/RunPod/Local servers)

```text
                     ForgeLLM Dashboard
                             │
                             ▼
             ┌─────────── FastAPI ──────────┐
             │                              │
         Scheduler                     Storage Service
             │                              │
     (Best-fit VRAM)                  (S3 / MinIO)
             │                              │
       ┌─────┴─────┐                  ┌─────┴─────┐
       ▼           ▼                  ▼           ▼
  Worker 01    Worker 02        Model Artifacts Datasets
 (RTX 4090)  (A100 80GB)
```

## Security & Registration
Workers must be started with a valid `FORGELLM_WORKER_TOKEN`. When they boot up, they discover their hardware via NVML and send a registration payload to the Control Plane. They continue to send heartbeats every 15 seconds. If a worker crashes, the control plane will mark it as `OFFLINE` after 5 minutes and reclaim its allocated locks.

## Storage Abstraction
Large binary files (datasets, model adapters, checkpoints) are no longer processed synchronously via the API or stored in PostgreSQL. They are streamed into `ArtifactStorage` (backed by MinIO or AWS S3).
When a worker is assigned a job, its internal `ArtifactCacheManager` checks its local `/tmp/forgellm_cache` and pulls the required artifacts from S3. LRU eviction ensures the cache does not exceed the allowed limit (default 200GB).

## Running the Agent
```bash
pip install -r requirements.txt
export FORGELLM_API_URL=http://localhost:8000
export FORGELLM_WORKER_TOKEN=secret
python workers/forgellm_agent/agent.py
```
