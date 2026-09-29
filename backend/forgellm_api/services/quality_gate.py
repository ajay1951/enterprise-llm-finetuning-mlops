import logging
import json
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)


class QualityGateService:
    def __init__(self):
        # In a real enterprise system, these would be loaded from a configuration file or database.
        self.default_thresholds = {
            "min_f1_score": 0.80,
            "min_accuracy": 0.85,
            "max_validation_loss": 0.50,
            "max_latency_ms": 500,
            "require_safety_checks": True,
        }

    def evaluate_model(
        self, evaluation_metrics: Dict[str, Any], thresholds: Dict[str, Any] = None
    ) -> Tuple[bool, str, List[str]]:
        """
        Evaluate a model's metrics against configured thresholds.
        Returns:
            Tuple[is_passing: bool, status: str, reasons: List[str]]
        """
        config = thresholds if thresholds else self.default_thresholds
        reasons = []
        is_passing = True

        # Check F1 Score
        if "f1_score" in evaluation_metrics:
            if evaluation_metrics["f1_score"] < config.get("min_f1_score", 0):
                is_passing = False
                reasons.append(
                    f"F1 score {evaluation_metrics['f1_score']} is below minimum threshold of {config.get('min_f1_score')}"
                )

        # Check Accuracy
        if "accuracy" in evaluation_metrics:
            if evaluation_metrics["accuracy"] < config.get("min_accuracy", 0):
                is_passing = False
                reasons.append(
                    f"Accuracy {evaluation_metrics['accuracy']} is below minimum threshold of {config.get('min_accuracy')}"
                )

        # Check Validation Loss
        if "validation_loss" in evaluation_metrics:
            if evaluation_metrics["validation_loss"] > config.get(
                "max_validation_loss", 999
            ):
                is_passing = False
                reasons.append(
                    f"Validation loss {evaluation_metrics['validation_loss']} is above maximum threshold of {config.get('max_validation_loss')}"
                )

        # Safety checks
        if config.get("require_safety_checks", False):
            if not evaluation_metrics.get("safety_passed", False):
                is_passing = False
                reasons.append("Safety evaluation failed or was not performed.")

        if not reasons and is_passing:
            reasons.append("All quality gate metrics passed successfully.")

        status = "PASS" if is_passing else "FAIL"

        return is_passing, status, reasons

    def generate_quality_score_json(
        self, is_passing: bool, status: str, reasons: List[str]
    ) -> str:
        return json.dumps({"passed": is_passing, "status": status, "reasons": reasons})


quality_gate = QualityGateService()
