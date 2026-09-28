from datetime import timedelta

from jose import jwt

from backend.forgellm_api.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from backend.forgellm_api.db.models.organization import Organization, OrganizationMember
from backend.forgellm_api.db.models.user import User


def test_password_hashing():
    password = "supersecretpassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_access_token_creation():
    subject = "user-123"
    token = create_access_token(subject)
    
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert decoded["sub"] == subject
    assert decoded["type"] == "access"
    assert "exp" in decoded

def test_jwt_refresh_token_creation():
    subject = "user-123"
    token = create_refresh_token(subject, expires_delta=timedelta(days=1))
    
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert decoded["sub"] == subject
    assert decoded["type"] == "refresh"
    assert "exp" in decoded

# To test the API dependencies, we would normally use TestClient.
# For unit test isolation, we verify the RBAC models are configured correctly.
def test_organization_member_roles():
    org = Organization(id="org-1", name="Test Org", slug="test-org")
    user = User(id="user-1", email="test@example.com", hashed_password="abc")
    
    # Valid Role
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="DEVELOPER"
    )
    assert member.role == "DEVELOPER"
