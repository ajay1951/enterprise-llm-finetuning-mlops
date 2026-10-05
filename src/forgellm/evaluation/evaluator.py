"""ForgeLLM Evaluation Engine.

Provides deterministic objective evaluation (Exact Match, ROUGE-L, Semantic Token Similarity,
Composite Quality Score) and optional real LLM-as-a-Judge multi-dimensional scoring.
"""

import datetime
import json
import os
import subprocess  # nosec B404
from typing import Any

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

from forgellm.evaluation.judge import LLMJudge

try:
    from rouge_score import rouge_scorer
except ImportError:
    rouge_scorer = None


def get_git_sha() -> str:
    """Helper to retrieve active git commit SHA for auditability."""
    try:
        return (
            subprocess.check_output(  # nosec B603 B607
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode("ascii")
            .strip()
        )
    except Exception:
        return os.environ.get("GITHUB_SHA", "unknown")


def compute_rouge_l(reference: str, candidate: str) -> float:
    """Pure-Python deterministic Longest Common Subsequence (LCS) ROUGE-L F1 calculation."""
    ref_tokens = reference.strip().lower().split()
    cand_tokens = candidate.strip().lower().split()
    if not ref_tokens or not cand_tokens:
        return 1.0 if reference.strip() == candidate.strip() else 0.0

    m, n = len(ref_tokens), len(cand_tokens)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if ref_tokens[i] == cand_tokens[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])

    lcs_len = dp[m][n]
    if lcs_len == 0:
        return 0.0

    precision = lcs_len / n
    recall = lcs_len / m
    if precision + recall == 0:
        return 0.0
    f1 = (2 * precision * recall) / (precision + recall)
    return round(float(f1), 4)


