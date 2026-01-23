"""
Test logout revokes refresh tokens
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main_simple import app
from app.models import User, RefreshToken
from app.services.refresh_token_service import RefreshTokenService
from app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    import uuid
    user = User(
        public_id=str(uuid.uuid4()),
        email="logout_test@example.com",
        auth_provider="local",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_logout_revokes_token(test_user, db: Session):
    """Test logout revokes refresh token"""
    # Create refresh token
    plain_token, refresh_token = RefreshTokenService.create_refresh_token(db, test_user)
    db.commit()
    
    # Logout
    response = client.post("/auth/logout", json={
        "refresh_token": plain_token
    })
    
    assert response.status_code == 200
    assert response.json()["ok"] == True
    
    # Verify token is revoked
    db.refresh(refresh_token)
    assert refresh_token.revoked == True


def test_logout_revoked_token_cannot_refresh(test_user, db: Session):
    """Test revoked token cannot be used for refresh"""
    # Create refresh token
    plain_token, refresh_token = RefreshTokenService.create_refresh_token(db, test_user)
    db.commit()
    
    # Logout (revoke token)
    client.post("/auth/logout", json={
        "refresh_token": plain_token
    })
    
    # Try to refresh with revoked token
    response = client.post("/auth/refresh", json={
        "refresh_token": plain_token
    })
    
    assert response.status_code == 401








