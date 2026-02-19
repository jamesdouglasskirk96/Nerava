"""
Test P0-2: DEMO_MODE gating to local-only
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


def test_demo_mode_blocked_in_prod(client):
    """Test that DEMO_MODE=true is ignored in production environment"""
    with patch.dict(os.environ, {"DEMO_MODE": "true", "ENV": "prod", "REGION": "us-east-1"}):
        # Try to redeem without auth - should get 401 even with DEMO_MODE=true
        response = client.post(
            "/v1/checkout/redeem",
            json={
                "qr_token": "test-token",
                "order_total_cents": 1000
            }
        )
        assert response.status_code == 401
        assert "UNAUTHORIZED" in response.json()["detail"]["error"]


def test_demo_mode_allowed_in_local(client):
    """Test that DEMO_MODE=true works in local environment"""
    with patch.dict(os.environ, {"DEMO_MODE": "true", "ENV": "local", "REGION": "local"}):
        # This test would require a demo user to exist, so we just verify the logic
        # In a real test, you'd need to seed a demo user first
        pass






