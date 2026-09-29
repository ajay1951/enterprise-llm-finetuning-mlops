"""Regression Analysis and Quality Gate Engine.

Compares Base Model vs Fine-Tuned Model evaluation results across objective metrics
and optional LLM Judge dimensions (including safety guards).
Enforces multi-metric quality gates with configurable thresholds to block regressions in CI/CD.
"""

import datetime
import json
import os
from typing import Any

from pydantic import BaseModel, Field


class QualityGateConfig(BaseModel):
    """Configurable thresholds for post-training regression analysis and CI quality gates."""

    max_rouge_degradation: float = Field(
        default=0.01,
        description="Maximum tolerated drop in ROUGE-L before failing gate.",
    )
    min_rouge_improvement: float = Field(
        default=0.0,
        description="Minimum ROUGE-L delta required for 'improved' status.",
    )
    max_exact_match_degradation: float = Field(
        default=0.02,
        description="Maximum tolerated drop in Exact Match rate before failing gate.",
    )
    min_exact_match_improvement: float = Field(
        default=0.0,
        description="Minimum Exact Match delta required for 'improved' status.",
    )
    max_semantic_similarity_degradation: float = Field(
        default=0.02,
        description="Maximum tolerated drop in Semantic Token Similarity before failing gate.",
    )
    min_semantic_similarity_improvement: float = Field(
        default=0.0,
        description="Minimum Semantic Token Similarity delta required for 'improved' status.",
    )
    max_composite_degradation: float = Field(
        default=0.02,
        description="Maximum tolerated drop in Composite Quality Score before failing gate.",
    )
    min_composite_improvement: float = Field(
        default=0.0,
        description="Minimum Composite Quality Score delta required for 'improved' status.",
    )
    max_judge_overall_degradation: float = Field(
        default=0.25,
        description="Maximum tolerated drop in LLM Judge overall score (1-5 scale).",
    )
    min_judge_overall_improvement: float = Field(
        default=0.0,
        description="Minimum LLM Judge overall delta required for 'improved' status.",
    )
    max_safety_degradation: float = Field(
        default=0.0,
        description="Maximum tolerated drop in LLM Judge safety score (default 0.0: zero tolerance).",
    )


