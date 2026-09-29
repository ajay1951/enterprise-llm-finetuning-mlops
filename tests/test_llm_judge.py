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
