import pytest
from fastapi.testclient import TestClient

from backend.forgellm_api.main import app
from forgellm.evaluation.evaluator import ForgeEvaluator
from forgellm.models.exporter import ModelExporter

client = TestClient(app)


def test_evaluator_semantic_metrics():
    # Test evaluation metrics calculation with semantic similarity and composite quality score
    class DummyTokenizer:
        def decode(self, *args, **kwargs):
            return "Hello world"

    class DummyModel:
        device = "cpu"

    evaluator = ForgeEvaluator(DummyModel(), DummyTokenizer())
    metrics = evaluator.compute_metrics(
        expected="I understand that is frustrating. Let me check your account.",
        generated="I understand that is frustrating. I will check your account.",
    )

    assert "exact_match" in metrics
    assert "rougeL" in metrics
    assert "semantic_similarity" in metrics
    assert "composite_quality_score" in metrics
    assert metrics["semantic_similarity"] > 0.5
    assert 0.0 <= metrics["composite_quality_score"] <= 1.0


def test_telemetry_stream_endpoint():
    response = client.get("/api/v1/telemetry/stream/job_123")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
