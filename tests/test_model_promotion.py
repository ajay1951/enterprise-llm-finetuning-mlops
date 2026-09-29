import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend.forgellm_api.api.v1.registry import promote_model_version
from backend.forgellm_api.db.models.model import ModelVersion
from backend.forgellm_api.schemas.registry import PromoteModelRequest


def test_promote_model_version_success():
    db = MagicMock()
    version = ModelVersion(
        id="v-1",
        model_id="m-1",
        lifecycle_status="staging",
        quality_score=json.dumps({"passed": True, "reasons": []}),
    )
    db.query().filter().first.return_value = version

    request = PromoteModelRequest(
        new_status="production", reason="Passed all quality and safety gates"
    )
    result = promote_model_version(
        model_id="m-1", version_id="v-1", request=request, db=db
    )

    assert result["new_status"] == "production"
    assert version.lifecycle_status == "production"


def test_promote_model_version_blocked_by_safety_or_quality_gate():
    """CRITICAL: If quality gate failed (e.g. safety drop or regression), promotion to production MUST be blocked."""
    db = MagicMock()
    version = ModelVersion(
        id="v-2",
        model_id="m-1",
        lifecycle_status="staging",
        quality_score=json.dumps(
            {
                "passed": False,
                "reasons": [
                    "Quality Gate Failure: LLM Judge Safety score dropped below baseline."
                ],
            }
        ),
    )
    db.query().filter().first.return_value = version

    request = PromoteModelRequest(
        new_status="production", reason="Trying to promote despite safety failure"
    )

    with pytest.raises(HTTPException) as exc_info:
        promote_model_version(model_id="m-1", version_id="v-2", request=request, db=db)

    assert exc_info.value.status_code == 400
    assert "Cannot promote to production: Quality gate failed" in exc_info.value.detail
    assert version.lifecycle_status == "staging"  # Status unchanged


def test_promote_model_version_blocked_missing_quality_gate():
    db = MagicMock()
    version = ModelVersion(
        id="v-3",
        model_id="m-1",
        lifecycle_status="staging",
        quality_score=None,
    )
    db.query().filter().first.return_value = version

    request = PromoteModelRequest(
        new_status="production", reason="No quality gate evaluation run"
    )

    with pytest.raises(HTTPException) as exc_info:
        promote_model_version(model_id="m-1", version_id="v-3", request=request, db=db)

    assert exc_info.value.status_code == 400
    assert "Missing quality gate evaluation" in exc_info.value.detail
