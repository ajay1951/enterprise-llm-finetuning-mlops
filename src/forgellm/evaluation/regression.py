import datetime
import json
import os
from typing import Any


class RegressionAnalyzer:
    def __init__(self, base_results: dict[str, Any], ft_results: dict[str, Any]):
        self.base_results = base_results
        self.ft_results = ft_results

    def compute_deltas(self) -> dict[str, Any]:
        base_agg = self.base_results.get("aggregate_metrics", {})
        ft_agg = self.ft_results.get("aggregate_metrics", {})

        rouge_delta = ft_agg.get("avg_rougeL", 0) - base_agg.get("avg_rougeL", 0)
        em_delta = ft_agg.get("avg_exact_match", 0) - base_agg.get("avg_exact_match", 0)

        return {
            "rougeL_delta": rouge_delta,
            "exact_match_delta": em_delta,
            "base_rougeL": base_agg.get("avg_rougeL", 0),
            "ft_rougeL": ft_agg.get("avg_rougeL", 0),
            "base_em": base_agg.get("avg_exact_match", 0),
            "ft_em": ft_agg.get("avg_exact_match", 0),
        }

    def check_quality_gate(self, min_rouge_improvement: float, max_rouge_degradation: float) -> str:
        deltas = self.compute_deltas()
        rouge_delta = deltas["rougeL_delta"]
        
        # If it improved by at least the min threshold
        if rouge_delta >= min_rouge_improvement:
            return "improved"
        # If it degraded by more than the allowed tolerance (a negative delta)
        elif rouge_delta <= -max_rouge_degradation:
            return "regressed"
        # Otherwise it falls in the middle tolerance band
        else:
            return "equivalent"

    def generate_report(self, output_dir: str, min_rouge_improvement: float, max_rouge_degradation: float) -> dict:
        os.makedirs(output_dir, exist_ok=True)
        
        deltas = self.compute_deltas()
        status = self.check_quality_gate(min_rouge_improvement, max_rouge_degradation)
        
        passed = status in ["improved", "equivalent"]
        
        payload = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "thresholds": {
                "min_rouge_improvement": min_rouge_improvement,
                "max_rouge_degradation": max_rouge_degradation
            },
            "metrics": deltas,
            "status": status,
            "passed": passed
        }
        
        # Save JSON
        json_path = os.path.join(output_dir, "regression_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            
        # Save Markdown
        md_path = os.path.join(output_dir, "regression_report.md")
        self._write_markdown_report(payload, md_path)
        
        return payload

    def _write_markdown_report(self, payload: dict, output_path: str):
        metrics = payload["metrics"]
        status = payload["status"]
        passed = payload["passed"]
        
        pass_text = "✅ PASSED" if passed else "❌ FAILED (REGRESSION)"
        status_text = status.upper()
        
        md = "# Post-Training Regression Report\n\n"
        md += f"**Timestamp:** {payload['timestamp']}\n"
        md += f"**Quality Gate Status:** {pass_text}\n"
        md += f"**Model Categorization:** {status_text}\n\n"
        
        md += "## Metric Deltas\n\n"
        md += "| Metric | Base Model | Fine-Tuned | Delta |\n"
        md += "|---|---|---|---|\n"
        
        r_sign = "+" if metrics["rougeL_delta"] > 0 else ""
        em_sign = "+" if metrics["exact_match_delta"] > 0 else ""
        
        md += f"| ROUGE-L | {metrics['base_rougeL']:.4f} | {metrics['ft_rougeL']:.4f} | {r_sign}{metrics['rougeL_delta']:.4f} |\n"
        md += f"| Exact Match | {metrics['base_em']:.4f} | {metrics['ft_em']:.4f} | {em_sign}{metrics['exact_match_delta']:.4f} |\n\n"
        
        md += "## Configuration\n"
        md += f"- **Min Required Improvement (ROUGE-L):** +{payload['thresholds']['min_rouge_improvement']}\n"
        md += f"- **Max Allowed Degradation (ROUGE-L):** -{payload['thresholds']['max_rouge_degradation']}\n"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
