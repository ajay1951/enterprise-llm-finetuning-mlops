from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from backend.forgellm_api.api.dependencies.auth import get_current_user, require_role
from backend.forgellm_api.core.audit import AuditLogger
from backend.forgellm_api.core.config import get_settings
from backend.forgellm_api.db.models.project import Project
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.schemas.dataset import DatasetResponse
from backend.forgellm_api.services.dataset_service import DatasetService
from backend.forgellm_api.storage.local import LocalStorage

router = APIRouter(tags=["Datasets"], prefix="/projects/{project_id}/datasets")


def get_storage():
    settings = get_settings()
    return LocalStorage(settings.DATASET_ROOT)


@router.post("/", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def upload_dataset(
    request: Request,
    project_id: str,
    organization_id: str = "org_default",
    name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: LocalStorage = Depends(get_storage),
    membership=Depends(require_role(["OWNER", "ADMIN", "DEVELOPER"])),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.organization_id == organization_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=404, detail="Project not found in this organization"
        )

    service = DatasetService(db, storage)
    dataset = service.create_dataset_and_upload(project_id, name, description, file)

    AuditLogger.log(
        db=db,
        action="dataset.upload",
        organization_id=organization_id,
        project_id=project_id,
        user_id=membership.user_id,
        resource_type="Dataset",
        resource_id=dataset.id,
        request=request,
    )
    return dataset


@router.get("/", response_model=list[DatasetResponse])
def get_datasets(
    project_id: str,
    organization_id: str = "org_default",
    db: Session = Depends(get_db),
    storage: LocalStorage = Depends(get_storage),
    membership=Depends(require_role(["OWNER", "ADMIN", "DEVELOPER", "VIEWER"])),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.organization_id == organization_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=404, detail="Project not found in this organization"
        )

    service = DatasetService(db, storage)
    return service.get_datasets(project_id)
