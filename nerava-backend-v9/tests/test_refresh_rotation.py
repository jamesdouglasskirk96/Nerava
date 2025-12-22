"""
Test refresh token rotation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

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
        email="refresh_test@example.com",
        auth_provider="local",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_refresh_rotates_token(test_user, db: Session):
    """Test that refresh rotates token (old revoked, new created)"""
    # Create initial refresh token
    old_plain_token, old_refresh_token = RefreshTokenService.create_refresh_token(db, test_user)
    db.commit()
    
    # Refresh token
    response = client.post("/auth/refresh", json={
        "refresh_token": old_plain_token
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    new_plain_token = data["refresh_token"]
    
    # Verify old token is revoked
    db.refresh(old_refresh_token)
    assert old_refresh_token.revoked == True
    assert old_refresh_token.replaced_by is not None
    
    # Verify new token exists
    new_refresh_token = RefreshTokenService.validate_refresh_token(db, new_plain_token)
    assert new_refresh_token is not None
    assert new_refresh_token.revoked == False


def test_refresh_reuse_detected(test_user, db: Session):
    """Test that reuse of revoked refresh token returns 401 + refresh_reuse_detected"""
    # Create and use refresh token
    old_plain_token, old_refresh_token = RefreshTokenService.create_refresh_token(db, test_user)
    db.commit()
    
    # First refresh (should succeed)
    response1 = client.post("/auth/refresh", json={
        "refresh_token": old_plain_token
    })
    assert response1.status_code == 200
    
    # Try to reuse old token (should fail)
    response2 = client.post("/auth/refresh", json={
        "refresh_token": old_plain_token
    })
    
    assert response2.status_code == 401
    assert "refresh_reuse_detected" in response2.headers.get("X-Error-Code", "")


def test_refresh_expired_token(test_user, db: Session):
    """Test refresh with expired token returns 401"""
    # Create expired refresh token
    from app.core.security import generate_refresh_token, hash_refresh_token
    plain_token = generate_refresh_token()
    token_hash = hash_refresh_token(plain_token)
    
    expired_token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
        revoked=False
    )
    db.add(expired_token)
    db.commit()
    
    # Try to refresh
    response = client.post("/auth/refresh", json={
        "refresh_token": plain_token
    })
    
    assert response.status_code == 401

