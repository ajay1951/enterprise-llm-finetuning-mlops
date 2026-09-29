import json

import pytest
from pydantic import ValidationError

from forgellm.evaluation.evaluator import ForgeEvaluator
from forgellm.evaluation.judge import (
    BaseJudgeProvider,
    JudgeEvaluationError,
    JudgeScore,
    LLMJudge,
    MockJudgeProvider,
)


class DummyTokenizer:
    def __init__(self, fixed_output: str = "Test response"):
        self.fixed_output = fixed_output
        self.eos_token_id = 0

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return f"Formatted: {messages[0]['content']}"

    def __call__(self, text, return_tensors="pt"):
        import torch

        return {"input_ids": torch.tensor([[1, 2, 3]])}

    def decode(self, token_ids, skip_special_tokens=True):
        return self.fixed_output


class DummyModel:
    def __init__(self):
        import torch

        self.device = torch.device("cpu")

    def generate(self, **kwargs):
        import torch

        return torch.tensor([[1, 2, 3, 4, 5]])


def test_judge_score_valid_schema():
    valid_data = {
        "relevance": 5,
        "helpfulness": 4,
        "instruction_following": 5,
        "factuality": 4,
        "safety": 5,
        "overall": 4.6,
        "reason": "Accurate and directly answers prompt.",
    }
    score = JudgeScore(**valid_data)
    assert score.relevance == 5
    assert score.helpfulness == 4
    assert score.safety == 5
    assert score.overall == 4.6
    assert "Accurate" in score.reason


def test_judge_score_invalid_ranges():
    # Score below 1
    with pytest.raises(ValidationError):
        JudgeScore(
            relevance=0,
            helpfulness=4,
            instruction_following=5,
            factuality=4,
            safety=5,
            overall=3.0,
            reason="Invalid score",
        )

    # Score above 5
    with pytest.raises(ValidationError):
        JudgeScore(
            relevance=6,
            helpfulness=4,
            instruction_following=5,
            factuality=4,
            safety=5,
            overall=3.0,
            reason="Invalid score",
        )


def test_judge_score_missing_fields():
    # Missing 'reason'
    with pytest.raises(ValidationError):
        JudgeScore(
            relevance=4,
            helpfulness=4,
            instruction_following=4,
            factuality=4,
            safety=5,
            overall=4.0,
        )


def test_mock_judge_evaluation_success():
    mock_provider = MockJudgeProvider(
        fixed_score={
            "relevance": 4,
            "helpfulness": 5,
            "instruction_following": 4,
            "factuality": 5,
            "safety": 5,
            "overall": 4.6,
            "reason": "Response accurately follows the instruction.",
        }
    )
    judge = LLMJudge(custom_provider_instance=mock_provider)
    assert judge.is_enabled() is True

    result = judge.evaluate(
        prompt="What is Docker?",
        generated="Docker is a platform for developing, shipping, and running applications in containers.",
        expected="Docker is a containerization platform.",
    )

    assert isinstance(result, JudgeScore)
    assert result.relevance == 4
    assert result.helpfulness == 5
    assert result.overall == 4.6


def test_mock_judge_malformed_json():
    class MalformedProvider(BaseJudgeProvider):
        def evaluate(
            self, system_prompt: str, user_prompt: str, timeout: float = 30.0
        ) -> str:
            return "This is not valid JSON at all."

    judge = LLMJudge(custom_provider_instance=MalformedProvider())
    with pytest.raises(JudgeEvaluationError, match="non-JSON"):
        judge.evaluate(prompt="Test", generated="Test")


def test_mock_judge_provider_failure():
    mock_provider = MockJudgeProvider(should_fail=True, fail_reason="Provider timeout")
    judge = LLMJudge(custom_provider_instance=mock_provider)

    with pytest.raises(JudgeEvaluationError, match="Provider timeout"):
        judge.evaluate(prompt="Test", generated="Test")


def test_judge_disabled_by_default_without_config(monkeypatch):
    monkeypatch.delenv("FORGELLM_JUDGE_PROVIDER", raising=False)
    monkeypatch.delenv("FORGELLM_JUDGE_API_KEY", raising=False)

    judge = LLMJudge(provider="none")
    assert judge.is_enabled() is False

    with pytest.raises(JudgeEvaluationError, match="disabled"):
        judge.evaluate(prompt="Test", generated="Test")


def test_judge_reproducibility_metadata():
    mock_provider = MockJudgeProvider()
    judge = LLMJudge(
        provider="mock",
        model="mock-gpt",
        rubric_version="v1.0",
        custom_provider_instance=mock_provider,
    )
    meta = judge.get_metadata()

    assert meta["judge_provider"] == "mock"
    assert meta["judge_model"] == "mock-gpt"
    assert meta["rubric_version"] == "v1.0"
    assert "timestamp" in meta
    assert "git_sha" in meta


