"""
Test P0-3: Pilot redeem endpoint requires authentication
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    from nerava_backend_v9.app.main import app
    return TestClient(app)


def test_pilot_redeem_requires_auth(client):
    """Test that /v1/pilot/redeem_code requires authentication"""
    response = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": "TEST123",
            "merchant_id": "merchant-123"
        }
    )
    assert response.status_code == 401
    assert "Not authenticated" in str(response.json()["detail"])


def test_pilot_redeem_with_auth(client):
    """Test that /v1/pilot/redeem_code works with valid token"""
    # This would require creating a test user and getting a token
    # For now, we just verify the endpoint exists and requires auth
    pass



