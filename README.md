# ForgeLLM: Enterprise AI Control Plane & LLM Fine-Tuning Platform

**ForgeLLM** is an open-source, enterprise-grade control plane and infrastructure for managing the complete lifecycle of Large Language Models (LLMs). It provides a unified, secure platform for dataset preparation, distributed LoRA/QLoRA Supervised Fine-Tuning (SFT), automated model evaluation, MLflow tracking, quality gates, and model serving.

---

## 🚀 Key Features

* **Dataset Management**: Data validation, deduplication, cleaning, ChatML formatting, and versioned dataset registry.
* **Efficient Fine-Tuning**: Parameter-efficient SFT powered by `peft`, `bitsandbytes` (4-bit/8-bit QLoRA), `transformers`, and `trl` with customizable model presets.
* **MLflow Tracking & Registry**: Automated experiment logging (loss curves, hyperparameters, metrics) and lifecycle stage management (`Production` alias).
* **Automated Quality Gates**: Evaluation engine comparing fine-tuned models against base models (ROUGE, BLEU, Perplexity) with automated pass/fail CI threshold gates.
* **Forge CLI (`forge`)**: Interactive command-line interface for hardware profiling, dataset preparation, fine-tuning, evaluation, interactive chat, and registry management.
* **FastAPI Async Backend**: High-performance REST API with background task orchestration, project management, and health endpoints.
* **Next.js Web Dashboard**: High-density React dashboard designed for engineering teams to monitor experiments, training jobs, datasets, and model registries.
* **Production Readiness**: GitHub Actions CI/CD pipeline, Docker containerization, Bandit security scanning, and Pytest coverage.

---

## 🏗️ Architecture

```
                                  +-----------------------+
                                  |   Next.js Dashboard   | (Port 3000)
                                  +-----------+-----------+
                                              |
                                              v
+------------------+              +-----------+-----------+
|    Forge CLI     +------------->|   FastAPI REST API    | (Port 8000)
+--------+---------+              +-----------+-----------+
         |                                    |
         v                                    v
+--------+---------+              +-----------+-----------+
| Core SFT Engine  |              |   Celery / Task Queue |
+--------+---------+              +-----------+-----------+
         |                                    |
         +-----------------+------------------+
                           |
                           v
              +------------+------------+
              | MLflow Tracking & S3    | (Port 5000)
              | Model Registry          |
              +-------------------------+
```

---

## 🛠️ Stack & Technologies

* **Engine & ML**: Python 3.11+, PyTorch, Transformers, PEFT, BitsAndBytes, TRL, Accelerate, MLflow.
* **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic, Celery, Redis, PostgreSQL.
* **Frontend**: Next.js 14, React, Tailwind CSS, Recharts, Lucide.
* **CLI & Tooling**: Typer, Rich, Pytest, Ruff, Bandit, Docker, GitHub Actions.

---

## 📦 Quick Start Guide

### Prerequisites

* Python 3.11+
* Node.js 18+ (for Web Dashboard)
* CUDA GPU recommended (NVIDIA RTX series or higher); CPU fallback supported.

---

### 1. Installation

```powershell
# Clone the repository
git clone https://github.com/your-username/ForgeLLM.git
cd ForgeLLM

# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Linux/macOS: source venv/bin/activate

# Install package and dependencies in editable mode
pip install -e .
```

---

### 2. Local Terminal (CLI) Workflow

ForgeLLM provides a full CLI tool `forge` to execute end-to-end workflows.

#### Step 1: Start MLflow Server
Start MLflow in a dedicated terminal window:
```powershell
.\venv\Scripts\Activate.ps1
mlflow server --host 127.0.0.1 --port 5000
```

#### Step 2: Validate & Prepare Dataset
Clean, format, and register dataset in ChatML format:
```powershell
forge dataset prepare data/processed/cleaned.jsonl --name customer-support
```

#### Step 3: Run Model Fine-Tuning
Execute SFT training with model presets (`small`, `medium`, `large`):
```powershell
forge train --dataset customer-support --preset small
```
*Take note of the generated **Experiment ID** (e.g. `EXP-000011`).*

#### Step 4: Run Model Evaluation & Quality Gate
Compare fine-tuned adapter against the base model:
```powershell
forge evaluate EXP-000011
```

#### Step 5: Promote Model to Production
Promote your evaluated model to `Production` stage:
```powershell
forge model promote ForgeLLM_Qwen_Qwen2.5-0.5B 1
```

#### Step 6: Interactive Terminal Chat
Chat with your fine-tuned model directly from terminal:
```powershell
forge chat customer-support:v7
```

---

### 3. Web Dashboard & API Setup

To run the web interface and API backend, launch the following services in separate terminals:

#### Terminal 1: MLflow Tracking Server
```powershell
mlflow server --host 127.0.0.1 --port 5000
```

#### Terminal 2: FastAPI Backend API
```powershell
uvicorn backend.forgellm_api.main:app --reload --port 8000
```
* **Swagger API Docs**: `http://localhost:8000/docs`
* **Healthcheck**: `http://localhost:8000/health`

#### Terminal 3: Next.js Web Dashboard
```powershell
cd frontend/forgellm-dashboard
npm install
npm run dev
```
* **Web Dashboard**: `http://localhost:3000`

---

## 💻 CLI Command Reference

| Command | Description |
| :--- | :--- |
| `forge system profile` | Detect PyTorch, CUDA, VRAM, and GPU acceleration. |
| `forge dataset validate <file>` | Validate JSON structure and ChatML schema compliance. |
| `forge dataset prepare <file>` | Clean, format, split, and register a new dataset. |
| `forge train --dataset <name>` | Launch LoRA/QLoRA fine-tuning training job. |
| `forge experiment list` | List all historical training experiments. |
| `forge evaluate <exp_id>` | Compute quality metrics and run CI quality gate. |
| `forge model list` | Display local registered models and versions. |
| `forge model show <ref>` | View metadata and configuration for a model version. |
| `forge model promote <name> <v>` | Promote model version in MLflow registry. |
| `forge chat <model_ref>` | Launch interactive local chat interface. |

---

## 🐳 Docker Deployment

To spin up the multi-container production stack using Docker Compose:

```bash
# Build and start services in background
docker-compose up --build -d

# Check service status
docker-compose ps
```

Containerized services:
* **Web Dashboard**: `http://localhost:3000`
* **FastAPI Backend**: `http://localhost:8000`
* **MLflow Tracking**: `http://localhost:5000`

---

## 🧪 Testing & Code Quality

ForgeLLM enforces rigorous quality standards:

```bash
# Run unit and integration tests
pytest

# Run code style & lint checks
ruff check .

# Run security static analysis
bandit -r src/ backend/
```

Automated GitHub Actions workflows (`.github/workflows/pipeline.yml`) run these verification steps on every push and pull request.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
