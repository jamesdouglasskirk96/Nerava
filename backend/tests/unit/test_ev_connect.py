"""
Unit tests for /v1/ev/connect endpoint
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.core.config import settings


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


def test_ev_connect_returns_url_when_enabled(client, mock_get_current_user):
    """Test /v1/ev/connect returns URL when Smartcar is enabled"""
    with patch.object(settings, 'smartcar_enabled', True):
        with patch.object(settings, 'smartcar_client_id', 'test_client_id'):
            with patch.object(settings, 'smartcar_redirect_uri', 'http://test.com/callback'):
                with patch.object(settings, 'smartcar_mode', 'sandbox'):
                    with patch.object(settings, 'smartcar_connect_url', 'https://connect.smartcar.com'):
                        with patch("app.routers.ev_smartcar.create_state_token", return_value="test-state-token"):
                            response = client.get(
                                "/v1/ev/connect",
                                headers={"Authorization": "Bearer test-token"}
                            )
                            
                            assert response.status_code == 200
                            data = response.json()
                            assert "url" in data
                            assert "smartcar.com" in data["url"]
                            assert "test_client_id" in data["url"]


def test_ev_connect_503_when_disabled(client, mock_get_current_user):
    """Test /v1/ev/connect returns 503 when Smartcar is disabled"""
    with patch.object(settings, 'smartcar_enabled', False):
        response = client.get(
            "/v1/ev/connect",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert "not configured" in data["detail"].lower()








