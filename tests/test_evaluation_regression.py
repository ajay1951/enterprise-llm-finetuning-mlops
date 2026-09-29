from forgellm.evaluation.regression import QualityGateConfig, RegressionAnalyzer


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


def test_quality_gate_config_defaults():
    cfg = QualityGateConfig()
    assert cfg.max_safety_degradation == 0.0
    assert cfg.max_rouge_degradation == 0.01
    assert cfg.max_exact_match_degradation == 0.02
    assert cfg.max_semantic_similarity_degradation == 0.02
    assert cfg.max_composite_degradation == 0.02
    assert cfg.max_judge_overall_degradation == 0.25


# --- ROUGE-L Tests ---
def test_rouge_improvement():
    base = make_eval_result(0.40, 0.30, 0.50, 0.45)
    ft = make_eval_result(0.55, 0.30, 0.50, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(min_rouge_improvement=0.10)
    assert status == "improved"
    assert not reasons


def test_rouge_equivalent():
    base = make_eval_result(0.50, 0.30, 0.50, 0.45)
    ft = make_eval_result(0.505, 0.30, 0.50, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(
        min_rouge_improvement=0.05, max_rouge_degradation=0.02
    )
    assert status == "equivalent"
    assert not reasons


def test_rouge_allowed_degradation():
    base = make_eval_result(0.50, 0.30, 0.50, 0.45)
    ft = make_eval_result(0.49, 0.30, 0.50, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(max_rouge_degradation=0.02)
    assert status == "equivalent"
    assert not reasons


def test_rouge_hard_regression():
    base = make_eval_result(0.50, 0.30, 0.50, 0.45)
    ft = make_eval_result(0.45, 0.30, 0.50, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(max_rouge_degradation=0.02)
    assert status == "regressed"
    assert any("ROUGE-L" in r for r in reasons)


# --- Exact Match Tests ---
def test_exact_match_improvement():
    base = make_eval_result(0.50, 0.30, 0.50, 0.45)
    ft = make_eval_result(0.50, 0.45, 0.50, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(min_exact_match_improvement=0.10)
    assert status == "improved"
    assert not reasons


def test_exact_match_allowed_degradation():
    base = make_eval_result(0.50, 0.50, 0.50, 0.45)
    ft = make_eval_result(0.50, 0.49, 0.50, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, _ = analyzer.check_quality_gate(max_exact_match_degradation=0.02)
    assert status == "equivalent"


def test_exact_match_hard_regression():
    base = make_eval_result(0.50, 0.50, 0.50, 0.45)
    ft = make_eval_result(0.50, 0.40, 0.50, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(max_exact_match_degradation=0.02)
    assert status == "regressed"
    assert any("Exact Match" in r for r in reasons)


# --- Semantic Similarity Tests ---
def test_semantic_similarity_improvement():
    base = make_eval_result(0.50, 0.30, 0.50, 0.45)
    ft = make_eval_result(0.50, 0.30, 0.65, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, _ = analyzer.check_quality_gate(min_semantic_similarity_improvement=0.10)
    assert status == "improved"


def test_semantic_similarity_hard_regression():
    base = make_eval_result(0.50, 0.30, 0.70, 0.45)
    ft = make_eval_result(0.50, 0.30, 0.60, 0.45)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(
        max_semantic_similarity_degradation=0.05
    )
    assert status == "regressed"
    assert any("Semantic Token Similarity" in r for r in reasons)


# --- Composite Quality Tests ---
def test_composite_quality_improvement():
    base = make_eval_result(0.50, 0.30, 0.50, 0.45)
    ft = make_eval_result(0.50, 0.30, 0.50, 0.60)
    analyzer = RegressionAnalyzer(base, ft)
    status, _ = analyzer.check_quality_gate(min_composite_improvement=0.10)
    assert status == "improved"


def test_composite_quality_hard_regression():
    base = make_eval_result(0.50, 0.30, 0.50, 0.60)
    ft = make_eval_result(0.50, 0.30, 0.50, 0.50)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(max_composite_degradation=0.05)
    assert status == "regressed"
    assert any("Composite Quality" in r for r in reasons)


# --- LLM Judge Overall Tests ---
def test_judge_overall_improvement():
    base = make_eval_result(0.50, 0.30, 0.50, 0.45, judge_overall=3.5, judge_safety=5.0)
    ft = make_eval_result(0.50, 0.30, 0.50, 0.45, judge_overall=4.5, judge_safety=5.0)
    analyzer = RegressionAnalyzer(base, ft)
    status, _ = analyzer.check_quality_gate(min_judge_overall_improvement=0.5)
    assert status == "improved"


def test_judge_overall_hard_regression():
    base = make_eval_result(0.50, 0.30, 0.50, 0.45, judge_overall=4.5, judge_safety=5.0)
    ft = make_eval_result(0.50, 0.30, 0.50, 0.45, judge_overall=3.5, judge_safety=5.0)
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(max_judge_overall_degradation=0.5)
    assert status == "regressed"
    assert any("Judge Overall" in r or "judge" in r for r in reasons)


# --- Safety Gate Tests ---
def test_safety_hard_regression_blocks_even_with_massive_quality_gain():
    """CRITICAL: If ROUGE, Composite, and Judge Overall increase significantly,
    any safety regression beyond tolerance MUST reject the model.
    """
    base = make_eval_result(
        rouge=0.50,
        em=0.40,
        similarity=0.50,
        composite=0.48,
        judge_overall=3.5,
        judge_safety=5.0,
    )
    ft = make_eval_result(
        rouge=0.85,
        em=0.75,
        similarity=0.90,
        composite=0.88,
        judge_overall=4.8,
        judge_safety=4.8,  # Safety drop -0.2
    )
    analyzer = RegressionAnalyzer(base, ft)
    status, reasons = analyzer.check_quality_gate(
        min_rouge_improvement=0.05,
        max_safety_degradation=0.0,  # Zero tolerance
    )
    assert status == "regressed"
    assert any("Safety" in r or "safety" in r for r in reasons)


def test_judge_unavailable_honesty(tmp_path):
    """When judge is disabled/unavailable, objective metrics work and report explicitly notes NOT CONFIGURED."""
    base = make_eval_result(rouge=0.50, em=0.40, similarity=0.60, composite=0.55)
    ft = make_eval_result(rouge=0.55, em=0.42, similarity=0.62, composite=0.58)

    analyzer = RegressionAnalyzer(base, ft)
    deltas = analyzer.compute_deltas()
    assert deltas["judge_available"] is False

    payload = analyzer.generate_report(str(tmp_path))
    assert payload["passed"] is True
    assert payload["status"] == "improved"

    report_content = (tmp_path / "regression_report.md").read_text(encoding="utf-8")
    assert "LLM Judge: NOT CONFIGURED" in report_content
    assert "**Passed:** `True`" in report_content
