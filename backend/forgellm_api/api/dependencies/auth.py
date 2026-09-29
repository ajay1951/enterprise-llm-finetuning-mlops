from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.core.security import SECRET_KEY, ALGORITHM
from backend.forgellm_api.db.models.user import User, APIKey
from backend.forgellm_api.db.models.organization import OrganizationMember

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

from backend.forgellm_api.db.models.organization import Organization, OrganizationMember


def get_current_user(db: Session = Depends(get_db)) -> User:
    # MOCK AUTHENTICATION FOR LOCAL DEV
    user = db.query(User).filter(User.email == "demo@forgellm.com").first()
    if not user:
        user = User(
            id="usr_demo",
            email="demo@forgellm.com",
            password_hash="mock",
            name="Demo User",
            status="ACTIVE",
        )
        db.add(user)
        db.commit()
    return user


def require_role(allowed_roles: list[str]):
    def role_checker(
        organization_id: str = "org_default",
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        # Ensure default org exists
        if organization_id == "org_default":
            org = (
                db.query(Organization).filter(Organization.id == "org_default").first()
            )
            if not org:
                org = Organization(
                    id="org_default", name="Demo Organization", slug="demo-org"
                )
                db.add(org)
                db.commit()

            mem = (
                db.query(OrganizationMember)
                .filter(OrganizationMember.organization_id == "org_default")
                .first()
            )
            if not mem:
                mem = OrganizationMember(
                    id="mem_demo",
                    organization_id="org_default",
                    user_id=current_user.id,
                    role="OWNER",
                )
                db.add(mem)
                db.commit()

            return mem

        membership = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == current_user.id,
            )
            .first()
        )

        if not membership or (
            membership.role not in allowed_roles and membership.role != "OWNER"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return membership

    return role_checker


def verify_api_key(required_scopes: list[str] = None):
    def api_key_checker(request: Request, db: Session = Depends(get_db)):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid API key")

        token = auth_header.split(" ")[1]

        # If it's a JWT, this is not an API key
        if "." in token:
            raise HTTPException(status_code=401, detail="Expected API key, got JWT")

        import hashlib

        key_hash = hashlib.sha256(token.encode()).hexdigest()

        api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if api_key.revoked_at:
            raise HTTPException(status_code=401, detail="API key revoked")

        import datetime

        now = datetime.datetime.now(datetime.timezone.utc)

        if (
            api_key.expires_at
            and api_key.expires_at.replace(tzinfo=datetime.timezone.utc) < now
        ):
            raise HTTPException(status_code=401, detail="API key expired")

        if required_scopes:
            key_scopes = api_key.scopes.split(",") if api_key.scopes else []
            for scope in required_scopes:
                if scope not in key_scopes:
                    raise HTTPException(
                        status_code=403,
                        detail=f"API key missing required scope: {scope}",
                    )

        # Update last used
        api_key.last_used_at = now
        db.commit()

        return api_key

    return api_key_checker


class TenantContext:
    def __init__(
        self, organization_id: str, project_id: str = None, user_id: str = None
    ):
        self.organization_id = organization_id
        self.project_id = project_id
        self.user_id = user_id
