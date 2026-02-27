"""
Tests for TeslaOAuthService — OAuth flow helpers, charging verification,
retry on unknown state, token refresh, and error differentiation.

All httpx calls are mocked.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import httpx

from app.services.tesla_oauth import (
    TeslaOAuthService,
    generate_ev_code,
    get_valid_access_token,
    TESLA_AUTH_URL,
    TESLA_TOKEN_URL,
    TESLA_FLEET_API_URL,
)
from app.models.tesla_connection import TeslaConnection


@pytest.fixture
def tesla_service():
    """Create a TeslaOAuthService with test credentials."""
    with patch("app.services.tesla_oauth.settings") as mock_settings:
        mock_settings.TESLA_CLIENT_ID = "test_client_id"
        mock_settings.TESLA_CLIENT_SECRET = "test_client_secret"
        mock_settings.API_BASE_URL = "https://api.test.com"
        service = TeslaOAuthService()
    return service


def _run_async(coro):
    """Helper to run async coroutines in synchronous tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestTeslaOAuthServiceAuthURL:
    """Tests for authorization URL generation."""

    def test_get_authorization_url(self, tesla_service):
        """Should generate a valid Tesla OAuth authorization URL."""
        url = tesla_service.get_authorization_url(state="test_state_abc")
        assert TESLA_AUTH_URL in url
        assert "client_id=test_client_id" in url
        assert "state=test_state_abc" in url
        assert "response_type=code" in url
        assert "openid" in url

    def test_get_authorization_url_custom_redirect(self, tesla_service):
        """Should allow overriding the redirect URI."""
        url = tesla_service.get_authorization_url(
            state="s1", redirect_uri="https://custom.example.com/callback"
        )
        assert "redirect_uri=https%3A%2F%2Fcustom.example.com%2Fcallback" in url


class TestTeslaOAuthServiceTokenExchange:
    """Tests for token exchange and refresh."""

    def test_exchange_code_for_tokens(self, tesla_service):
        """Should POST to token endpoint and return token response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = _run_async(tesla_service.exchange_code_for_tokens("auth_code_123"))

        assert result["access_token"] == "test_access_token"
        assert result["refresh_token"] == "test_refresh_token"

    def test_refresh_access_token(self, tesla_service):
        """Should refresh tokens using the refresh_token grant type."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = _run_async(tesla_service.refresh_access_token("old_refresh_token"))

        assert result["access_token"] == "new_access_token"