def test_evaluator_with_active_judge(tmp_path):
    test_jsonl = tmp_path / "test_with_judge.jsonl"
    out_dir = tmp_path / "eval_judge_output"

    record = {
        "messages": [
            {"role": "user", "content": "How do I reset my password?"},
            {
                "role": "assistant",
                "content": "Click 'Forgot Password' on the login screen.",
            },
        ]
    }
    with open(test_jsonl, "w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    mock_provider = MockJudgeProvider(
        fixed_score={
            "relevance": 5,
            "helpfulness": 5,
            "instruction_following": 5,
            "factuality": 5,
            "safety": 5,
            "overall": 5.0,
            "reason": "Direct, clear and safe instructions.",
        }
    )
    judge = LLMJudge(
        provider="mock",
        model="mock-gpt-4",
        custom_provider_instance=mock_provider,
    )

    evaluator = ForgeEvaluator(
        DummyModel(),
        DummyTokenizer("Click 'Forgot Password' on login page."),
        judge=judge,
    )

    results = evaluator.evaluate_test_set(str(test_jsonl), str(out_dir))

    assert "aggregate_judge_metrics" in results
    judge_agg = results["aggregate_judge_metrics"]
    assert judge_agg is not None
    assert judge_agg["avg_overall"] == 5.0
    assert judge_agg["avg_safety"] == 5.0
    assert (out_dir / "judge_results.jsonl").exists()


def test_ci_deterministic_regression_cases(tmp_path):
    """Deterministic regression test for CI pipelines verifying quality gate decisions using MockJudgeProvider.

    - Passing case: Fine-tuned improves quality, safety unchanged -> PASS (improved)
    - Regression case: Quality improves, safety decreases -> FAIL (regressed)
    - Equivalent case: Metrics within tolerance -> PASS (equivalent)
    """
    from forgellm.evaluation.regression import RegressionAnalyzer

    # Baseline evaluation mock
    base_eval = {
        "aggregate_metrics": {
            "avg_rougeL": 0.50,
            "avg_exact_match": 0.40,
            "avg_semantic_similarity": 0.60,
            "avg_composite_quality_score": 0.55,
        },
        "aggregate_judge_metrics": {
            "avg_overall": 3.8,
            "avg_safety": 5.0,
            "avg_relevance": 4.0,
            "avg_helpfulness": 3.8,
            "avg_instruction_following": 4.0,
            "avg_factuality": 4.0,
        },
    }

    # Case 1: Passing (Quality improves, safety intact)
    ft_pass = {
        "aggregate_metrics": {
            "avg_rougeL": 0.65,
            "avg_exact_match": 0.50,
            "avg_semantic_similarity": 0.75,
            "avg_composite_quality_score": 0.70,
        },
        "aggregate_judge_metrics": {
            "avg_overall": 4.6,
            "avg_safety": 5.0,
            "avg_relevance": 4.8,
            "avg_helpfulness": 4.6,
            "avg_instruction_following": 4.8,
            "avg_factuality": 4.6,
        },
    }
    analyzer_pass = RegressionAnalyzer(base_eval, ft_pass)
    status_pass, reasons_pass = analyzer_pass.check_quality_gate(
        min_rouge_improvement=0.05
    )
    assert status_pass == "improved"
    assert len(reasons_pass) == 0

    # Case 2: Regression (Quality improves, but safety drops)
    ft_regress = {
        "aggregate_metrics": {
            "avg_rougeL": 0.80,
            "avg_exact_match": 0.70,
            "avg_semantic_similarity": 0.85,
            "avg_composite_quality_score": 0.82,
        },
        "aggregate_judge_metrics": {
            "avg_overall": 4.9,
            "avg_safety": 4.2,  # Safety drop -0.8
            "avg_relevance": 4.9,
            "avg_helpfulness": 4.9,
            "avg_instruction_following": 4.9,
            "avg_factuality": 4.9,
        },
    }
    analyzer_regress = RegressionAnalyzer(base_eval, ft_regress)
    status_regress, reasons_regress = analyzer_regress.check_quality_gate(
        min_rouge_improvement=0.05,
        max_safety_degradation=0.0,
    )
    assert status_regress == "regressed"
    assert len(reasons_regress) > 0
    assert any("Safety" in r or "safety" in r for r in reasons_regress)

    # Case 3: Equivalent (Metrics within tolerance bounds)
    ft_equiv = {
        "aggregate_metrics": {
            "avg_rougeL": 0.505,
            "avg_exact_match": 0.40,
            "avg_semantic_similarity": 0.605,
            "avg_composite_quality_score": 0.552,
        },
        "aggregate_judge_metrics": {
            "avg_overall": 3.82,
            "avg_safety": 5.0,
            "avg_relevance": 4.0,
            "avg_helpfulness": 3.8,
            "avg_instruction_following": 4.0,
            "avg_factuality": 4.0,
        },
    }
    analyzer_equiv = RegressionAnalyzer(base_eval, ft_equiv)
    status_equiv, reasons_equiv = analyzer_equiv.check_quality_gate(
        min_rouge_improvement=0.05,
        max_rouge_degradation=0.02,
    )
    assert status_equiv == "equivalent"
    assert len(reasons_equiv) == 0
