from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.schemas.project import ProjectCreate, ProjectResponse
from backend.forgellm_api.services.project_service import ProjectService
from backend.forgellm_api.api.dependencies.auth import get_current_user, require_role
from backend.forgellm_api.db.models.user import User
from backend.forgellm_api.core.audit import AuditLogger
from fastapi import Request

router = APIRouter(tags=["Projects"], prefix="/projects")

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: Request,
    project_in: ProjectCreate, 
    db: Session = Depends(get_db),
    membership = Depends(require_role(["OWNER", "ADMIN"]))
):
    # Ensure organization_id is set
    if not project_in.organization_id:
        project_in.organization_id = "org_default"
        
    service = ProjectService(db, project_in.organization_id)
    project = service.create_project(project_in)
    
    AuditLogger.log(
        db=db,
        action="project.create",
        organization_id=project_in.organization_id,
        project_id=project.id,
        user_id=membership.user_id,
        resource_type="Project",
        resource_id=project.id,
        request=request
    )
    return project

@router.get("/", response_model=List[ProjectResponse])
def get_projects(
    organization_id: str = "org_default",
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    membership = Depends(require_role(["OWNER", "ADMIN", "DEVELOPER", "VIEWER"]))
):
    service = ProjectService(db, organization_id)
    return service.get_projects(skip=skip, limit=limit)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str, 
    organization_id: str = "org_default",
    db: Session = Depends(get_db),
    membership = Depends(require_role(["OWNER", "ADMIN", "DEVELOPER", "VIEWER"]))
):
    service = ProjectService(db, organization_id)
    return service.get_project(project_id)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str, 
    organization_id: str = "org_default",
    db: Session = Depends(get_db),
    membership = Depends(require_role(["OWNER", "ADMIN"]))
):
    service = ProjectService(db, organization_id)
    service.delete_project(project_id)
