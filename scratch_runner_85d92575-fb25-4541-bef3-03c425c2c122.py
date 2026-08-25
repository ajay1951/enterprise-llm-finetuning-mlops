
import asyncio
import uvicorn
from serving.forgellm_server.engine import engine
from serving.forgellm_server.main import app

async def init():
    print("Initializing model...")
    success = await engine.initialize(
        backend_type="transformers",
        base_model="Qwen/Qwen2.5-0.5B",
        adapter_path="",
        device="cuda",
        config={}
    )
    if not success:
        raise RuntimeError("Failed to load model")

@app.on_event("startup")
async def startup_event():
    await init()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=59264, log_level="info")
