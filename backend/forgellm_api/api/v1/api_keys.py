from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets
import hashlib
from datetime import datetime, timezone
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.db.models.user import User, APIKey
from backend.forgellm_api.db.models.organization import OrganizationMember
from backend.forgellm_api.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreateResponse
from backend.forgellm_api.api.dependencies.auth import get_current_user

router = APIRouter()

def generate_api_key():
    secret = secrets.token_hex(32)
    key = f"sk-forgellm-{secret}"
    return key

@router.post("/", response_model=APIKeyCreateResponse)
def create_api_key(
    key_in: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify user has ADMIN or OWNER rights in organization
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == key_in.organization_id,
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not membership or membership.role not in ["OWNER", "ADMIN", "DEVELOPER"]:
        raise HTTPException(status_code=403, detail="Not authorized to create API keys in this organization")

    raw_key = generate_api_key()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:15] + "..."
    
    api_key = APIKey(
        name=key_in.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=key_in.scopes,
        organization_id=key_in.organization_id,
        project_id=key_in.project_id,
        created_by=current_user.id
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return APIKeyCreateResponse(key=api_key, secret=raw_key)

@router.get("/", response_model=List[APIKeyResponse])
def list_api_keys(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify membership
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
        
    keys = db.query(APIKey).filter(APIKey.organization_id == organization_id).all()
    return keys

@router.post("/{key_id}/revoke", response_model=APIKeyResponse)
def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
        
    # Verify membership
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == api_key.organization_id,
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not membership or membership.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized to revoke API keys")
        
    api_key.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(api_key)
    
    return api_key
