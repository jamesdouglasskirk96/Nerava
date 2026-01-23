"""
Tests for auth endpoint error paths.

Critical for security: invalid tokens, expired tokens, malformed requests.
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient
from app.core.config import settings


def test_auth_invalid_token_format(client: TestClient):
    """Test that malformed token is rejected."""
    response = client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"}
    )
    assert response.status_code == 401


def test_auth_expired_token(client: TestClient):
    """Test that expired token is rejected."""
    # Create expired token
    expire = datetime.utcnow() - timedelta(hours=1)
    payload = {
        "sub": "123",
        "exp": expire
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    response = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_auth_missing_token(client: TestClient):
    """Test that request without token is rejected."""
    response = client.get("/v1/auth/me")
    assert response.status_code == 401


def test_auth_wrong_secret_token(client: TestClient):
    """Test that token signed with wrong secret is rejected."""
    wrong_secret = "wrong-secret-key"
    payload = {
        "sub": "123",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, wrong_secret, algorithm=settings.ALGORITHM)
    
    response = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_auth_login_invalid_credentials(client: TestClient, db):
    """Test that login with invalid credentials fails."""
    response = client.post(
        "/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower() or "credentials" in response.json()["detail"].lower()


def test_auth_register_duplicate_email(client: TestClient, db):
    """Test that registering with existing email fails."""
    email = "duplicate@example.com"
    
    # First registration
    response1 = client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "password": "password123"
        }
    )
    
    # Second registration with same email
    response2 = client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "password": "password456"
        }
    )
    
    # One should succeed, one should fail
    assert response1.status_code in [200, 201] or response2.status_code in [400, 409]
    if response1.status_code in [200, 201]:
        assert response2.status_code in [400, 409]


def test_auth_magic_link_invalid_token(client: TestClient):
    """Test that magic link with invalid token fails."""
    response = client.post(
        "/v1/auth/magic_link/verify",
        json={"token": "invalid-token-123"}
    )
    assert response.status_code == 401


def test_auth_magic_link_expired_token(client: TestClient):
    """Test that expired magic link token is rejected."""
    # Create expired magic link token
    expire = datetime.utcnow() - timedelta(minutes=20)  # Expired (15 min expiry)
    payload = {
        "sub": "123",
        "email": "test@example.com",
        "purpose": "magic_link",
        "exp": expire
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    response = client.post(
        "/v1/auth/magic_link/verify",
        json={"token": token}
    )
    assert response.status_code == 401


def test_auth_magic_link_wrong_purpose(client: TestClient):
    """Test that token with wrong purpose is rejected."""
    expire = datetime.utcnow() + timedelta(minutes=10)
    payload = {
        "sub": "123",
        "email": "test@example.com",
        "purpose": "wrong_purpose",  # Not "magic_link"
        "exp": expire
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    response = client.post(
        "/v1/auth/magic_link/verify",
        json={"token": token}
    )
    assert response.status_code == 401







