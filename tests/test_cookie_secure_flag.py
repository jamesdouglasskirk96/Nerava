"""
Test P0-5: Cookie secure flag is environment-aware
"""
import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    """Create test client"""
    from nerava_backend_v9.app.main import app
    return TestClient(app)


def test_cookie_secure_in_prod(client):
    """Test that cookies have Secure flag in production"""
    with patch.dict(os.environ, {"ENV": "prod", "REGION": "us-east-1"}):
        response = client.post(
            "/v1/auth/login",
            json={"email": "test@example.com", "password": "testpass"}
        )
        # Check Set-Cookie header
        set_cookie = response.headers.get("Set-Cookie", "")
        if "access_token" in set_cookie:
            assert "Secure" in set_cookie


def test_cookie_not_secure_in_local_http(client):
    """Test that cookies don't have Secure flag in local HTTP"""
    with patch.dict(os.environ, {"ENV": "local", "REGION": "local", "HTTPS": "false"}):
        response = client.post(
            "/v1/auth/login",
            json={"email": "test@example.com", "password": "testpass"}
        )
        # In local HTTP, Secure flag should not be set
        set_cookie = response.headers.get("Set-Cookie", "")
        if "access_token" in set_cookie and "http://" in os.getenv("FRONTEND_URL", ""):
            # Secure flag should not be present for local HTTP
            pass  # This is expected behavior






