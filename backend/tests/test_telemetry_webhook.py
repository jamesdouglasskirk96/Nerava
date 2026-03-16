"""
Tests for Tesla Fleet Telemetry webhook endpoint.

Covers: valid payloads, HMAC signature validation, feature flag,
and error handling.
"""
import json
import hmac
import hashlib
import uuid
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


@pytest.fixture
def tesla_user_with_conn(db):
    """Create a user with active Tesla connection for webhook tests."""
    from app.models.user import User
    from app.models.tesla_connection import TeslaConnection

    user = User(
        email="webhook_driver@test.com",
        password_hash="hashed",
        is_active=True,
        role_flags="driver",
    )
    db.add(user)
    db.flush()

    conn = TeslaConnection(
        id=str(uuid.uuid4()),
        user_id=user.id,
        access_token="enc_token",
        refresh_token="enc_refresh",
        token_expires_at=datetime.utcnow() + timedelta(hours=1),
        vehicle_id="v123",
        vin="5YJ3E1EA1PF000002",
        is_active=True,
        telemetry_enabled=True,
    )
    db.add(conn)
    db.commit()
    db.refresh(user)
    return user


def _make_payload(vin="5YJ3E1EA1PF000002", charge_state="Charging", battery=50):
    """Build a valid telemetry webhook payload."""
    return {
        "vin": vin,
        "data": [
            {"key": "DetailedChargeState", "value": charge_state},
            {"key": "BatteryLevel", "value": battery},
            {"key": "ACChargingPower", "value": 11.0},
        ],
        "created_at": datetime.utcnow().isoformat(),
        "msg_type": "data",
    }


class TestTelemetryWebhookEndpoint:
    """Test POST /v1/webhooks/tesla/telemetry."""

    def test_valid_payload_returns_200(self, client, tesla_user_with_conn):
        """Valid telemetry payload should return 200."""
        payload = _make_payload()
        response = client.post(
            "/v1/webhooks/tesla/telemetry",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"

    def test_valid_payload_creates_session(self, client, tesla_user_with_conn):
        """Valid charging telemetry should create a session."""
        payload = _make_payload(charge_state="Charging")
        response = client.post(
            "/v1/webhooks/tesla/telemetry",
            json=payload,
        )
        assert response.status_code == 200
        result = response.json().get("result")
        assert result is not None
        assert result["action"] == "created"

    def test_unknown_vin_returns_200_with_null_result(self, client, tesla_user_with_conn):
        """Unknown VIN should still return 200 (no retry) but null result."""
        payload = _make_payload(vin="UNKNOWN_VIN_99999")
        response = client.post(
            "/v1/webhooks/tesla/telemetry",
            json=payload,
        )
        assert response.status_code == 200
        assert response.json()["result"] is None

    def test_invalid_payload_returns_422(self, client, tesla_user_with_conn):
        """Malformed payload should return 422."""
        response = client.post(
            "/v1/webhooks/tesla/telemetry",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_feature_flag_disabled_returns_503(self, client, tesla_user_with_conn):
        """Disabled webhook should return 503."""
        with patch("app.routers.tesla_telemetry.settings") as mock_settings:
            mock_settings.TELEMETRY_WEBHOOK_ENABLED = False
            mock_settings.TESLA_TELEMETRY_HMAC_SECRET = ""

            payload = _make_payload()
            response = client.post(
                "/v1/webhooks/tesla/telemetry",
                json=payload,
            )
            assert response.status_code == 503

    def test_invalid_hmac_returns_401(self, client, tesla_user_with_conn):
        """Invalid HMAC signature should return 401 when secret is configured."""
        with patch("app.routers.tesla_telemetry.settings") as mock_settings:
            mock_settings.TELEMETRY_WEBHOOK_ENABLED = True
            mock_settings.TESLA_TELEMETRY_HMAC_SECRET = "test-secret-key"

            payload = _make_payload()
            response = client.post(
                "/v1/webhooks/tesla/telemetry",
                json=payload,
                headers={"X-Telemetry-Signature": "invalid_signature"},
            )
            assert response.status_code == 401

    def test_valid_hmac_accepted(self, client, tesla_user_with_conn):
        """Valid HMAC signature should be accepted."""
        secret = "test-secret-key"
        payload = _make_payload()
        body = json.dumps(payload).encode()
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        with patch("app.routers.tesla_telemetry.settings") as mock_settings:
            mock_settings.TELEMETRY_WEBHOOK_ENABLED = True
            mock_settings.TESLA_TELEMETRY_HMAC_SECRET = secret

            response = client.post(
                "/v1/webhooks/tesla/telemetry",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Telemetry-Signature": signature,
                },
            )
            assert response.status_code == 200
