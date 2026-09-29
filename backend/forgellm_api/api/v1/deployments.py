from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.forgellm_api.api.dependencies.auth import get_current_user, require_role
from backend.forgellm_api.core.audit import AuditLogger
from backend.forgellm_api.db.models.project import Project
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.schemas.deployment import DeploymentCreate, DeploymentResponse
from backend.forgellm_api.services.deployment_service import DeploymentService

router = APIRouter(tags=["Deployments"])


@router.post(
    "/projects/{project_id}/deployments",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deployment(
    request: Request,
    project_id: str,
    deploy_in: DeploymentCreate,
    organization_id: str = "org_default",
    db: Session = Depends(get_db),
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
    service = DeploymentService(db)
    try:
        deployment = service.create_deployment(project_id, deploy_in)
        AuditLogger.log(
            db=db,
            action="deployment.create",
            organization_id=organization_id,
            project_id=project_id,
            user_id=membership.user_id,
            resource_type="Deployment",
            resource_id=deployment.id,
            request=request,
        )
        return deployment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/projects/{project_id}/deployments", response_model=list[DeploymentResponse]
)
def list_project_deployments(
    project_id: str,
    organization_id: str = "org_default",
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
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
    service = DeploymentService(db)
    return service.get_deployments(project_id=project_id, skip=skip, limit=limit)


@router.get("/deployments", response_model=list[DeploymentResponse])
def list_all_deployments(
    organization_id: str = "org_default",
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    membership=Depends(require_role(["OWNER", "ADMIN", "DEVELOPER", "VIEWER"])),
):
    service = DeploymentService(db)
    return service.get_deployments(skip=skip, limit=limit)


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(deployment_id: str, db: Session = Depends(get_db)):
    service = DeploymentService(db)
    deployment = service.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.post("/deployments/{deployment_id}/start", response_model=DeploymentResponse)
def start_deployment(
    request: Request,
    deployment_id: str,
    db: Session = Depends(get_db),
    # In a full implementation, this should verify project access via TenantContext
):
    service = DeploymentService(db)
    try:
        deployment = service.start_deployment(deployment_id)
        # AuditLogger.log(...) omitted for brevity, but same pattern as above
        return deployment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/deployments/{deployment_id}/stop", response_model=DeploymentResponse)
def stop_deployment(deployment_id: str, db: Session = Depends(get_db)):
    service = DeploymentService(db)
    try:
        return service.stop_deployment(deployment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/deployments/{deployment_id}/restart", response_model=DeploymentResponse)
def restart_deployment(deployment_id: str, db: Session = Depends(get_db)):
    service = DeploymentService(db)
    try:
        service.stop_deployment(deployment_id)
        # In a real system, you'd wait for it to fully stop before starting,
        # but for Phase 6 we can just enqueue the start command immediately,
        # or have the frontend poll until stopped before calling start.
        return service.start_deployment(deployment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/deployments/{deployment_id}")
def delete_deployment(deployment_id: str, db: Session = Depends(get_db)):
    service = DeploymentService(db)
    service.delete_deployment(deployment_id)
    return {"status": "success"}


@router.get("/deployments/{deployment_id}/logs")
def get_deployment_logs(
    deployment_id: str, limit: int = 500, db: Session = Depends(get_db)
):
    service = DeploymentService(db)
    return service.get_logs(deployment_id, limit=limit)
