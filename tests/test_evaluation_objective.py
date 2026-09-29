import json
import os

import pytest

from forgellm.evaluation.evaluator import ForgeEvaluator


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


def test_exact_match_metric():
    evaluator = ForgeEvaluator(DummyModel(), DummyTokenizer())

    # Identical strings
    m1 = evaluator.compute_metrics("Hello world", "Hello world")
    assert m1["exact_match"] == 1.0

    # Whitespace normalization
    m2 = evaluator.compute_metrics("  Hello world \n", "Hello world")
    assert m2["exact_match"] == 1.0

    # Differing strings
    m3 = evaluator.compute_metrics("Hello world", "Hello universe")
    assert m3["exact_match"] == 0.0


def test_rouge_and_semantic_similarity():
    evaluator = ForgeEvaluator(DummyModel(), DummyTokenizer())

    expected = "The quick brown fox jumps over the lazy dog"
    generated = "The fast brown fox leaps over a lazy dog"

    metrics = evaluator.compute_metrics(expected, generated)

    assert "rougeL" in metrics
    assert "semantic_similarity" in metrics
    assert 0.0 < metrics["rougeL"] <= 1.0
    assert 0.0 < metrics["semantic_similarity"] <= 1.0
    assert "composite_quality_score" in metrics
    assert 0.0 <= metrics["composite_quality_score"] <= 1.0


def test_empty_and_whitespace_inputs():
    evaluator = ForgeEvaluator(DummyModel(), DummyTokenizer())

    # Empty strings
    m_empty = evaluator.compute_metrics("", "")
    assert m_empty["exact_match"] == 1.0
    assert m_empty["semantic_similarity"] == 1.0
    assert m_empty["composite_quality_score"] == 1.0

    # One empty, one non-empty
    m_diff = evaluator.compute_metrics("expected answer", "")
    assert m_diff["exact_match"] == 0.0
    assert m_diff["semantic_similarity"] == 0.0
    assert m_diff["composite_quality_score"] == 0.0


def test_evaluator_test_set_execution(tmp_path):
    test_jsonl = tmp_path / "test.jsonl"
    out_dir = tmp_path / "eval_output"

    records = [
        {
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello there"},
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "What is 2+2?"},
                {"role": "assistant", "content": "It is 4"},
            ]
        },
        {"malformed": "invalid_line"},  # Malformed line to test graceful skipping
    ]

    with open(test_jsonl, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in records)

    tokenizer = DummyTokenizer(fixed_output="Hello there")
    evaluator = ForgeEvaluator(DummyModel(), tokenizer)
    results = evaluator.evaluate_test_set(str(test_jsonl), str(out_dir))

    assert results["aggregate_metrics"]["total_samples"] == 2
    assert "avg_exact_match" in results["aggregate_metrics"]
    assert "avg_rougeL" in results["aggregate_metrics"]
    assert "avg_semantic_similarity" in results["aggregate_metrics"]
    assert "avg_composite_quality_score" in results["aggregate_metrics"]

    # Verify generated artifact files exist
    assert (out_dir / "evaluation_results.json").exists()
    assert (out_dir / "metrics.json").exists()
    assert (out_dir / "predictions.jsonl").exists()
    assert (out_dir / "report.md").exists()
    assert (out_dir / "baseline_report.md").exists()


def test_deterministic_output():
    evaluator1 = ForgeEvaluator(DummyModel(), DummyTokenizer("Consistent response"))
    evaluator2 = ForgeEvaluator(DummyModel(), DummyTokenizer("Consistent response"))

    m1 = evaluator1.compute_metrics("Reference text", "Consistent response")
    m2 = evaluator2.compute_metrics("Reference text", "Consistent response")

    assert m1 == m2
