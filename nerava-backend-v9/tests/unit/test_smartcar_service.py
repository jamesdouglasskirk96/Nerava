"""
Unit tests for Smartcar Service - OAuth and vehicle API calls
All HTTP calls must be mocked to avoid real network requests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import httpx
from app.services.smartcar_service import (
    exchange_code_for_tokens,
    refresh_tokens,
    list_vehicles,
    get_vehicle_location,
    get_vehicle_charge,
)
from app.models.vehicle import VehicleAccount, VehicleToken


class TestExchangeCodeForTokens:
    """Test OAuth token exchange"""
    
    @pytest.mark.asyncio
    async def test_successful_token_exchange(self):
        """Successful token exchange should return token data"""
        mock_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "scope": "read_vehicle_info read_location read_charge",
        }
        
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_post.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await exchange_code_for_tokens("test_code")
            
            assert result["access_token"] == "test_access_token"
            assert result["refresh_token"] == "test_refresh_token"
            assert result["expires_in"] == 3600
    
    @pytest.mark.asyncio
    async def test_401_error_handling(self):
        """401 error should raise HTTPStatusError"""
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 401
            mock_response_obj.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=mock_response_obj
            )
            mock_post.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            with pytest.raises(httpx.HTTPStatusError):
                await exchange_code_for_tokens("invalid_code")
    
    @pytest.mark.asyncio
    async def test_500_error_handling(self):
        """500 error should raise HTTPStatusError"""
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 500
            mock_response_obj.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Internal Server Error",
                request=MagicMock(),
                response=mock_response_obj
            )
            mock_post.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            with pytest.raises(httpx.HTTPStatusError):
                await exchange_code_for_tokens("test_code")


class TestRefreshTokens:
    """Test token refresh logic"""
    
    @pytest.mark.asyncio
    async def test_refresh_when_token_valid(self, db):
        """Should return existing token if still valid (expires in > 5 min)"""
        vehicle_account = VehicleAccount(
            id="va_123",
            user_id=1,
            provider="smartcar",
            provider_vehicle_id="vehicle_123",
            is_active=True
        )
        db.add(vehicle_account)
        db.commit()
        
        # Token expires in 10 minutes (still valid)
        existing_token = VehicleToken(
            id="token_123",
            vehicle_account_id=vehicle_account.id,
            access_token="old_token",
            refresh_token="refresh_token",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            scope="read_vehicle_info"
        )
        db.add(existing_token)
        db.commit()
        
        result = await refresh_tokens(db, vehicle_account)
        
        # Should return existing token (no refresh needed)
        assert result.id == existing_token.id
        assert result.access_token == "old_token"
    
    @pytest.mark.asyncio
    async def test_refresh_when_token_expired(self, db):
        """Should refresh token if expires soon (< 5 min)"""
        vehicle_account = VehicleAccount(
            id="va_456",
            user_id=1,
            provider="smartcar",
            provider_vehicle_id="vehicle_456",
            is_active=True
        )
        db.add(vehicle_account)
        db.commit()
        
        # Token expires in 2 minutes (needs refresh)
        old_token = VehicleToken(
            id="token_456",
            vehicle_account_id=vehicle_account.id,
            access_token="old_token",
            refresh_token="refresh_token",
            expires_at=datetime.utcnow() + timedelta(minutes=2),
            scope="read_vehicle_info"
        )
        db.add(old_token)
        db.commit()
        
        mock_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "scope": "read_vehicle_info"
        }
        
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_post.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await refresh_tokens(db, vehicle_account)
            
            # Should have new token
            assert result.access_token == "new_access_token"
            # Should create new token record
            assert result.id != old_token.id


class TestListVehicles:
    """Test vehicle listing"""
    
    @pytest.mark.asyncio
    async def test_successful_list_vehicles(self):
        """Should return vehicles list"""
        mock_response = {
            "vehicles": [
                {"id": "vehicle_1", "meta": {"data": {}}},
                {"id": "vehicle_2", "meta": {"data": {}}}
            ]
        }
        
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            result = await list_vehicles("test_access_token")
            
            assert "vehicles" in result
            assert len(result["vehicles"]) == 2
    
    @pytest.mark.asyncio
    async def test_token_error_401_raises_exception(self):
        """401 error (expired/invalid token) should raise HTTPStatusError"""
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 401
            mock_response_obj.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=mock_response_obj
            )
            mock_get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await list_vehicles("expired_token")
            
            assert exc_info.value.response.status_code == 401


class TestGetVehicleLocation:
    """Test vehicle location retrieval"""
    
    @pytest.mark.asyncio
    async def test_successful_get_location(self):
        """Should return location data"""
        mock_response = {
            "latitude": 30.4021,
            "longitude": -97.7266
        }
        
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            result = await get_vehicle_location("test_token", "vehicle_123")
            
            assert result["latitude"] == 30.4021
            assert result["longitude"] == -97.7266


class TestGetVehicleCharge:
    """Test vehicle charge state retrieval"""
    
    @pytest.mark.asyncio
    async def test_successful_get_charge(self):
        """Should return charge state"""
        mock_response = {
            "stateOfCharge": 75.5,
            "isPluggedIn": True
        }
        
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            result = await get_vehicle_charge("test_token", "vehicle_123")
            
            assert result["stateOfCharge"] == 75.5
            assert result["isPluggedIn"] is True
    
    @pytest.mark.asyncio
    async def test_token_error_401_raises_exception(self):
        """401 error (expired/invalid token) should raise HTTPStatusError"""
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 401
            mock_response_obj.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=mock_response_obj
            )
            mock_get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await get_vehicle_charge("expired_token", "vehicle_123")
            
            assert exc_info.value.response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_server_error_500_raises_exception(self):
        """500 error should raise HTTPStatusError"""
        with patch("app.services.smartcar_service.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 500
            mock_response_obj.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Internal Server Error",
                request=MagicMock(),
                response=mock_response_obj
            )
            mock_get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await get_vehicle_charge("test_token", "vehicle_123")
            
            assert exc_info.value.response.status_code == 500

