# ForgeLLM Model Evaluation Report

- **Timestamp:** `2026-09-29T14:51:25.224506+00:00`
- **Git SHA:** `2bfb6a7ead15aedee6407232d14614efb266de5a`
- **Model Version:** `Qwen/Qwen2.5-0.5B-finetuned`
- **Dataset Version:** `v1`

## 1. Objective Deterministic Metrics

| Metric | Score | Definition |
|:---|:---|:---|
| **Exact Match** | `0.0%` | Exact string match on normalized output |
| **ROUGE-L** | `0.0276` | Longest Common Subsequence F1 measure |
| **Semantic Similarity** | `0.0500` | Token-set Jaccard similarity index |
| **Composite Quality Score** | `0.2288` | Deterministic formula: 0.5*ROUGE-L + 0.3*Similarity + 0.2*LengthRatio |

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
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.西班
acco
You are a helpful assistant.西班
acco
Hello!uable.

- *Objective:* ROUGE-L: `0.0276` | EM: `0` | Composite: `0.2288`

---

