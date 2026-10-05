# ForgeLLM vLLM Production Serving Deployment

This directory contains containerized deployment assets for high-throughput inference using **vLLM** and **PagedAttention**.

---

## 1. Prerequisites
- Docker Engine with NVIDIA Container Toolkit (`nvidia-container-runtime`).
- NVIDIA GPU with minimum 4GB VRAM (e.g., RTX 2050/3060/4090, A100/H100).
- Hugging Face Access Token (optional for private/gated weights).

---

## 2. Quick Start

### Build and Launch via Docker Compose
```bash
docker compose -f deployment/vllm/docker-compose.yml up -d
```

### Check Health and Readiness
```bash
curl http://localhost:8000/health
```

### Test OpenAI-Compatible Chat Completion
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B",
    "messages": [{"role": "user", "content": "What is ForgeLLM?"}],
    "temperature": 0.0,
    "max_tokens": 128
  }'
```

---

## 3. Configuration Parameters
Edit `deployment/vllm/config.yaml`:
- `gpu_memory_utilization`: Proportion of GPU memory allocated to KV cache (default `0.90`).
- `max_model_len`: Maximum context window length in tokens (default `2048`).
- `tensor_parallel_size`: Number of GPUs for distributed tensor parallelism (default `1`).
