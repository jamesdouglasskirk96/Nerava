"""
Test P1-4: Magic link rate limiting (3 requests per minute)
"""
import pytest
import time
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    from nerava_backend_v9.app.main import app
    return TestClient(app)


def test_magic_link_rate_limit(client):
    """Test that magic link requests are rate limited to 3/min"""
    # Make 4 requests rapidly
    responses = []
    for i in range(4):
        response = client.post(
            "/v1/auth/magic_link/request",
            json={"email": f"test{i}@example.com"}
        )
        responses.append(response.status_code)
    
    # At least one should be 429 (rate limited)
    assert 429 in responses, "Rate limit not enforced"


def test_magic_link_rate_limit_resets(client):
    """Test that rate limit resets after time window"""
    # Make 3 requests (should succeed)
    for i in range(3):
        response = client.post(
            "/v1/auth/magic_link/request",
            json={"email": f"test{i}@example.com"}
        )
        assert response.status_code != 429
    
    # Wait 61 seconds (rate limit window)
    time.sleep(61)
    
    # Next request should succeed
    response = client.post(
        "/v1/auth/magic_link/request",
        json={"email": "test4@example.com"}
    )
    # Should not be rate limited after window reset
    assert response.status_code != 429



