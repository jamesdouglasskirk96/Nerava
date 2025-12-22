"""
Test Smartcar state JWT functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from jose import jwt

from app.main_simple import app
from app.models import User
from app.core.config import settings
from app.core.security import create_smartcar_state_jwt, verify_smartcar_state_jwt

client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    import uuid
    user = User(
        public_id=str(uuid.uuid4()),
        email="smartcar_test@example.com",
        auth_provider="google",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_connect_creates_state_jwt(test_user, db: Session):
    """Test /v1/ev/connect creates state JWT with user_public_id"""
    # Create access token for user
    from app.core.security import create_access_token
    access_token = create_access_token(test_user.public_id)
    
    # Mock Smartcar config
    with patch.object(settings, 'SMARTCAR_CLIENT_ID', 'test_client_id'), \
         patch.object(settings, 'SMARTCAR_CLIENT_SECRET', 'test_secret'), \
         patch.object(settings, 'SMARTCAR_REDIRECT_URI', 'http://test.com/callback'), \
         patch.object(settings, 'SMARTCAR_MODE', 'sandbox'), \
         patch.object(settings, 'SMARTCAR_CONNECT_URL', 'https://connect.smartcar.com'):
        
        response = client.get("/v1/ev/connect", headers={
            "Authorization": f"Bearer {access_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        
        # Extract state from URL
        import urllib.parse
        parsed_url = urllib.parse.urlparse(data["url"])
        params = urllib.parse.parse_qs(parsed_url.query)
        state = params.get("state", [None])[0]
        
        assert state is not None
        
        # Verify state JWT contains user_public_id
        if settings.SMARTCAR_STATE_SECRET:
            payload = verify_smartcar_state_jwt(state)
            assert payload["user_public_id"] == test_user.public_id
            assert payload["purpose"] == "smartcar_oauth"


def test_callback_validates_state_and_links_user(test_user, db: Session):
    """Test callback validates state JWT and links to user by public_id"""
    # Create state JWT
    if not settings.SMARTCAR_STATE_SECRET:
        pytest.skip("SMARTCAR_STATE_SECRET not configured")
    
    state = create_smartcar_state_jwt(test_user.public_id)
    
    # Mock Smartcar token exchange
    mock_token_data = {
        "access_token": "smartcar_access_token",
        "refresh_token": "smartcar_refresh_token",
        "expires_in": 3600,
        "scope": "read_vehicle_info"
    }
    
    mock_vehicles_data = {
        "vehicles": ["vehicle_123"]
    }
    
    with patch('app.services.smartcar_service.exchange_code_for_tokens') as mock_exchange, \
         patch('app.services.smartcar_service.list_vehicles') as mock_list:
        
        mock_exchange.return_value = mock_token_data
        mock_list.return_value = mock_vehicles_data
        
        # Mock Smartcar config
        with patch.object(settings, 'SMARTCAR_CLIENT_ID', 'test_client_id'), \
             patch.object(settings, 'SMARTCAR_CLIENT_SECRET', 'test_secret'), \
             patch.object(settings, 'SMARTCAR_REDIRECT_URI', 'http://test.com/callback'), \
             patch.object(settings, 'FRONTEND_URL', 'http://test.com'):
            
            response = client.get("/oauth/smartcar/callback", params={
                "code": "smartcar_code",
                "state": state
            }, follow_redirects=False)
            
            # Should redirect (302) on success
            assert response.status_code == 302
            
            # Verify vehicle was linked to user (check database)
            from app.models_vehicle import VehicleAccount
            account = db.query(VehicleAccount).filter(
                VehicleAccount.user_id == test_user.id
            ).first()
            
            assert account is not None
            assert account.provider == "smartcar"

