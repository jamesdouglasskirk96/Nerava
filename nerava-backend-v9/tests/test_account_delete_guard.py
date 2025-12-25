"""
Test account delete endpoint confirmation guard
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
        is_active=True,
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
    
    from app.core.security import create_access_token
    access_token = create_access_token(test_user.public_id, auth_provider=test_user.auth_provider)
    return access_token


def test_delete_account_requires_confirmation(auth_token, test_user):
    """Test DELETE /v1/account requires "DELETE" confirmation"""
    # Try without confirmation
    response = client.delete(
        "/v1/account",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "confirmation": "WRONG"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "CONFIRMATION_REQUIRED" in str(data)


def test_delete_account_with_confirmation(auth_token, test_user, db: Session):
    """Test DELETE /v1/account with correct confirmation"""
    assert test_user.is_active is True
    
    response = client.delete(
        "/v1/account",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "confirmation": "DELETE"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    
    # Verify user is soft-deleted
    db.refresh(test_user)
    assert test_user.is_active is False

