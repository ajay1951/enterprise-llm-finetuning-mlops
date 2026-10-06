# ForgeLLM Hugging Face ZeroGPU Deployment Guide

This guide describes how to deploy and synchronize the live public demonstration of **ForgeLLM** to **Hugging Face Spaces** utilizing free **ZeroGPU** dynamic allocation.

---

## 1. Overview & Architecture

ForgeLLM provides a lightweight, self-contained Gradio 5.x application in `deployments/huggingface_zerogpu/` that interfaces directly with Hugging Face ZeroGPU infrastructure.

```text
Public User / Client
        │
        ▼ (Web / REST API)
┌────────────────────────────────────────────────────────────────────────┐
│     Gradio 5.x Interface (deployments/huggingface_zerogpu)             │
│  ┌───────────────────────────────┬──────────────────────────────────┐  │
│  │   Chatbot & Prompt Controls   │    Live Inference Telemetry      │  │
│  │   - Multi-turn conversation   │    - TTFT (s) & Latency (s)      │  │
│  │   - Sampling parameters       │    - Output Tokens & tok/s       │  │
│  └───────────────────────────────┴──────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      ZeroGPUInferenceEngine                            │
│    - @spaces.GPU transient leasing                                     │
│    - ChatML prompt template builder                                    │
│    - TextIteratorStreamer token generation                             │
│    - Dynamic latency, TTFT, and throughput computation                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Hugging Face ZeroGPU Infrastructure                    │
│    - Dynamic NVIDIA A100/H100/L4 GPU                                   │
│    - Qwen/Qwen2.5-0.5B-Instruct Model in bfloat16                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

1. A free account on [Hugging Face](https://huggingface.co).
2. A Hugging Face User Access Token (with `write` permission).
3. Git configured locally.

---

## 3. Creating the Hugging Face Space

1. Navigate to [Hugging Face Spaces New](https://huggingface.co/new-space).
2. Set Space Name: `forgellm-demo` (or desired name).
3. Select License: `Apache 2.0` (or `MIT`).
4. Select Space SDK: **Gradio**.
5. Select Space Hardware: **ZeroGPU (Free)**.
6. Click **Create Space**.

---

## 4. Deploying via Git Subtree Push

To deploy the self-contained `deployments/huggingface_zerogpu/` directory directly to your Hugging Face Space repository:

```bash
# Add Hugging Face Space remote
git remote add hf-space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/forgellm-demo

# Push the isolated ZeroGPU directory as the root of the Space
git subtree push --prefix deployments/huggingface_zerogpu hf-space main
```

*(If force pushing or updating an existing space):*
```bash
git push hf-space `git subtree split --prefix deployments/huggingface_zerogpu main`:main --force
```

---

## 5. Automated CI/CD Sync (Optional GitHub Action)

To keep your Hugging Face Space automatically in sync with the `main` branch of this repository, create `.github/workflows/sync_hf_space.yml`:

```yaml
name: Sync to Hugging Face Space

on:
  push:
    branches: [main]
    paths:
      - 'deployments/huggingface_zerogpu/**'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Push to Hugging Face
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          git remote add hf https://${{ secrets.HF_USERNAME }}:${{ secrets.HF_TOKEN }}@huggingface.co/spaces/${{ secrets.HF_USERNAME }}/forgellm-demo
          git subtree push --prefix deployments/huggingface_zerogpu hf main
```

---

## 6. Programmatic Consumption via Python Client

Clients can consume the public ZeroGPU demo programmatically using `gradio_client`:

```python
from gradio_client import Client

client = Client("<YOUR_HF_USERNAME>/forgellm-demo")
result = client.predict(
    message="Explain how LoRA fine-tuning works in ForgeLLM.",
    system_prompt="You are a helpful AI assistant.",
    temperature=0.7,
    max_tokens=256,
    top_p=0.9,
    api_name="/chat_response"
)
print(result)
```

---

## 7. Local Testing & Validation

You can run the ZeroGPU demo locally on your workstation prior to pushing:

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the Gradio app locally
python deployments/huggingface_zerogpu/app.py
```
Open `http://localhost:7860` in your browser.
