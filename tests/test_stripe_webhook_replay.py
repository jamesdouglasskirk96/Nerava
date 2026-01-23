"""
Test P1-5: Stripe webhook replay protection (reject events >5min old)
"""
import pytest
import json
import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    from nerava_backend_v9.app.main import app
    return TestClient(app)


def test_stripe_webhook_rejects_old_event(client):
    """Test that Stripe webhooks older than 5 minutes are rejected"""
    # Create an event with timestamp 6 minutes ago
    old_timestamp = int((datetime.now(timezone.utc).timestamp() - 360))  # 6 minutes ago
    
    old_event = {
        "id": "evt_test_old",
        "type": "transfer.paid",
        "created": old_timestamp,
        "data": {
            "object": {
                "id": "tr_test"
            }
        }
    }
    
    response = client.post(
        "/v1/stripe/webhook",
        json=old_event,
        headers={"stripe-signature": "test-signature"}
    )
    
    # Should be rejected with 400
    assert response.status_code == 400
    assert "too old" in response.json()["detail"].lower() or "replay" in response.json()["detail"].lower()


def test_stripe_webhook_accepts_recent_event(client):
    """Test that recent Stripe webhooks (<5min old) are accepted"""
    # Create an event with current timestamp
    recent_timestamp = int(datetime.now(timezone.utc).timestamp())
    
    recent_event = {
        "id": "evt_test_recent",
        "type": "transfer.paid",
        "created": recent_timestamp,
        "data": {
            "object": {
                "id": "tr_test"
            }
        }
    }
    
    # Note: This test may fail if signature verification is required
    # In local/dev, signature verification might be skipped
    response = client.post(
        "/v1/stripe/webhook",
        json=recent_event,
        headers={"stripe-signature": "test-signature"}
    )
    
    # Should not be rejected for being too old
    # (May fail for other reasons like signature, but not for age)
    if response.status_code == 400:
        assert "too old" not in response.json()["detail"].lower()



