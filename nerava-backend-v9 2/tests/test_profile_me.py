"""
Test /auth/me endpoint
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main_simple import app
from app.models import User
from app.services.refresh_token_service import RefreshTokenService

client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        auth_provider="local",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user, db: Session):
    """Create auth token for test user"""
    _, refresh_token = RefreshTokenService.create_refresh_token(db, test_user)
    db.commit()
    
    # Get access token by logging in
    from app.core.security import create_access_token
    access_token = create_access_token(test_user.public_id, auth_provider=test_user.auth_provider)
    return access_token


def test_get_me_returns_expected_fields(auth_token, test_user):
    """Test /auth/me returns expected fields"""
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "public_id" in data
    assert "auth_provider" in data
    assert "email" in data
    assert "created_at" in data
    
    # Check values
    assert data["public_id"] == str(test_user.public_id)
    assert data["auth_provider"] == test_user.auth_provider
    assert data["email"] == test_user.email


def test_get_me_requires_auth():
    """Test /auth/me requires authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 401







