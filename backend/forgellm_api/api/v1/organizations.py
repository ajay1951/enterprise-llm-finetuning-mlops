from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from slugify import slugify
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.db.models.organization import Organization, OrganizationMember
from backend.forgellm_api.db.models.user import User
from backend.forgellm_api.schemas.organization import OrganizationCreate, OrganizationResponse
from backend.forgellm_api.api.dependencies.auth import get_current_user, require_role

router = APIRouter()

@router.post("/", response_model=OrganizationResponse)
def create_organization(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    slug = slugify(org_in.name)
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        slug = f"{slug}-{current_user.id[:6]}"
        
    org = Organization(name=org_in.name, slug=slug)
    db.add(org)
    db.flush()
    
    # Creator is OWNER
    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role="OWNER"
    )
    db.add(member)
    db.commit()
    db.refresh(org)
    return org

@router.get("/", response_model=List[OrganizationResponse])
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).all()
    org_ids = [m.organization_id for m in memberships]
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all()
    return orgs

@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: str,
    membership = Depends(require_role(["OWNER", "ADMIN", "DEVELOPER", "VIEWER"])),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org
