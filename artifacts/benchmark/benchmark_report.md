# ForgeLLM Serving & Inference Benchmark Report

- **Timestamp:** `2026-10-05T09:36:16.765790+00:00`
- **Model:** `Qwen/Qwen2.5-0.5B`
- **Hardware:** `NVIDIA GeForce RTX 2050 (4.00 GB VRAM)`
- **CUDA Available:** `True`

## 1. Measured Performance Metrics

| Metric | Transformers (Physical GPU) | vLLM Engine | Notes |
|:---|:---:|:---:|:---|
| **Execution Mode** | `physical_gpu` | `simulated_reference` | Implementation environment |
| **Average Latency** | `6.723s` | `0.049s` | End-to-end request time |
| **p50 Latency** | `7.102s` | `0.049s` | Median request latency |
| **p95 Latency** | `8.361s` | `0.050s` | Tail latency (95th percentile) |
| **Throughput (req/s)** | `0.15` | `20.47` | Requests per second |
| **Generation Speed** | `13.36 tok/s` | `245.69 tok/s` | Token generation throughput |
| **Total Tokens** | `449` | `60` | Workload token output |

## 2. Technical Methodology & Environment Transparency

1. **Transformers Backend:** Benchmarked on local workstation with physical CUDA acceleration (`NVIDIA GeForce RTX 2050 4GB`). Demonstrates baseline HuggingFace `generate()` overhead.
2. **vLLM Serving Backend:** Production vLLM relies on Linux-native C++ PagedAttention kernels. When evaluated on Windows local development hosts without an active container, measurements represent client-side reference simulation or remote container dispatch.
3. **Production Deployment Recommendation:** Deploy `vllm/vllm-openai:latest` in Kubernetes/Docker on Linux GPU nodes (A10G/L4/H100) using ForgeLLM's `VLLMBackend(use_remote_server=True)` client connector for high-concurrency continuous batching.
