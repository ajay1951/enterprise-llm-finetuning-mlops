from workers.forgellm_worker.celery_app import celery_app
from backend.forgellm_api.db.session import SessionLocal
from backend.forgellm_api.db.models.deployment import Deployment
from backend.forgellm_api.db.models.model import ModelVersion
from backend.forgellm_api.services.deployment_service import DeploymentService
from backend.forgellm_api.core.config import get_settings
import logging
import time
import subprocess
import socket
import os
import redis
import json
import asyncio
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)
settings = get_settings()

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

@celery_app.task(bind=True, name="run_deployment_server")
def run_deployment_server(self, deployment_id: str):
    logger.info(f"Starting deployment worker for {deployment_id}")
    
    db = SessionLocal()
    service = DeploymentService(db)
    
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment or deployment.status == "cancelled":
            return False
            
        deployment.status = "starting"
        db.commit()
        service.log_event(deployment_id, "deployment.starting", {"message": "Acquired worker. Starting server..."})

        # Fetch model version metadata
        model_version = db.query(ModelVersion).filter(ModelVersion.id == deployment.model_version_id).first()
        if not model_version:
            raise ValueError("Model version not found.")

        # Find available port
        port = get_free_port()
        deployment.port = port
        deployment.endpoint = f"http://localhost:{port}"
        db.commit()

        # Start the internal FastAPI server as a subprocess
        env = os.environ.copy()
        
        # Configure the server using ENV vars which we can read inside main.py / engine.py if needed, 
        # but for now we'll write a small startup script or rely on the server pulling from DB/Args
        
        # We will write a tiny runner script that injects the config and runs uvicorn
        runner_code = f"""
import asyncio
import uvicorn
from serving.forgellm_server.engine import engine
from serving.forgellm_server.main import app

async def init():
    print("Initializing model...")
    success = await engine.initialize(
        backend_type="{deployment.serving_backend}",
        base_model="{model_version.base_model}",
        adapter_path="{model_version.adapter_path}",
        device="{deployment.device}",
        config={deployment.configuration or {}}
    )
    if not success:
        raise RuntimeError("Failed to load model")

@app.on_event("startup")
async def startup_event():
    await init()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port={port}, log_level="info")
"""
        runner_path = f"scratch_runner_{deployment_id}.py"
        with open(runner_path, "w") as f:
            f.write(runner_code)

        deployment.status = "loading"
        db.commit()
        service.log_event(deployment_id, "deployment.loading", {"message": "Loading model and weights into memory."})

        import sys
        
        # Start Process using the same python interpreter (from the venv)
        process = subprocess.Popen(
            [sys.executable, runner_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )

        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"forgellm:deployment_control:{deployment_id}")
        
        # Wait for ready
        is_ready = False
        start_time = time.time()
        timeout = 900 # 15 minutes to load model (could be downloading)
        
        while time.time() - start_time < timeout:
            # Check for stop signal
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message and message['data']:
                data = json.loads(message['data'])
                if data.get("command") == "stop":
                    logger.info("Received stop signal during load")
                    process.terminate()
                    deployment.status = "stopped"
                    deployment.stopped_at = datetime.utcnow()
                    db.commit()
                    return True

            # Stream logs
            # In a real scenario we'd use select or async reading. For simplicity, we just check if it crashed.
            if process.poll() is not None:
                output = process.stdout.read()
                logger.error(f"Server process crashed. Output:\n{output}")
                raise RuntimeError(f"Server process crashed with exit code {process.returncode}\n{output[-500:]}")

            try:
                resp = httpx.get(f"http://localhost:{port}/ready", timeout=1.0)
                if resp.status_code == 200:
                    is_ready = True
                    break
            except httpx.RequestError:
                pass
                
            time.sleep(2)
            
        if not is_ready:
            process.terminate()
            output = process.stdout.read()
            logger.error(f"Model loading timed out. Output:\n{output}")
            raise RuntimeError(f"Model loading timed out after {timeout}s.\n{output[-500:]}")

        # Mark ready
        deployment.status = "ready"
        deployment.health_status = "healthy"
        deployment.started_at = datetime.utcnow()
        db.commit()
        service.log_event(deployment_id, "deployment.ready", {"message": "Deployment is ready and accepting traffic."})

        # Main health check loop
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message and message['data']:
                data = json.loads(message['data'])
                if data.get("command") == "stop":
                    logger.info("Received stop signal")
                    break

            if process.poll() is not None:
                logger.error("Model server process died unexpectedly")
                deployment.status = "failed"
                deployment.error_message = "Process died unexpectedly"
                db.commit()
                service.log_event(deployment_id, "deployment.failed", {"message": "Process died unexpectedly."})
                return False

            try:
                resp = httpx.get(f"http://localhost:{port}/health", timeout=2.0)
                if resp.status_code == 200:
                    if deployment.health_status != "healthy":
                        deployment.health_status = "healthy"
                        db.commit()
                else:
                    if deployment.health_status != "unhealthy":
                        deployment.health_status = "unhealthy"
                        db.commit()
            except Exception as e:
                if deployment.health_status != "unhealthy":
                    deployment.health_status = "unhealthy"
                    db.commit()
                    
            time.sleep(5)

        # Cleanup
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            
        if os.path.exists(runner_path):
            os.remove(runner_path)
            
        deployment.status = "stopped"
        deployment.stopped_at = datetime.utcnow()
        db.commit()
        service.log_event(deployment_id, "deployment.stopped", {"message": "Deployment stopped successfully."})
        return True

    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        if deployment:
            deployment.status = "failed"
            deployment.error_message = str(e)
            db.commit()
            service.log_event(deployment_id, "deployment.failed", {"message": str(e)})
        return False
        
    finally:
        db.close()