class ForgeEvaluator:
    """Evaluates language model predictions using objective deterministic metrics

    and optional provider-independent LLM-as-a-Judge assessment.
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        model_version: str = "base-model",
        dataset_version: str = "v1.0",
        judge: LLMJudge | None = None,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = model.device if hasattr(model, "device") else torch.device("cpu")
        self.model_version = model_version
        self.dataset_version = dataset_version
        self.judge = judge or LLMJudge()

        if rouge_scorer:
            try:
                self.scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
            except Exception:
                self.scorer = None
        else:
            self.scorer = None

    def generate_response(self, prompt: str, max_new_tokens: int = 64) -> str:
        """Generate response deterministically using greedy decoding (do_sample=False)."""
        messages = [{"role": "user", "content": prompt}]
        try:
            prompt_formatted = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            prompt_formatted = f"User: {prompt}\nAssistant:"

        raw_inputs = self.tokenizer(prompt_formatted, return_tensors="pt")
        input_ids = raw_inputs["input_ids"].to(self.device)
        attention_mask = raw_inputs.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)

        input_len = input_ids.shape[-1]

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                eos_token_id=getattr(self.tokenizer, "eos_token_id", None),
                pad_token_id=getattr(self.tokenizer, "eos_token_id", None),
            )

        generated_text = self.tokenizer.decode(
            outputs[0][input_len:], skip_special_tokens=True
        )
        return generated_text.strip()

    def compute_metrics(self, expected: str, generated: str) -> dict[str, float]:
        """Compute objective deterministic metrics between expected and generated text.

        Metrics Calculated:
        - exact_match: Binary indicator (1.0 if identical whitespace-stripped strings, else 0.0).
        - rougeL: Longest Common Subsequence F1 measure (0.0 to 1.0).
        - semantic_similarity: Token-set Jaccard similarity (|intersection| / |union| on lowercased words).
        - composite_quality_score: Deterministic weighted combination:
            0.5 * rougeL + 0.3 * semantic_similarity + 0.2 * min(len(generated)/max(len(expected), 1), 1.0).
        """
        exp_clean = expected.strip()
        gen_clean = generated.strip()

        if not exp_clean and not gen_clean:
            return {
                "exact_match": 1.0,
                "rougeL": 1.0,
                "semantic_similarity": 1.0,
                "composite_quality_score": 1.0,
            }

        metrics: dict[str, float] = {
            "exact_match": 1.0 if exp_clean == gen_clean else 0.0
        }

        # ROUGE-L calculation with pure-Python fallback
        if self.scorer and exp_clean and gen_clean:
            try:
                scores = self.scorer.score(expected, generated)
                metrics["rougeL"] = round(float(scores["rougeL"].fmeasure), 4)
            except Exception:
                metrics["rougeL"] = compute_rouge_l(expected, generated)
        else:
            metrics["rougeL"] = compute_rouge_l(expected, generated)

        # Semantic Token Similarity (Jaccard Index)
        exp_tokens = set(exp_clean.lower().split())
        gen_tokens = set(gen_clean.lower().split())
        if exp_tokens or gen_tokens:
            intersection = exp_tokens.intersection(gen_tokens)
            union = exp_tokens.union(gen_tokens)
            metrics["semantic_similarity"] = (
                round(len(intersection) / len(union), 4) if union else 1.0
            )
        else:
            metrics["semantic_similarity"] = 1.0

        # Composite Quality Score (Deterministic heuristic formula, normalized to 0.0-1.0)
        len_ratio = (
            min(len(gen_clean) / max(len(exp_clean), 1), 1.0) if exp_clean else 1.0
        )
        composite = (
            (0.5 * metrics["rougeL"])
            + (0.3 * metrics["semantic_similarity"])
            + (0.2 * len_ratio)
        )
        metrics["composite_quality_score"] = round(max(0.0, min(1.0, composite)), 4)

        return metrics

    def evaluate_test_set(self, test_file: str, output_dir: str) -> dict[str, Any]:
        """Run full evaluation on a test dataset, generating structured JSON and Markdown artifacts."""
        if not os.path.exists(test_file):
            raise FileNotFoundError(f"Test file not found: {test_file}")

        os.makedirs(output_dir, exist_ok=True)
        results: list[dict[str, Any]] = []
        judge_results: list[dict[str, Any]] = []

        total_em = 0.0
        total_rouge = 0.0
        total_sim = 0.0
        total_composite = 0.0

        # Judge accumulators
        judge_enabled = self.judge.is_enabled()
        judge_totals = {
            "relevance": 0.0,
            "helpfulness": 0.0,
            "instruction_following": 0.0,
            "factuality": 0.0,
            "safety": 0.0,
            "overall": 0.0,
        }
        judge_evaluated_count = 0

        with open(test_file, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    prompt = next(
                        msg["content"]
                        for msg in record["messages"]
                        if msg["role"] == "user"
                    )
                    expected = next(
                        (
                            msg["content"]
                            for msg in record["messages"]
                            if msg["role"] == "assistant"
                        ),
                        "",
                    )

                    response = self.generate_response(prompt)
                    obj_metrics = self.compute_metrics(expected, response)

                    total_em += obj_metrics["exact_match"]
                    total_rouge += obj_metrics["rougeL"]
                    total_sim += obj_metrics["semantic_similarity"]
                    total_composite += obj_metrics["composite_quality_score"]

                    print(
                        f"  [Evaluator] Evaluated sample {line_idx} | composite: {obj_metrics['composite_quality_score']:.2f}",
                        flush=True,
                    )

                    record_payload: dict[str, Any] = {
                        "sample_id": line_idx,
                        "prompt": prompt,
                        "expected": expected,
                        "generated": response,
                        "objective_metrics": obj_metrics,
                    }

                    # Run LLM Judge if configured
                    if judge_enabled:
                        try:
                            j_score = self.judge.evaluate(
                                prompt=prompt, generated=response, expected=expected
                            )
                            record_payload["judge_metrics"] = j_score.model_dump()

                            judge_totals["relevance"] += j_score.relevance
                            judge_totals["helpfulness"] += j_score.helpfulness
                            judge_totals["instruction_following"] += (
                                j_score.instruction_following
                            )
                            judge_totals["factuality"] += j_score.factuality
                            judge_totals["safety"] += j_score.safety
                            judge_totals["overall"] += j_score.overall
                            judge_evaluated_count += 1

                            judge_results.append(
                                {
                                    "sample_id": line_idx,
                                    "prompt": prompt,
                                    "generated": response,
                                    "score": j_score.model_dump(),
                                }
                            )
                        except Exception as e:
                            record_payload["judge_error"] = str(e)

                    results.append(record_payload)
                except Exception as e:
                    print(f"Skipping malformed test line {line_idx}: {e}")

        num_samples = len(results)
        agg_objective: dict[str, Any] = {
            "total_samples": num_samples,
            "avg_exact_match": round(total_em / num_samples, 4)
            if num_samples > 0
            else 0.0,
            "avg_rougeL": round(total_rouge / num_samples, 4)
            if num_samples > 0
            else 0.0,
            "avg_semantic_similarity": round(total_sim / num_samples, 4)
            if num_samples > 0
            else 0.0,
            "avg_composite_quality_score": round(total_composite / num_samples, 4)
            if num_samples > 0
            else 0.0,
        }

        agg_judge: dict[str, Any] | None = None
        if judge_enabled and judge_evaluated_count > 0:
            agg_judge = {
                "evaluated_samples": judge_evaluated_count,
                "avg_relevance": round(
                    judge_totals["relevance"] / judge_evaluated_count, 2
                ),
                "avg_helpfulness": round(
                    judge_totals["helpfulness"] / judge_evaluated_count, 2
                ),
                "avg_instruction_following": round(
                    judge_totals["instruction_following"] / judge_evaluated_count, 2
                ),
                "avg_factuality": round(
                    judge_totals["factuality"] / judge_evaluated_count, 2
                ),
                "avg_safety": round(judge_totals["safety"] / judge_evaluated_count, 2),
                "avg_overall": round(
                    judge_totals["overall"] / judge_evaluated_count, 2
                ),
            }

        final_payload: dict[str, Any] = {
            "metadata": {
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "git_sha": get_git_sha(),
                "model_version": self.model_version,
                "dataset_version": self.dataset_version,
                "judge_metadata": self.judge.get_metadata()
                if judge_enabled
                else {"status": "disabled"},
            },
            "aggregate_metrics": agg_objective,
            "aggregate_judge_metrics": agg_judge,
            "results": results,
        }

        # 1. Save evaluation_results.json
        json_path = os.path.join(output_dir, "evaluation_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, indent=2)

        # 2. Save standalone metrics.json (summarized for CI/CD)
        metrics_path = os.path.join(output_dir, "metrics.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": final_payload["metadata"],
                    "objective": agg_objective,
                    "judge": agg_judge,
                },
                f,
                indent=2,
            )

        # 3. Save predictions.jsonl
        pred_path = os.path.join(output_dir, "predictions.jsonl")
        with open(pred_path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in results)

        # 4. Save judge_results.jsonl if judge was active
        if judge_enabled and judge_results:
            judge_jsonl_path = os.path.join(output_dir, "judge_results.jsonl")
            with open(judge_jsonl_path, "w", encoding="utf-8") as f:
                f.writelines(
                    json.dumps(jr, ensure_ascii=False) + "\n" for jr in judge_results
                )

        # 5. Generate Markdown Report
        md_path = os.path.join(output_dir, "report.md")
        self.generate_markdown_report(final_payload, md_path)

        # Legacy compatibility link for baseline_report.md
        legacy_md_path = os.path.join(output_dir, "baseline_report.md")
        self.generate_markdown_report(final_payload, legacy_md_path)

        # Log to MLflow if active run exists
        try:
            import mlflow

            if mlflow.active_run():
                mlflow_metrics: dict[str, float] = {
                    "eval_exact_match": agg_objective["avg_exact_match"],
                    "eval_rougeL": agg_objective["avg_rougeL"],
                    "eval_semantic_similarity": agg_objective[
                        "avg_semantic_similarity"
                    ],
                    "eval_composite_quality_score": agg_objective[
                        "avg_composite_quality_score"
                    ],
                }
                if agg_judge:
                    mlflow_metrics.update(
                        {
                            "eval_judge_relevance": agg_judge["avg_relevance"],
                            "eval_judge_helpfulness": agg_judge["avg_helpfulness"],
                            "eval_judge_instruction_following": agg_judge[
                                "avg_instruction_following"
                            ],
                            "eval_judge_factuality": agg_judge["avg_factuality"],
                            "eval_judge_safety": agg_judge["avg_safety"],
                            "eval_judge_overall": agg_judge["avg_overall"],
                        }
                    )

                mlflow.log_metrics(mlflow_metrics)
                mlflow.log_artifact(json_path, artifact_path="evaluation")
                mlflow.log_artifact(metrics_path, artifact_path="evaluation")
                mlflow.log_artifact(pred_path, artifact_path="evaluation")
                mlflow.log_artifact(md_path, artifact_path="evaluation")
                if judge_enabled and judge_results:
                    mlflow.log_artifact(judge_jsonl_path, artifact_path="evaluation")
        except ImportError:
            pass

        return final_payload

    def generate_markdown_report(self, payload: dict, output_path: str):
        """Generate a transparent markdown evaluation report distinguishing objective and judge metrics."""
        meta = payload["metadata"]
        obj = payload["aggregate_metrics"]
        judge = payload.get("aggregate_judge_metrics")

        md = "# ForgeLLM Model Evaluation Report\n\n"
        md += f"- **Timestamp:** `{meta['timestamp']}`\n"
        md += f"- **Git SHA:** `{meta.get('git_sha', 'unknown')}`\n"
        md += f"- **Model Version:** `{meta['model_version']}`\n"
        md += f"- **Dataset Version:** `{meta['dataset_version']}`\n\n"

        md += "## 1. Objective Deterministic Metrics\n\n"
        md += "| Metric | Score | Definition |\n"
        md += "|:---|:---|:---|\n"
        md += f"| **Exact Match** | `{obj['avg_exact_match'] * 100:.1f}%` | Exact string match on normalized output |\n"
        md += f"| **ROUGE-L** | `{obj['avg_rougeL']:.4f}` | Longest Common Subsequence F1 measure |\n"
        md += f"| **Semantic Similarity** | `{obj['avg_semantic_similarity']:.4f}` | Token-set Jaccard similarity index |\n"
        md += f"| **Composite Quality Score** | `{obj['avg_composite_quality_score']:.4f}` | Deterministic formula: 0.5*ROUGE-L + 0.3*Similarity + 0.2*LengthRatio |\n\n"

        if judge:
            j_meta = meta.get("judge_metadata", {})
            md += "## 2. LLM-as-a-Judge Evaluation (Optional)\n\n"
            md += f"- **Judge Provider:** `{j_meta.get('judge_provider', 'unknown')}`\n"
            md += f"- **Judge Model:** `{j_meta.get('judge_model', 'unknown')}`\n"
            md += f"- **Rubric Version:** `{j_meta.get('rubric_version', 'v1.0')}`\n\n"
            md += "| Evaluation Dimension | Score (1-5) |\n"
            md += "|:---|:---|\n"
            md += f"| **Relevance** | `{judge['avg_relevance']} / 5.0` |\n"
            md += f"| **Helpfulness** | `{judge['avg_helpfulness']} / 5.0` |\n"
            md += f"| **Instruction Following** | `{judge['avg_instruction_following']} / 5.0` |\n"
            md += f"| **Factuality** | `{judge['avg_factuality']} / 5.0` |\n"
            md += f"| **Safety** | `{judge['avg_safety']} / 5.0` |\n"
            md += f"| **Overall Quality** | `{judge['avg_overall']} / 5.0` |\n\n"
        else:
            md += "## 2. LLM-as-a-Judge\n\n*LLM Judge not configured for this run (objective evaluation only).*\n\n"

        md += "## 3. Sample Predictions\n\n"
        for i, res in enumerate(payload.get("results", [])[:5], start=1):
            md += f"### Sample {i}\n"
            md += f"**Prompt:**\n> {res['prompt']}\n\n"
            md += f"**Expected:**\n{res['expected']}\n\n"
            md += f"**Generated:**\n{res['generated']}\n\n"
            obj_m = res["objective_metrics"]
            md += f"- *Objective:* ROUGE-L: `{obj_m['rougeL']:.4f}` | EM: `{int(obj_m['exact_match'])}` | Composite: `{obj_m['composite_quality_score']:.4f}`\n"
            if "judge_metrics" in res:
                jm = res["judge_metrics"]
                md += f"- *Judge Overall:* `{jm['overall']}/5.0` (Safety: `{jm['safety']}/5`) — *Reason:* {jm['reason']}\n"
            md += "\n---\n\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
