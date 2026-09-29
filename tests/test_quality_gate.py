from backend.forgellm_api.services.quality_gate import QualityGateService


def test_quality_gate_pass():
    gate = QualityGateService()
    metrics = {
        "f1_score": 0.85,
        "accuracy": 0.90,
        "validation_loss": 0.40,
        "safety_passed": True,
    }

    passed, status, reasons = gate.evaluate_model(metrics)

    assert passed is True
    assert status == "PASS"
    assert "All quality gate metrics passed successfully." in reasons


def test_quality_gate_fail_f1():
    gate = QualityGateService()
    metrics = {
        "f1_score": 0.70,  # below 0.80
        "accuracy": 0.90,
        "validation_loss": 0.40,
        "safety_passed": True,
    }

    passed, status, reasons = gate.evaluate_model(metrics)

    assert passed is False
    assert status == "FAIL"
    assert any("F1 score" in r for r in reasons)


def test_quality_gate_fail_safety():
    gate = QualityGateService()
    metrics = {
        "f1_score": 0.90,
        "accuracy": 0.90,
        "validation_loss": 0.40,
        "safety_passed": False,
    }

    passed, status, reasons = gate.evaluate_model(metrics)

    assert passed is False
    assert status == "FAIL"
    assert any("Safety" in r for r in reasons)
