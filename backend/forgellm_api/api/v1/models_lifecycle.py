import os
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.forgellm_api.core.security import get_current_user
from backend.forgellm_api.db.models.audit import AuditLog
from backend.forgellm_api.db.models.model import Model, ModelVersion
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.schemas.model import ModelImportRequest, ModelResponse

router = APIRouter(tags=["Model Lifecycle"])


@router.post(
    "/api/v1/projects/{project_id}/models/import", response_model=ModelResponse
)
def import_local_model(
    project_id: str,
    import_req: ModelImportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not os.path.exists(import_req.local_path):
        raise HTTPException(
            status_code=400,
            detail=f"Local path does not exist: {import_req.local_path}",
        )

    model = db.query(Model).filter(Model.name == import_req.name).first()
    if not model:
        model = Model(
            project_id=project_id,
            name=import_req.name,
            description="Imported from local path",
        )
        db.add(model)
        db.flush()

    version = ModelVersion(
        model_id=model.id,
        version_tag="v1.0",
        base_model=import_req.base_model,
        adapter_path="",  # Since it might be a full model
        artifact_uri=import_req.local_path,
        lifecycle_status="READY",
    )
    db.add(version)

    audit = AuditLog(
        organization_id=current_user.get("organization_id"),
        user_id=current_user.get("user_id"),
        action=f"Imported model {model.name} from {import_req.local_path}",
        resource_type="model_version",
        resource_id=version.id,
        ip_address="127.0.0.1",  # Mock
    )
    db.add(audit)
    db.commit()
    db.refresh(model)
    return model


@router.get("/api/v1/projects/{project_id}/models", response_model=list[ModelResponse])
def get_models_by_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    models = db.query(Model).filter(Model.project_id == project_id).all()
    return models


@router.post("/api/v1/models/{version_id}/promote")
def promote_model(
    version_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not version:
        raise HTTPException(404, "Model version not found")

    old_status = version.lifecycle_status
    if old_status == "STAGED":
        version.lifecycle_status = "PRODUCTION"
    elif old_status == "READY":
        version.lifecycle_status = "STAGED"
    else:
        raise HTTPException(400, f"Cannot promote from status {old_status}")

    audit = AuditLog(
        organization_id=current_user.get("organization_id"),
        user_id=current_user.get("user_id"),
        action=f"Promoted model {version.model_id} from {old_status} to {version.lifecycle_status}",
        resource_type="model_version",
        resource_id=version.id,
        ip_address="127.0.0.1",  # Mock
    )
    db.add(audit)
    db.commit()

    return {"id": version.id, "lifecycle_status": version.lifecycle_status}


@router.post("/api/v1/models/{version_id}/rollback")
def rollback_model(
    version_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not version:
        raise HTTPException(404, "Model version not found")

    old_status = version.lifecycle_status
    if old_status == "PRODUCTION":
        version.lifecycle_status = "STAGED"
    elif old_status == "STAGED":
        version.lifecycle_status = "READY"
    else:
        raise HTTPException(400, f"Cannot rollback from status {old_status}")

    audit = AuditLog(
        organization_id=current_user.get("organization_id"),
        user_id=current_user.get("user_id"),
        action=f"Rolled back model {version.model_id} from {old_status} to {version.lifecycle_status}",
        resource_type="model_version",
        resource_id=version.id,
        ip_address="127.0.0.1",  # Mock
    )
    db.add(audit)
    db.commit()

    return {"id": version.id, "lifecycle_status": version.lifecycle_status}
