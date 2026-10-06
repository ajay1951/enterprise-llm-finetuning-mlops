---
title: ForgeLLM Public ZeroGPU Demo
emoji: ⚒️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.20.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Enterprise LLM Fine-Tuning & MLOps Platform Public Demo
---

# ⚒️ ForgeLLM — Enterprise LLM Platform Public Demo

Welcome to the live public demonstration of **ForgeLLM** deployed on **Hugging Face ZeroGPU**.

ForgeLLM is an enterprise-grade LLM fine-tuning, evaluation, regression testing, and production inference platform.

---

## 🚀 Live Demo Specifications

- **Model:** `Qwen/Qwen2.5-0.5B-Instruct`
- **Inference Runtime:** PyTorch 2.5+ / Hugging Face Transformers with dynamic `@spaces.GPU` ZeroGPU transient leasing
- **Prompt Format:** ChatML (`<|im_start|>user ... <|im_end|>`)
- **Live Observability & Telemetry:**
  - **Time to First Token (TTFT)** in seconds (`s`)
  - **Total Generation Latency** in seconds (`s`)
  - **Output Token Count**
  - **Real-Time Throughput** in tokens per second (`tok/s`)
  - **Live Generation State** (`🟢 Ready`, `⚡ Generating...`, `✓ Complete`, `❌ Error`)
  - **Runtime Specifications** (Model, Engine, Device Precision)
- **Features:** Real-time token streaming, parameter controls (temperature, max tokens, nucleus sampling), and dedicated inference observability metrics.

---

## 🏗️ ForgeLLM Platform Architecture

- **Fine-Tuning:** PEFT / QLoRA 4-bit / LoRA Supervised Fine-Tuning (SFT)
- **Evaluation Engine:** Deterministic objective metrics (Pure-Python LCS ROUGE-L, Exact Match, Token Similarity) + optional LLM-as-a-Judge
- **Regression Quality Gates:** Automated pre-deployment quality validation blocking performance degradation
- **Production Serving Backend:** vLLM with PagedAttention and continuous batching on Linux GPU nodes
- **Source Code & Documentation:** [GitHub: ajay1951/enterprise-llm-finetuning-mlops](https://github.com/ajay1951/enterprise-llm-finetuning-mlops)

---

## 🛠️ Programmatic API Access

You can query this space programmatically using the Gradio Python Client:

```python
from gradio_client import Client

client = Client("ajay1951/forgellm-demo")
result = client.predict(
    message="What is LoRA parameter-efficient fine-tuning?", api_name="/predict"
)
print(result)
```
