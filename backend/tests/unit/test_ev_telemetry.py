"""
Unit tests for /v1/ev/me/telemetry/latest endpoint
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
import httpx

from app.main import app
from app.models_vehicle import VehicleAccount


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user object"""
    user = MagicMock()
    user.id = 1
    user.public_id = "test-public-id"
    return user


@pytest.fixture
def mock_get_current_user(mock_user):
    """Mock get_current_user dependency"""
    with patch("app.routers.ev_smartcar.get_current_user", return_value=mock_user):
        yield


@pytest.fixture
def mock_vehicle_account():
    """Mock vehicle account"""
    account = MagicMock(spec=VehicleAccount)
    account.id = "test-account-id"
    account.user_id = 1
    account.provider = "smartcar"
    account.provider_vehicle_id = "test-vehicle-id"
    account.is_active = True
    return account


def test_telemetry_returns_404_when_not_connected(client, mock_get_current_user):
    """Test telemetry endpoint returns 404 when no vehicle connected"""
    with patch("app.routers.ev_smartcar.get_db") as mock_db:
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db.return_value = mock_db_session
        
        response = client.get(
            "/v1/ev/me/telemetry/latest",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


def test_telemetry_returns_424_on_smartcar_400(client, mock_get_current_user, mock_vehicle_account):
    """Test telemetry endpoint returns 424 when Smartcar returns 400"""
    with patch("app.routers.ev_smartcar.get_db") as mock_db:
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_vehicle_account
        mock_db.return_value = mock_db_session
        
        # Mock poll_vehicle_telemetry_for_account to raise HTTPStatusError with 400
        mock_error = httpx.HTTPStatusError(
            "Bad Request",
            request=MagicMock(),
            response=MagicMock(status_code=400)
        )
        
        with patch("app.routers.ev_smartcar.poll_vehicle_telemetry_for_account", side_effect=mock_error):
            response = client.get(
                "/v1/ev/me/telemetry/latest",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 424
            data = response.json()
            assert "SMARTCAR_TOKEN_EXCHANGE_FAILED" in str(data["detail"])


def test_telemetry_returns_200_when_mocked_smartcar_ok(client, mock_get_current_user, mock_vehicle_account):
    """Test telemetry endpoint returns 200 when mocked Smartcar returns ok"""
    with patch("app.routers.ev_smartcar.get_db") as mock_db:
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_vehicle_account
        mock_db.return_value = mock_db_session
        
        # Mock successful telemetry response
        from app.models_vehicle import VehicleTelemetry
        from datetime import datetime
        
        mock_telemetry = MagicMock(spec=VehicleTelemetry)
        mock_telemetry.recorded_at = datetime.utcnow()
        mock_telemetry.soc_pct = 75.5
        mock_telemetry.charging_state = "CHARGING"
        mock_telemetry.latitude = 30.2672
        mock_telemetry.longitude = -97.7431
        
        with patch("app.routers.ev_smartcar.poll_vehicle_telemetry_for_account", return_value=mock_telemetry):
            response = client.get(
                "/v1/ev/me/telemetry/latest",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "recorded_at" in data
            assert data["soc_pct"] == 75.5
            assert data["charging_state"] == "CHARGING"








