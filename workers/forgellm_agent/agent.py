import os
import time
import socket
import json
import uuid
import asyncio
import httpx
import psutil
from typing import Dict, Any, List

from workers.forgellm_agent.cache_manager import ArtifactCacheManager

try:
    import pynvml

    HAS_NVML = True
except ImportError:
    HAS_NVML = False


class ForgeLLMWorkerAgent:
    def __init__(self):
        self.api_url = os.environ.get("FORGELLM_API_URL", "http://localhost:8000")
        self.worker_id = os.environ.get(
            "FORGELLM_WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}"
        )
        self.token = os.environ.get(
            "FORGELLM_WORKER_TOKEN", "default-insecure-worker-token"
        )
        self.worker_type = os.environ.get("FORGELLM_WORKER_TYPE", "hybrid")
        self.active_jobs = []
        self.gpus = []
        self.cache = ArtifactCacheManager()

        self.has_nvml = HAS_NVML
        if self.has_nvml:
            try:
                pynvml.nvmlInit()
            except Exception as e:
                print(f"Warning: NVML init failed: {e}")
                self.has_nvml = False
        else:
            self.has_nvml = False

    def get_gpu_info(self) -> List[Dict[str, Any]]:
        gpus = []
        if getattr(self, "has_nvml", False):
            try:
                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    util_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    uuid_str = (
                        pynvml.nvmlDeviceGetUUID(handle).decode("utf-8")
                        if isinstance(pynvml.nvmlDeviceGetUUID(handle), bytes)
                        else pynvml.nvmlDeviceGetUUID(handle)
                    )
                    name = (
                        pynvml.nvmlDeviceGetName(handle).decode("utf-8")
                        if isinstance(pynvml.nvmlDeviceGetName(handle), bytes)
                        else pynvml.nvmlDeviceGetName(handle)
                    )

                    try:
                        temp = pynvml.nvmlDeviceGetTemperature(
                            handle, pynvml.NVML_TEMPERATURE_GPU
                        )
                    except:
                        temp = 0.0

                    try:
                        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                    except:
                        power = 0.0

                    gpus.append(
                        {
                            "gpu_index": i,
                            "uuid": uuid_str,
                            "name": name,
                            "memory_total": mem_info.total / (1024 * 1024),
                            "memory_used": mem_info.used / (1024 * 1024),
                            "utilization": float(util_info.gpu),
                            "temperature": float(temp),
                            "power": float(power),
                            "status": "AVAILABLE",
                            "current_job_id": None,
                        }
                    )
            except Exception as e:
                print(f"Error getting GPU info: {e}")
        return gpus

    async def register(self):
        self.gpus = self.get_gpu_info()
        payload = {
            "worker_id": self.worker_id,
            "hostname": socket.gethostname(),
            "worker_type": self.worker_type,
            "cpu_count": psutil.cpu_count(),
            "ram_total": psutil.virtual_memory().total / (1024**3),
            "gpu_count": len(self.gpus),
            "gpus": self.gpus,
            "software_version": "0.1.0",
        }

        async with httpx.AsyncClient() as client:
            print(f"Registering worker {self.worker_id} with {self.api_url}...")
            resp = await client.post(
                f"{self.api_url}/api/v1/workers/register",
                json=payload,
                headers={"x-worker-token": self.token},
                timeout=10.0,
            )
            resp.raise_for_status()
            print("Successfully registered.")

    async def heartbeat(self):
        payload = {
            "status": "ONLINE",
            "ram_available": psutil.virtual_memory().available / (1024**3),
            "gpus": self.get_gpu_info(),
            "active_jobs": self.active_jobs,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/api/v1/workers/{self.worker_id}/heartbeat",
                json=payload,
                headers={"x-worker-token": self.token},
                timeout=5.0,
            )
            resp.raise_for_status()

    async def fetch_and_execute_jobs(self):
        # In a real implementation, the agent might connect to a Redis queue or use HTTP long-polling
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.api_url}/api/v1/workers/{self.worker_id}/jobs",
                    headers={"x-worker-token": self.token},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    jobs = resp.json()
                    for job in jobs:
                        print(f"Received new job: {job['id']} of type {job['type']}")
                        self.active_jobs.append(job["id"])

                        # Use Cache Manager to pull model/dataset
                        if "dataset_uri" in job:
                            await self.cache.get_artifact(job["dataset_uri"])

                        # Mock Execution
                        print(f"Executing job {job['id']}...")
                        await asyncio.sleep(2)  # Mock execution time

                        # Mock Complete
                        await client.post(
                            f"{self.api_url}/api/v1/jobs/{job['id']}/status",
                            json={"status": "COMPLETED"},
                            headers={"x-worker-token": self.token},
                        )
                        self.active_jobs.remove(job["id"])

            except Exception as e:
                pass  # Ignoring errors for mock polling

    async def run_loop(self):
        await self.register()

        while True:
            try:
                await self.heartbeat()
                await self.fetch_and_execute_jobs()
            except Exception as e:
                print(f"Loop error: {e}. Retrying in 15s...")

            await asyncio.sleep(15)


def main():
    agent = ForgeLLMWorkerAgent()
    try:
        asyncio.run(agent.run_loop())
    except KeyboardInterrupt:
        print("Worker shutting down.")


if __name__ == "__main__":
    main()
