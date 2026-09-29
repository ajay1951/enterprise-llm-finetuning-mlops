# ForgeLLM Model Evaluation Report

- **Timestamp:** `2026-09-29T14:50:03.714698+00:00`
- **Git SHA:** `2bfb6a7ead15aedee6407232d14614efb266de5a`
- **Model Version:** `Qwen/Qwen2.5-0.5B-base`
- **Dataset Version:** `v1`

## 1. Objective Deterministic Metrics

| Metric | Score | Definition |
|:---|:---|:---|
| **Exact Match** | `0.0%` | Exact string match on normalized output |
| **ROUGE-L** | `0.0138` | Longest Common Subsequence F1 measure |
| **Semantic Similarity** | `0.0556` | Token-set Jaccard similarity index |
| **Composite Quality Score** | `0.2236` | Deterministic formula: 0.5*ROUGE-L + 0.3*Similarity + 0.2*LengthRatio |

## 2. LLM-as-a-Judge

*LLM Judge not configured for this run (objective evaluation only).*

## 3. Sample Predictions

### Sample 1
**Prompt:**
> Hello!

**Expected:**
Hi there! How can I help you today?

**Generated:**
system
You are a helpful assistant.
user
Hello!
assistant
Hello!uable
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco
acco

- *Objective:* ROUGE-L: `0.0138` | EM: `0` | Composite: `0.2236`

---

