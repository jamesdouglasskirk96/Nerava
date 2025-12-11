"""
Integration tests for EV/Smartcar OAuth connect flow
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.models import User
from app.models.vehicle import VehicleAccount


@pytest.fixture
def test_user(db):
    """Create a test user"""
    # Use autoincrement ID instead of hardcoding to avoid conflicts
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True,
        role_flags="driver"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user




class TestEvConnectFlow:
    """Test EV connect OAuth flow"""
    
    def test_get_connect_returns_smartcar_url(self, client, db, test_user):
        """GET /v1/ev/connect should return or redirect to Smartcar auth URL"""
        from app.main_simple import app
        from app.dependencies.domain import get_current_user
        
        # Override auth dependency to return test_user
        def mock_get_current_user():
            return test_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        # Mock Smartcar settings - patch at the module level where it's imported
        with patch("app.routers.ev_smartcar.settings") as mock_settings:
            # Create a MagicMock that properly handles method calls
            mock_settings.smartcar_enabled = MagicMock(return_value=True)
            mock_settings.smartcar_connect_url = "https://connect.smartcar.com"
            mock_settings.smartcar_client_id = "test_client_id"
            mock_settings.smartcar_redirect_uri = "https://api.test.com/oauth/smartcar/callback"
            mock_settings.smartcar_mode = "test"
            mock_settings.jwt_secret = "test_secret_key"
            mock_settings.jwt_alg = "HS256"
            
            try:
                response = client.get("/v1/ev/connect")
                
                # Should return 200 with Smartcar URL
                assert response.status_code == 200
                data = response.json()
                assert "url" in data
                assert "smartcar.com" in data["url"] or "connect.smartcar.com" in data["url"]
            finally:
                # Clear override
                app.dependency_overrides.pop(get_current_user, None)
    
    def test_oauth_callback_creates_vehicle_account(self, client, db, test_user):
        """OAuth callback should create VehicleAccount and link to user"""
        # Mock Smartcar token exchange
        mock_token_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "scope": "read_vehicle_info"
        }
        
        mock_vehicles_response = {
            "vehicles": ["vehicle_123"]  # Smartcar returns list of vehicle ID strings
        }
        
        with patch("app.routers.ev_smartcar.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
            with patch("app.routers.ev_smartcar.list_vehicles", new_callable=AsyncMock) as mock_list:
                mock_exchange.return_value = mock_token_response
                mock_list.return_value = mock_vehicles_response
                
                # Mock state token verification
                with patch("app.routers.ev_smartcar.verify_state_token") as mock_verify:
                    with patch("app.routers.ev_smartcar.settings") as mock_settings:
                        mock_verify.return_value = test_user.id
                        mock_settings.frontend_url = "http://localhost:8001/app"
                        mock_settings.jwt_secret = "test_secret_key"
                        mock_settings.jwt_alg = "HS256"
                        
                        # Call callback endpoint
                        response = client.get(
                            "/oauth/smartcar/callback",
                            params={"code": "test_code", "state": "test_state"}
                        )
                        
                        # Should redirect to frontend (302) or return success
                        assert response.status_code in [200, 302]
                        
                        # Verify VehicleAccount was created
                        vehicle_account = db.query(VehicleAccount).filter(
                            VehicleAccount.user_id == test_user.id
                        ).first()
                        
                        assert vehicle_account is not None
                        assert vehicle_account.provider == "smartcar"
                        assert vehicle_account.provider_vehicle_id == "vehicle_123"