class TestTeslaOAuthServiceVehicles:
    """Tests for vehicle data and charging verification."""

    def test_get_vehicles(self, tesla_service):
        """Should return list of vehicles from Tesla API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": [
                {"id": 12345, "vin": "5YJ3E1EA0JF000001", "display_name": "My Tesla"}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            vehicles = _run_async(tesla_service.get_vehicles("access_token"))

        assert len(vehicles) == 1
        assert vehicles[0]["vin"] == "5YJ3E1EA0JF000001"

    def test_verify_charging_is_charging(self, tesla_service):
        """Should detect 'Charging' state as is_charging=True."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": {
                "charge_state": {
                    "charging_state": "Charging",
                    "battery_level": 65,
                    "charge_rate": 32,
                    "charger_power": 11,
                    "minutes_to_full_charge": 120,
                    "fast_charger_present": False,
                },
                "drive_state": {
                    "latitude": 30.4,
                    "longitude": -97.7,
                },
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            is_charging, charge_data = _run_async(
                tesla_service.verify_charging("token", "12345")
            )

        assert is_charging is True
        assert charge_data["battery_level"] == 65
        assert charge_data["latitude"] == 30.4

    def test_verify_charging_not_charging(self, tesla_service):
        """Should detect 'Stopped' state as is_charging=False."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": {
                "charge_state": {
                    "charging_state": "Stopped",
                    "battery_level": 90,
                },
                "drive_state": {},
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            is_charging, charge_data = _run_async(
                tesla_service.verify_charging("token", "12345")
            )

        assert is_charging is False

    def test_verify_charging_starting_state(self, tesla_service):
        """'Starting' state should also be detected as charging."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": {
                "charge_state": {"charging_state": "Starting"},
                "drive_state": {},
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            is_charging, _ = _run_async(
                tesla_service.verify_charging("token", "12345")
            )

        assert is_charging is True


class TestTeslaOAuthVerifyAllVehicles:
    """Tests for verify_charging_all_vehicles with retries."""

    def test_verify_all_vehicles_no_vehicles(self, tesla_service):
        """Should return False when account has no vehicles."""
        with patch.object(tesla_service, "get_vehicles", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            is_charging, charge_data, vehicle = _run_async(
                tesla_service.verify_charging_all_vehicles("token")
            )

        assert is_charging is False
        assert "error" in charge_data

    def test_verify_all_vehicles_finds_charging(self, tesla_service):
        """Should find the vehicle that is charging."""
        vehicles = [
            {"id": 1, "vin": "VIN1"},
            {"id": 2, "vin": "VIN2"},
        ]

        async def mock_verify(token, vid):
            if vid == "2":
                return True, {"is_charging": True, "charging_state": "Charging"}
            return False, {"is_charging": False, "charging_state": "Stopped"}

        with patch.object(tesla_service, "get_vehicles", new_callable=AsyncMock) as mock_get, \
             patch.object(tesla_service, "wake_vehicle", new_callable=AsyncMock) as mock_wake, \
             patch.object(tesla_service, "verify_charging", side_effect=mock_verify):
            mock_get.return_value = vehicles
            mock_wake.return_value = True

            is_charging, charge_data, vehicle = _run_async(
                tesla_service.verify_charging_all_vehicles("token")
            )

        assert is_charging is True
        assert vehicle["vin"] == "VIN2"

    def test_verify_all_vehicles_retries_on_unknown_state(self, tesla_service):
        """Should retry when charging_state is None (vehicle waking up)."""
        vehicles = [{"id": 1, "vin": "VIN1"}]
        call_count = 0

        async def mock_verify(token, vid):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return False, {"is_charging": False, "charging_state": None}
            return True, {"is_charging": True, "charging_state": "Charging"}

        with patch.object(tesla_service, "get_vehicles", new_callable=AsyncMock) as mock_get, \
             patch.object(tesla_service, "wake_vehicle", new_callable=AsyncMock), \
             patch.object(tesla_service, "verify_charging", side_effect=mock_verify), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_get.return_value = vehicles

            is_charging, charge_data, vehicle = _run_async(
                tesla_service.verify_charging_all_vehicles("token")
            )

        assert is_charging is True
        assert call_count == 3


class TestTeslaOAuthTokenRefresh:
    """Tests for get_valid_access_token with error differentiation."""

    def test_token_still_valid(self, db):
        """Should return decrypted token if not yet expired."""
        user_id = 1
        connection = MagicMock(spec=TeslaConnection)
        connection.token_expires_at = datetime.utcnow() + timedelta(hours=1)
        connection.access_token = "encrypted_access"
        service = MagicMock()

        with patch("app.services.tesla_oauth.decrypt_token", return_value="decrypted_access"):
            result = _run_async(get_valid_access_token(db, connection, service))

        assert result == "decrypted_access"

    def test_token_refresh_on_401_deactivates(self, db):
        """HTTP 401 during refresh should deactivate the connection."""
        connection = MagicMock(spec=TeslaConnection)
        connection.token_expires_at = datetime.utcnow() - timedelta(hours=1)
        connection.refresh_token = "encrypted_refresh"
        connection.is_active = True

        service = MagicMock()
        # Build a proper httpx response for 401
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        service.refresh_access_token = AsyncMock(side_effect=error)

        with patch("app.services.tesla_oauth.decrypt_token", return_value="raw_refresh"):
            result = _run_async(get_valid_access_token(db, connection, service))

        assert result is None
        assert connection.is_active is False

    def test_token_refresh_on_5xx_raises(self, db):
        """HTTP 5xx during refresh should raise (transient error)."""
        connection = MagicMock(spec=TeslaConnection)
        connection.token_expires_at = datetime.utcnow() - timedelta(hours=1)
        connection.refresh_token = "encrypted_refresh"

        service = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 502
        error = httpx.HTTPStatusError(
            "Bad Gateway", request=MagicMock(), response=mock_response
        )
        service.refresh_access_token = AsyncMock(side_effect=error)

        with patch("app.services.tesla_oauth.decrypt_token", return_value="raw_refresh"):
            with pytest.raises(httpx.HTTPStatusError):
                _run_async(get_valid_access_token(db, connection, service))


class TestEVCodeGeneration:
    """Tests for EV verification code generation."""

    def test_ev_code_format(self):
        """EV code should match EV-XXXX format."""
        code = generate_ev_code()
        assert code.startswith("EV-")
        assert len(code) == 7  # "EV-" + 4 chars

    def test_ev_code_uniqueness(self):
        """Multiple generated codes should be unique (probabilistic)."""
        codes = {generate_ev_code() for _ in range(100)}
        # With 34^4 = ~1.3M possible codes, 100 should all be unique
        assert len(codes) == 100
