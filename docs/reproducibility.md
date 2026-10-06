# ForgeLLM: Reproducibility & Environment Setup Guide

**Document Version:** `1.0.0`  
**Target Audience:** ML Engineers, Platform Engineers, Reviewers, Evaluators  

This document provides explicit, deterministic instructions for reproducing the environment, tests, fine-tuning, evaluation, benchmarks, and ZeroGPU deployments of ForgeLLM.

---

## 1. System Requirements & Hardware Specifications

| Component | Minimum Requirement | Recommended Specification |
| :--- | :--- | :--- |
| **Operating System** | Linux (Ubuntu 22.04 LTS), macOS, Windows 11 | Ubuntu 22.04 LTS or Windows 11 WSL2 |
| **Python Version** | Python `3.11` or `3.12` | Python `3.12` |
| **GPU / VRAM** | 4.0 GB VRAM (CUDA 12.1+) or CPU | 8.0+ GB VRAM (NVIDIA RTX / A10G / L4) |
| **RAM** | 16 GB System Memory | 32 GB System Memory |
| **Disk Space** | 10 GB Free Storage | 25 GB SSD Storage |

---

## 2. Environment Setup & Dependency Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/ajay1951/enterprise-llm-finetuning-mlops.git
cd enterprise-llm-finetuning-mlops
```

### Step 2: Create Isolated Virtual Environment
```bash
# Using standard venv
python -m venv .venv

# Activate on Linux / macOS:
source .venv/bin/activate

# Activate on Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies & Editable Package
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

---

## 3. Automated Verification & Test Execution

Run the complete test suite and code quality linters:

```bash
# 1. Run all repository unit and integration tests (172 tests)
pytest tests/ -v

# 2. Run dedicated ZeroGPU adapter tests (18 tests)
pytest tests/test_zerogpu_adapter.py -v

# 3. Code formatting check (Ruff)
ruff format --check src/ tests/ deployments/

# 4. Code linting (Ruff)
ruff check src/ tests/ deployments/
```

Expected output:
```text
172 passed
18 passed
All checks passed!
```

---

## 4. Reproducing Parameter-Efficient Fine-Tuning (PEFT)

### Local Micro-Fine-Tuning Experiment
To execute a reproducible micro fine-tuning run on a local GPU (e.g. RTX 2050 4GB or higher) with PEFT LoRA and MLflow tracking:

```bash
# Run training via Forge CLI
forge train \
  --model "Qwen/Qwen2.5-0.5B" \
  --data "data/raw/train.jsonl" \
  --epochs 1 \
  --batch-size 1 \
  --grad-accum 4 \
  --lr 0.0002 \
  --output-dir "outputs/repro_experiment"
```

The output adapter weights are stored in `outputs/repro_experiment/adapter` and experiment metrics are automatically logged to MLflow (`http://localhost:5000`).

---

## 5. Reproducing Evaluation & Regression Gates

Run the deterministic objective evaluator and quality gate against base and fine-tuned checkpoints:

```bash
# Run deterministic regression evaluation
forge evaluate \
  --base-model "Qwen/Qwen2.5-0.5B" \
  --adapter-path "outputs/repro_experiment/adapter" \
  --eval-dataset "tests/fixtures/sample_dataset.jsonl" \
  --output "artifacts/evaluation/regression_report.json"
```

### Quality Gate Metrics Evaluated:
- **Exact Match (EM):** Case-insensitive string match
- **ROUGE-L:** Pure-Python Longest Common Subsequence (LCS) F1 score
- **Semantic Token Similarity:** Token-set Jaccard overlap
- **Composite Quality Score:** Weighted metric combination ($0.4 \cdot \text{ROUGE} + 0.4 \cdot \text{Sim} + 0.2 \cdot \text{EM}$)

---

## 6. Reproducing High-Throughput Inference Benchmarks

Execute the comparative latency and throughput benchmark suite:

```bash
# Run inference benchmark across batch sizes and backends
python benchmarks/inference/benchmark_serving.py \
  --model "Qwen/Qwen2.5-0.5B" \
  --backend transformers \
  --output "artifacts/benchmarks/serving_benchmark.json"
```

---

## 7. ZeroGPU Deployment & Live Telemetry Reproduction

The Hugging Face ZeroGPU deployment operates without local GPU requirement by leveraging Hugging Face's transient GPU leasing infrastructure.

### Local Testing of ZeroGPU UI (CPU Fallback Mode)
```bash
# Launch Gradio interface locally
python deployments/huggingface_zerogpu/app.py
```
Open `http://localhost:7860` in any web browser.

### Remote ZeroGPU Deployment
Deploy the verified subtree branch directly to your Hugging Face Space:
```bash
git subtree split --prefix deployments/huggingface_zerogpu main
git push hf-space <split-commit-sha>:main --force
```

---

## 8. Configuration & Environment Variables

All configuration is managed through environment variables with safe fallbacks:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./forgellm.db` | PostgreSQL or SQLite database URI |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker URI for Celery workers |
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow experiment tracking server |
| `FORGELLM_MODEL_CACHE` | `~/.cache/forgellm` | Directory for local model checkpoints |
| `HF_TOKEN` | *None* | Optional Hugging Face token for Hub access |

> **Security Note:** Never commit `.env` files or API credentials to version control. ForgeLLM uses `.env.example` as a template.
