import pytest

from forgellm.evaluation.regression import RegressionAnalyzer


def make_eval_result(
    rouge: float,
    em: float,
    similarity: float,
    composite: float,
    judge_overall: float | None = None,
    judge_safety: float | None = None,
):
    agg_obj = {
        "avg_rougeL": rouge,
        "avg_exact_match": em,
        "avg_semantic_similarity": similarity,
        "avg_composite_quality_score": composite,
    }
    agg_judge = None
    if judge_overall is not None and judge_safety is not None:
        agg_judge = {
            "avg_overall": judge_overall,
            "avg_safety": judge_safety,
            "avg_relevance": judge_overall,
            "avg_helpfulness": judge_overall,
            "avg_instruction_following": judge_overall,
            "avg_factuality": judge_overall,
        }
    return {
        "aggregate_metrics": agg_obj,
        "aggregate_judge_metrics": agg_judge,
    }


def test_regression_improvement():
    base = make_eval_result(rouge=0.50, em=0.40, similarity=0.60, composite=0.55)
    ft = make_eval_result(rouge=0.65, em=0.50, similarity=0.75, composite=0.70)

    analyzer = RegressionAnalyzer(base, ft)
    deltas = analyzer.compute_deltas()

    assert deltas["rougeL_delta"] == 0.15
    assert deltas["composite_quality_delta"] == 0.15

    status, reasons = analyzer.check_quality_gate(min_rouge_improvement=0.05)
    assert status == "improved"
    assert len(reasons) == 0


def test_regression_equivalent():
    base = make_eval_result(rouge=0.50, em=0.40, similarity=0.60, composite=0.55)
    ft = make_eval_result(rouge=0.505, em=0.40, similarity=0.605, composite=0.552)

    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(
        min_rouge_improvement=0.05,
        max_rouge_degradation=0.02,
    )
    assert status == "equivalent"
    assert len(reasons) == 0


def test_regression_objective_failure():
    base = make_eval_result(rouge=0.60, em=0.50, similarity=0.70, composite=0.65)
    ft = make_eval_result(rouge=0.45, em=0.30, similarity=0.50, composite=0.48)

    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(max_rouge_degradation=0.05)

    assert status == "regressed"
    assert len(reasons) > 0
    assert any("ROUGE-L" in r for r in reasons)


def test_regression_safety_block_despite_rouge_improvement():
    """Critical test: Even if ROUGE-L improves, a safety degradation MUST mark the model as regressed."""
    base = make_eval_result(
        rouge=0.50,
        em=0.40,
        similarity=0.60,
        composite=0.55,
        judge_overall=4.5,
        judge_safety=5.0,
    )
    ft = make_eval_result(
        rouge=0.75,
        em=0.60,
        similarity=0.85,
        composite=0.80,  # Massive ROUGE gain
        judge_overall=4.0,
        judge_safety=2.5,  # Dangerous safety drop
    )

    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(
        min_rouge_improvement=0.05,
        max_safety_degradation=0.0,  # Zero tolerance on safety
    )

    assert status == "regressed"
    assert any("Safety" in r or "safety" in r for r in reasons)


def test_regression_judge_overall_degradation():
    base = make_eval_result(
        rouge=0.50,
        em=0.40,
        similarity=0.60,
        composite=0.55,
        judge_overall=4.5,
        judge_safety=5.0,
    )
    ft = make_eval_result(
        rouge=0.50,
        em=0.40,
        similarity=0.60,
        composite=0.55,
        judge_overall=3.0,
        judge_safety=5.0,  # Quality dropped
    )

    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(max_judge_overall_degradation=0.3)

    assert status == "regressed"
    assert any("Judge overall" in r or "judge" in r for r in reasons)


def test_regression_report_generation(tmp_path):
    base = make_eval_result(rouge=0.50, em=0.40, similarity=0.60, composite=0.55)
    ft = make_eval_result(rouge=0.60, em=0.50, similarity=0.70, composite=0.65)

    analyzer = RegressionAnalyzer(base, ft)
    payload = analyzer.generate_report(str(tmp_path), min_rouge_improvement=0.05)

    assert payload["status"] == "improved"
    assert payload["passed"] is True
    assert (tmp_path / "regression_results.json").exists()
    assert (tmp_path / "regression_report.md").exists()
