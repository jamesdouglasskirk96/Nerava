"""
Integration test for phone-first checkin flow.

Tests the contract between link app and backend API to catch
response format mismatches early.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_twilio():
    """Mock Twilio client."""
    with patch('app.services.checkin_service.get_twilio_client') as mock:
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "test_sid_123"
        mock_client.messages.create.return_value = mock_message
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_redis():
    """Mock Redis for rate limiting."""
    with patch('app.utils.rate_limit.get_redis_client') as mock:
        yield None  # Use in-memory fallback


@pytest.fixture
def mock_db_session(db_session):
    """Provide database session."""
    return db_session


def test_phone_start_response_contract(mock_twilio, mock_redis, mock_db_session):
    """
    Test that phone-start endpoint returns correct response format.

    This test would have caught the ok vs success mismatch.
    """
    # Mock EV browser User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 Tesla/2024.38.6",
        "X-EV-Browser-Bypass": "true",  # Allow in test
    }

    response = client.post(
        "/api/v1/checkin/phone-start",
        json={"phone": "+15125551234"},
        headers=headers,
    )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()

    # Contract validation: must have 'ok' field (not 'success')
    assert "ok" in data, f"Response missing 'ok' field. Got: {list(data.keys())}"
    assert data["ok"] is True, f"Expected ok=True, got ok={data.get('ok')}"

    # Must have session_code
    assert "session_code" in data, f"Response missing 'session_code' field"
    assert data["session_code"] is not None, "session_code should not be None"
    assert len(data["session_code"]) == 6, f"Expected 6-char code, got: {data['session_code']}"

    # Must have expires_in_seconds
    assert "expires_in_seconds" in data, f"Response missing 'expires_in_seconds' field"
    assert isinstance(data["expires_in_seconds"], int), "expires_in_seconds must be int"
    assert data["expires_in_seconds"] > 0, "expires_in_seconds must be positive"

    # Optional fields
    if "message" in data:
        assert isinstance(data["message"], str), "message must be string"

    if "error" in data:
        assert isinstance(data["error"], str), "error must be string"


def test_phone_start_rate_limit(mock_twilio, mock_redis, mock_db_session):
    """Test rate limiting works correctly."""
    headers = {
        "User-Agent": "Mozilla/5.0 Tesla/2024.38.6",
        "X-EV-Browser-Bypass": "true",
    }

    # Make 3 requests (should succeed)
    for i in range(3):
        response = client.post(
            "/api/v1/checkin/phone-start",
            json={"phone": "+15125551235"},
            headers=headers,
        )
        assert response.status_code == 201, f"Request {i+1} should succeed"

    # 4th request should be rate limited
    response = client.post(
        "/api/v1/checkin/phone-start",
        json={"phone": "+15125551235"},
        headers=headers,
    )
    assert response.status_code == 429, f"Expected 429 rate limit, got {response.status_code}"


def test_phone_start_requires_ev_browser(mock_twilio, mock_db_session):
    """Test that non-EV browsers are rejected."""
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
    }

    response = client.post(
        "/api/v1/checkin/phone-start",
        json={"phone": "+15125551234"},
        headers=headers,
    )

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    data = response.json()
    assert "error" in data.get("detail", {}), "Should have error in detail"
    assert data["detail"]["error"] == "ev_browser_required"


def test_session_token_verification(mock_db_session):
    """Test that session tokens can be verified."""
    # This would require creating a session first, then testing token lookup
    # For now, just verify the endpoint exists and validates token format
    response = client.get("/api/v1/checkin/s/invalid-token")

    assert response.status_code in [404, 400], "Invalid token should return 404 or 400"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