class RegressionAnalyzer:
    """Analyzes performance deltas between a baseline and a fine-tuned model checkpoint."""

    def __init__(self, base_results: dict[str, Any], ft_results: dict[str, Any]):
        self.base_results = base_results
        self.ft_results = ft_results

    def compute_deltas(self) -> dict[str, Any]:
        """Compute deltas across all available objective and judge metrics."""
        base_obj = self.base_results.get("aggregate_metrics", {})
        ft_obj = self.ft_results.get("aggregate_metrics", {})

        base_judge = self.base_results.get("aggregate_judge_metrics") or {}
        ft_judge = self.ft_results.get("aggregate_judge_metrics") or {}

        deltas: dict[str, Any] = {
            # Objective Metrics
            "base_rougeL": base_obj.get("avg_rougeL", 0.0),
            "ft_rougeL": ft_obj.get("avg_rougeL", 0.0),
            "rougeL_delta": round(
                ft_obj.get("avg_rougeL", 0.0) - base_obj.get("avg_rougeL", 0.0), 4
            ),
            "base_exact_match": base_obj.get("avg_exact_match", 0.0),
            "ft_exact_match": ft_obj.get("avg_exact_match", 0.0),
            "exact_match_delta": round(
                ft_obj.get("avg_exact_match", 0.0)
                - base_obj.get("avg_exact_match", 0.0),
                4,
            ),
            "base_semantic_similarity": base_obj.get("avg_semantic_similarity", 0.0),
            "ft_semantic_similarity": ft_obj.get("avg_semantic_similarity", 0.0),
            "semantic_similarity_delta": round(
                ft_obj.get("avg_semantic_similarity", 0.0)
                - base_obj.get("avg_semantic_similarity", 0.0),
                4,
            ),
            "base_composite_quality": base_obj.get("avg_composite_quality_score", 0.0),
            "ft_composite_quality": ft_obj.get("avg_composite_quality_score", 0.0),
            "composite_quality_delta": round(
                ft_obj.get("avg_composite_quality_score", 0.0)
                - base_obj.get("avg_composite_quality_score", 0.0),
                4,
            ),
        }

        # LLM Judge Metrics (only if active in both)
        if base_judge and ft_judge:
            deltas["judge_available"] = True
            deltas["base_judge_overall"] = base_judge.get("avg_overall", 0.0)
            deltas["ft_judge_overall"] = ft_judge.get("avg_overall", 0.0)
            deltas["judge_overall_delta"] = round(
                ft_judge.get("avg_overall", 0.0) - base_judge.get("avg_overall", 0.0), 2
            )

            deltas["base_judge_safety"] = base_judge.get("avg_safety", 0.0)
            deltas["ft_judge_safety"] = ft_judge.get("avg_safety", 0.0)
            deltas["judge_safety_delta"] = round(
                ft_judge.get("avg_safety", 0.0) - base_judge.get("avg_safety", 0.0), 2
            )

            # Additional qualitative dimensions if present
            for dim in [
                "relevance",
                "helpfulness",
                "instruction_following",
                "factuality",
            ]:
                b_val = base_judge.get(f"avg_{dim}")
                f_val = ft_judge.get(f"avg_{dim}")
                if b_val is not None and f_val is not None:
                    deltas[f"base_judge_{dim}"] = b_val
                    deltas[f"ft_judge_{dim}"] = f_val
                    deltas[f"judge_{dim}_delta"] = round(f_val - b_val, 2)
        else:
            deltas["judge_available"] = False

        return deltas

    def check_quality_gate(
        self,
        config: QualityGateConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[str, list[str]]:
        """Evaluate whether the fine-tuned model passes regression quality gates.

        Returns:
            tuple of (status: 'improved' | 'equivalent' | 'regressed', failure_reasons: list[str])

        Semantics:
            - 'regressed' (passed = False): Triggered if ANY critical objective metric or judge dimension
              (especially Safety) degrades beyond its configured maximum tolerance.
            - 'improved' (passed = True): Triggered when all degradation tolerances are respected AND
              at least one key metric demonstrates meaningful positive gain exceeding threshold.
            - 'equivalent' (passed = True): Triggered when all metrics remain within acceptable bounds
              without meeting the threshold for notable improvement.
        """
        if config is None:
            gate_cfg = QualityGateConfig(**kwargs)
        elif isinstance(config, dict):
            combined = {**config, **kwargs}
            gate_cfg = QualityGateConfig(**combined)
        elif isinstance(config, QualityGateConfig):
            if kwargs:
                gate_cfg = config.model_copy(update=kwargs)
            else:
                gate_cfg = config
        else:
            gate_cfg = QualityGateConfig()

        deltas = self.compute_deltas()
        reasons: list[str] = []

        # 1. Objective metrics regression checks
        if deltas["rougeL_delta"] < -gate_cfg.max_rouge_degradation:
            reasons.append(
                f"ROUGE-L degraded by {deltas['rougeL_delta']:.4f} (tolerance: -{gate_cfg.max_rouge_degradation:.4f})"
            )

        if deltas["exact_match_delta"] < -gate_cfg.max_exact_match_degradation:
            reasons.append(
                f"Exact Match degraded by {deltas['exact_match_delta']:.4f} (tolerance: -{gate_cfg.max_exact_match_degradation:.4f})"
            )

        if (
            deltas["semantic_similarity_delta"]
            < -gate_cfg.max_semantic_similarity_degradation
        ):
            reasons.append(
                f"Semantic Token Similarity degraded by {deltas['semantic_similarity_delta']:.4f} (tolerance: -{gate_cfg.max_semantic_similarity_degradation:.4f})"
            )

        if deltas["composite_quality_delta"] < -gate_cfg.max_composite_degradation:
            reasons.append(
                f"Composite Quality Score degraded by {deltas['composite_quality_delta']:.4f} (tolerance: -{gate_cfg.max_composite_degradation:.4f})"
            )

        # 2. LLM Judge metrics regression checks (when judge is available)
        if deltas.get("judge_available", False):
            # Hard Safety Gate: Zero tolerance for safety drop by default
            if deltas["judge_safety_delta"] < -gate_cfg.max_safety_degradation:
                reasons.append(
                    f"LLM Judge Safety score degraded by {deltas['judge_safety_delta']:.2f} (tolerance: -{gate_cfg.max_safety_degradation:.2f})"
                )

            if deltas["judge_overall_delta"] < -gate_cfg.max_judge_overall_degradation:
                reasons.append(
                    f"LLM Judge Overall score degraded by {deltas['judge_overall_delta']:.2f} (tolerance: -{gate_cfg.max_judge_overall_degradation:.2f})"
                )

        if reasons:
            return "regressed", reasons

        # 3. Check for meaningful improvement
        improved_signals = 0
        if (
            gate_cfg.min_rouge_improvement > 0
            and deltas["rougeL_delta"] >= gate_cfg.min_rouge_improvement
        ):
            improved_signals += 1
        if (
            gate_cfg.min_exact_match_improvement > 0
            and deltas["exact_match_delta"] >= gate_cfg.min_exact_match_improvement
        ):
            improved_signals += 1
        if (
            gate_cfg.min_semantic_similarity_improvement > 0
            and deltas["semantic_similarity_delta"]
            >= gate_cfg.min_semantic_similarity_improvement
        ):
            improved_signals += 1
        if (
            gate_cfg.min_composite_improvement > 0
            and deltas["composite_quality_delta"] >= gate_cfg.min_composite_improvement
        ):
            improved_signals += 1
        if (
            deltas.get("judge_available", False)
            and gate_cfg.min_judge_overall_improvement > 0
            and deltas["judge_overall_delta"] >= gate_cfg.min_judge_overall_improvement
        ):
            improved_signals += 1

        # Default positive gain heuristics if no explicit positive thresholds were set
        if (
            improved_signals > 0
            or (
                deltas["rougeL_delta"] > 0.01
                and deltas["composite_quality_delta"] > 0.01
            )
            or (
                deltas.get("judge_available", False)
                and deltas["judge_overall_delta"] >= 0.2
            )
        ):
            return "improved", []

        return "equivalent", []

    def generate_report(
        self,
        output_dir: str,
        config: QualityGateConfig | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate structured regression results JSON and Markdown summary report."""
        os.makedirs(output_dir, exist_ok=True)
        if config is None:
            gate_cfg = QualityGateConfig(**kwargs)
        elif isinstance(config, dict):
            combined = {**config, **kwargs}
            gate_cfg = QualityGateConfig(**combined)
        elif isinstance(config, QualityGateConfig):
            if kwargs:
                gate_cfg = config.model_copy(update=kwargs)
            else:
                gate_cfg = config
        else:
            gate_cfg = QualityGateConfig()

        deltas = self.compute_deltas()
        status, reasons = self.check_quality_gate(config=gate_cfg)

        passed = status in ["improved", "equivalent"]

        payload: dict[str, Any] = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "thresholds": gate_cfg.model_dump(),
            "metrics": deltas,
            "status": status,
            "passed": passed,
            "failure_reasons": reasons,
        }

        # Save JSON
        json_path = os.path.join(output_dir, "regression_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # Save Markdown
        md_path = os.path.join(output_dir, "regression_report.md")
        self._write_markdown_report(payload, md_path)

        return payload

    def _write_markdown_report(self, payload: dict[str, Any], output_path: str) -> None:
        metrics = payload["metrics"]
        status = payload["status"]
        passed = payload["passed"]
        reasons = payload.get("failure_reasons", [])

        pass_text = "PASSED" if passed else "FAILED (REGRESSION)"
        status_text = status.upper()

        md = "# ForgeLLM Post-Training Regression Report\n\n"
        md += f"- **Timestamp:** `{payload['timestamp']}`\n"
        md += f"- **Quality Gate Result:** **{pass_text}**\n"
        md += f"- **Model Categorization:** `{status_text}`\n"
        md += f"- **Passed:** `{passed}`\n\n"

        if reasons:
            md += "### Quality Gate Failure Reasons\n"
            for r in reasons:
                md += f"- ❌ {r}\n"
            md += "\n"

        md += "## 1. Objective Metric Comparison\n\n"
        md += "| Metric | Base Model | Fine-Tuned | Delta | Status |\n"
        md += "|---|---|---|---|---|\n"

        def fmt_delta(val: float) -> str:
            sign = "+" if val > 0 else ""
            return f"`{sign}{val:.4f}`"

        r_delta = metrics["rougeL_delta"]
        em_delta = metrics["exact_match_delta"]
        sim_delta = metrics["semantic_similarity_delta"]
        comp_delta = metrics["composite_quality_delta"]

        md += f"| **Exact Match** | `{metrics['base_exact_match'] * 100:.1f}%` | `{metrics['ft_exact_match'] * 100:.1f}%` | {fmt_delta(em_delta)} | {'🟢' if em_delta >= 0 else '🔴'} |\n"
        md += f"| **ROUGE-L** | `{metrics['base_rougeL']:.4f}` | `{metrics['ft_rougeL']:.4f}` | {fmt_delta(r_delta)} | {'🟢' if r_delta >= 0 else '🔴'} |\n"
        md += f"| **Semantic Similarity** | `{metrics['base_semantic_similarity']:.4f}` | `{metrics['ft_semantic_similarity']:.4f}` | {fmt_delta(sim_delta)} | {'🟢' if sim_delta >= 0 else '🔴'} |\n"
        md += f"| **Composite Quality** | `{metrics['base_composite_quality']:.4f}` | `{metrics['ft_composite_quality']:.4f}` | {fmt_delta(comp_delta)} | {'🟢' if comp_delta >= 0 else '🔴'} |\n\n"

        md += "## 2. LLM-as-a-Judge Comparison\n\n"
        if metrics.get("judge_available", False):
            md += "| Evaluation Dimension | Base Model | Fine-Tuned | Delta |\n"
            md += "|---|---|---|---|\n"
            j_ov_delta = metrics.get("judge_overall_delta", 0.0)
            j_saf_delta = metrics.get("judge_safety_delta", 0.0)
            md += (
                f"| **Overall Quality (1-5)** | `{metrics['base_judge_overall']:.2f}` | `{metrics['ft_judge_overall']:.2f}` | `+{j_ov_delta:.2f}` |\n"
                if j_ov_delta >= 0
                else f"| **Overall Quality (1-5)** | `{metrics['base_judge_overall']:.2f}` | `{metrics['ft_judge_overall']:.2f}` | `{j_ov_delta:.2f}` |\n"
            )
            md += (
                f"| **Safety Score (1-5)** | `{metrics['base_judge_safety']:.2f}` | `{metrics['ft_judge_safety']:.2f}` | `+{j_saf_delta:.2f}` |\n"
                if j_saf_delta >= 0
                else f"| **Safety Score (1-5)** | `{metrics['base_judge_safety']:.2f}` | `{metrics['ft_judge_safety']:.2f}` | `{j_saf_delta:.2f}` |\n"
            )
            for dim in [
                "relevance",
                "helpfulness",
                "instruction_following",
                "factuality",
            ]:
                if f"base_judge_{dim}" in metrics:
                    d_delta = metrics[f"judge_{dim}_delta"]
                    sign = "+" if d_delta >= 0 else ""
                    md += f"| **{dim.replace('_', ' ').title()} (1-5)** | `{metrics[f'base_judge_{dim}']:.2f}` | `{metrics[f'ft_judge_{dim}']:.2f}` | `{sign}{d_delta:.2f}` |\n"
            md += "\n"
        else:
            md += "*LLM Judge: NOT CONFIGURED (Evaluation conducted using deterministic objective metrics only)*\n\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
