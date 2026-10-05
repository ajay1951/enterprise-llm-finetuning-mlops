# ForgeLLM Model Evaluation Report

- **Timestamp:** `2026-10-05T09:34:16.978509+00:00`
- **Git SHA:** `9adfc6469b117d56ac9bf6508194d02fa631da9a`
- **Model Version:** `Qwen/Qwen2.5-0.5B-finetuned`
- **Dataset Version:** `v1.0`

## 1. Objective Deterministic Metrics

| Metric | Score | Definition |
|:---|:---|:---|
| **Exact Match** | `0.0%` | Exact string match on normalized output |
| **ROUGE-L** | `0.1284` | Longest Common Subsequence F1 measure |
| **Semantic Similarity** | `0.0922` | Token-set Jaccard similarity index |
| **Composite Quality Score** | `0.2919` | Deterministic formula: 0.5*ROUGE-L + 0.3*Similarity + 0.2*LengthRatio |

## 2. LLM-as-a-Judge

*LLM Judge not configured for this run (objective evaluation only).*

## 3. Sample Predictions

### Sample 1
**Prompt:**
> What is ForgeLLM?

**Expected:**
ForgeLLM is an enterprise-grade LLM fine-tuning and evaluation platform designed for reproducibility and production readiness.

**Generated:**
ForgeLLM is a language model that can generate human-like text.orda
<quote>ForgeLLM is a language model that can generate human-like text.</quoteorda
<quote>ForgeLLM is a language model that can generate human-like text.</quoteorda
<quote>ForgeLLM is a language model that

- *Objective:* ROUGE-L: `0.0645` | EM: `0` | Composite: `0.2572`

---

### Sample 2
**Prompt:**
> How does LoRA work in parameter-efficient fine-tuning?

**Expected:**
LoRA freezes the pre-trained model weights and injects trainable rank decomposition matrices into Transformer layers, drastically reducing trainable parameters.

**Generated:**
LoRA is a variant of the Transformer architecture that allows for efficient parameter-efficient fine-tuning. LoRA is a variant of the Transformer architecture that allows for efficient parameter-efficient fine-tuning. LoRA is a variant of the Transformer architecture that allows for efficient parameter-efficient fine-tuning. LoRA is a variant of the

- *Objective:* ROUGE-L: `0.1081` | EM: `0` | Composite: `0.2851`

---

### Sample 3
**Prompt:**
> What is the purpose of QLoRA?

**Expected:**
QLoRA quantizes the frozen base model to 4-bit NormalFloat precision while keeping LoRA adapters in 16-bit brain floating point, allowing fine-tuning on consumer GPUs.

**Generated:**
QLoRA is a type of deep learning model that is designed to be more efficient and effective than traditional neural networks.oard
probante
What are the advantages of QLoRA?probante
probante
What are the disadvantages of QLoRA?probante
probante
What is the future of QLoRA?probante

- *Objective:* ROUGE-L: `0.0822` | EM: `0` | Composite: `0.2661`

---

### Sample 4
**Prompt:**
> What is the role of an LLM evaluation objective metric?

**Expected:**
Objective evaluation metrics such as Exact Match, ROUGE-L, and token semantic similarity provide deterministic, reproducible regression testing.

**Generated:**
An LLM evaluation objective metric is a metric that is used to evaluate the performance of an LLM model. It is used to measure the accuracy, precision, recall, and F1 score of the model. LPARAM evaluation objective metrics are used to compare the performance of different models and to identify the best model for a given

- *Objective:* ROUGE-L: `0.1081` | EM: `0` | Composite: `0.2796`

---

### Sample 5
**Prompt:**
> Explain how MLflow Model Registry tracks fine-tuned LLM artifacts.

**Expected:**
MLflow Model Registry centralizes model lineage, versioning, metadata, and production deployment alias promotion across experiments.

**Generated:**
MLflow Model Registry tracks fine-tuned LLM artifacts by storing the model's weights and hyperparameters in a JSON file. The model's weights are stored in a JSON file that contains the model's weights and hyperparameters. The hyperparameters are stored in a JSON file that contains the hyperparameters used to train the model

- *Objective:* ROUGE-L: `0.1429` | EM: `0` | Composite: `0.3039`

---

