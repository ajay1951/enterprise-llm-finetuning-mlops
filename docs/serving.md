# ForgeLLM Model Serving & Inference

ForgeLLM provides a robust serving architecture designed to run alongside your training clusters. 

## Architecture

```text
                       Model Registry
                             │
                             ▼
                      Deployment Service
                             │
                             ▼
                       Model Server (Internal)
                             │
                   ┌─────────┴─────────┐
                   ▼                   ▼
               REST API           Streaming API
                   │                   │
                   └─────────┬─────────┘
                             ▼
                        API Gateway (/v1/chat/completions)
```

The system ensures that **Training** and **Inference** are strictly separated. 
- `celery_app` (worker) acts as the deployment manager.
- Upon receiving a deploy task, the worker spawns an internal, high-performance `forgellm_server` (FastAPI) on a dedicated port.
- This isolates the GPU memory from the main Celery process.
- The `forgellm_api` backend acts as an Inference Gateway, proxying client traffic to the appropriate internal server using Server-Sent Events (SSE) for streaming.

## Deploying Models

1. Navigate to **Projects -> Models** in the dashboard.
2. Select your registered model.
3. Click **Deploy Model**.
4. Configure hardware (CPU/CUDA), Max Context, and Serving Backend (Transformers).
5. The deployment will enter the `queued` state, then `starting`, `loading`, and finally `ready`.

## Using the OpenAI-Compatible API

Once your deployment is `ready`, you can interact with it using standard OpenAI clients.

### cURL

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-deployment-name",
    "messages": [
      {
        "role": "user",
        "content": "Explain quantum computing."
      }
    ],
    "stream": true,
    "temperature": 0.7
  }'
```

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed-yet" 
)

response = client.chat.completions.create(
    model="your-deployment-name",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="")
```

## GPU Requirements

Deployments requiring `cuda` will fail if no compatible NVIDIA GPU is found. The internal model server validates memory and CUDA extensions on startup. If you only have a CPU, select `cpu` during deployment.
