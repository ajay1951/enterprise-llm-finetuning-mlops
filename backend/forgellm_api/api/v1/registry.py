from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.forgellm_api.db.models.model import ModelPromotionHistory, ModelVersion
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.schemas.registry import (
    ArchiveModelRequest,
    PromoteModelRequest,
    RollbackModelRequest,
)
from backend.forgellm_api.services.event_service import event_service

router = APIRouter(prefix="/models", tags=["Model Registry"])


@router.post("/{model_id}/versions/{version_id}/promote")
def promote_model_version(
    model_id: str,
    version_id: str,
    request: PromoteModelRequest,
    db: Session = Depends(get_db),
):
    version = (
        db.query(ModelVersion)
        .filter(ModelVersion.id == version_id, ModelVersion.model_id == model_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")

    valid_transitions = {
        "development": ["staging", "archived", "rejected"],
        "staging": ["production", "development", "archived"],
        "production": ["archived", "staging"],
        "rejected": ["development", "archived"],
        "archived": ["development"],
    }

    current = version.lifecycle_status
    target = request.new_status

    if target not in valid_transitions.get(current, []):
        raise HTTPException(
            status_code=400, detail=f"Invalid transition from {current} to {target}"
        )

    # Example Quality Gate enforcement: Prevent production promotion if quality_score is absent/failed
    if target == "production":
        if not version.quality_score:
            raise HTTPException(
                status_code=400,
                detail="Cannot promote to production: Missing quality gate evaluation",
            )
        import json

        try:
            q_score = json.loads(version.quality_score)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Cannot promote to production: Invalid quality score format",
            )

        if not q_score.get("passed", False):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot promote to production: Quality gate failed. Reasons: {q_score.get('reasons')}",
            )

    # Audit log
    audit = ModelPromotionHistory(
        model_version_id=version_id,
        previous_status=current,
        new_status=target,
        actor="user",  # Replace with actual auth user
        reason=request.reason,
    )
    db.add(audit)

    version.lifecycle_status = target
    db.commit()

    event_service.publish_log(db, version_id, 1, "INFO", f"Model promoted to {target}")

    return {"message": f"Successfully promoted to {target}", "new_status": target}


@router.post("/{model_id}/rollback")
def rollback_model(
    model_id: str, request: RollbackModelRequest, db: Session = Depends(get_db)
):
    # Find current production version
    current_prod = (
        db.query(ModelVersion)
        .filter(
            ModelVersion.model_id == model_id,
            ModelVersion.lifecycle_status == "production",
        )
        .first()
    )

    target_version = (
        db.query(ModelVersion)
        .filter(
            ModelVersion.id == request.target_version_id,
            ModelVersion.model_id == model_id,
        )
        .first()
    )

    if not target_version:
        raise HTTPException(status_code=404, detail="Target version not found")

    if current_prod and current_prod.id == target_version.id:
        raise HTTPException(
            status_code=400, detail="Target version is already the production version"
        )

    if current_prod:
        # Demote current prod
        audit_demote = ModelPromotionHistory(
            model_version_id=current_prod.id,
            previous_status="production",
            new_status="archived",
            actor="user",
            reason=f"Rolled back to {target_version.version_tag}: {request.reason}",
        )
        db.add(audit_demote)
        current_prod.lifecycle_status = "archived"

    # Promote target
    audit_promote = ModelPromotionHistory(
        model_version_id=target_version.id,
        previous_status=target_version.lifecycle_status,
        new_status="production",
        actor="user",
        reason=f"Rollback operation: {request.reason}",
    )
    db.add(audit_promote)
    target_version.lifecycle_status = "production"

    db.commit()

    return {"message": "Rollback successful"}


@router.post("/{model_id}/versions/{version_id}/archive")
def archive_model_version(
    model_id: str,
    version_id: str,
    request: ArchiveModelRequest,
    db: Session = Depends(get_db),
):
    version = (
        db.query(ModelVersion)
        .filter(ModelVersion.id == version_id, ModelVersion.model_id == model_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")

    if version.lifecycle_status == "production":
        raise HTTPException(
            status_code=400,
            detail="Cannot archive active production version. Demote it first.",
        )

    audit = ModelPromotionHistory(
        model_version_id=version_id,
        previous_status=version.lifecycle_status,
        new_status="archived",
        actor="user",
        reason=request.reason,
    )
    db.add(audit)

    version.lifecycle_status = "archived"
    db.commit()

    return {"message": "Version archived"}
