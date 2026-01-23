"""
Test Google SSO authentication
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.main_simple import app
from app.models import User
from app.core.config import settings

client = TestClient(app)


@pytest.fixture
def mock_google_verify():
    """Mock Google ID token verification"""
    with patch('app.services.google_auth.verify_google_id_token') as mock:
        yield mock


def test_google_login_new_user(mock_google_verify, db: Session):
    """Test Google login creates new user"""
    mock_google_verify.return_value = {
        "sub": "google_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "email_verified": True
    }
    
    response = client.post("/auth/google", json={
        "id_token": "fake_google_token"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["auth_provider"] == "google"
    assert data["user"]["email"] == "test@example.com"
    
    # Verify user was created
    user = db.query(User).filter(User.provider_sub == "google_user_123").first()
    assert user is not None
    assert user.email == "test@example.com"
    assert user.auth_provider == "google"


def test_google_login_existing_user(mock_google_verify, db: Session):
    """Test Google login with existing user"""
    import uuid
    # Create existing user
    existing_user = User(
        public_id=str(uuid.uuid4()),
        email="existing@example.com",
        auth_provider="google",
        provider_sub="google_user_123",
        is_active=True
    )
    db.add(existing_user)
    db.commit()
    
    mock_google_verify.return_value = {
        "sub": "google_user_123",
        "email": "existing@example.com",
        "email_verified": True
    }
    
    response = client.post("/auth/google", json={
        "id_token": "fake_google_token"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["public_id"] == existing_user.public_id


def test_google_login_me_endpoint(mock_google_verify, db: Session):
    """Test /me endpoint returns correct user after Google login"""
    mock_google_verify.return_value = {
        "sub": "google_user_456",
        "email": "me@example.com",
        "email_verified": True
    }
    
    # Login
    login_response = client.post("/auth/google", json={
        "id_token": "fake_google_token"
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    
    # Get /me
    me_response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["auth_provider"] == "google"
    assert data["email"] == "me@example.com"


def test_google_login_not_configured():
    """Test Google login returns 503 when not configured"""
    with patch.object(settings, 'GOOGLE_CLIENT_ID', ''):
        response = client.post("/auth/google", json={
            "id_token": "fake_token"
        })
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()








