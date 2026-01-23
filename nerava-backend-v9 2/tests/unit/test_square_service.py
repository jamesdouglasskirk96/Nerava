"""
Unit tests for Square Service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.square_service import (
    get_square_oauth_authorize_url,
    exchange_square_oauth_code,
    fetch_square_location_stats,
    SquareOAuthResult,
    SquareLocationStats,
)
from app.config import settings


class TestSquareOAuth:
    """Test Square OAuth URL generation"""
    
    @pytest.mark.asyncio
    async def test_get_square_oauth_authorize_url(self):
        """Should build correct Square OAuth URL"""
        # Mock settings
        with patch('app.services.square_service.settings') as mock_settings:
            mock_settings.square_application_id = "test_app_id"
            mock_settings.square_redirect_url = "https://example.com/callback"
            mock_settings.square_env = "sandbox"
            
            state = "test_state_123"
            url = await get_square_oauth_authorize_url(state)
            
            assert "squareupsandbox.com" in url
            assert "test_app_id" in url
            assert state in url
            assert "MERCHANT_PROFILE_READ" in url
            assert "PAYMENTS_READ" in url
    
    @pytest.mark.asyncio
    async def test_get_square_oauth_authorize_url_missing_config(self):
        """Should raise ValueError if Square config is missing"""
        with patch('app.services.square_service.settings') as mock_settings:
            mock_settings.square_application_id = ""
            mock_settings.square_redirect_url = "https://example.com/callback"
            
            with pytest.raises(ValueError, match="SQUARE_APPLICATION_ID"):
                await get_square_oauth_authorize_url("state")
    
    @pytest.mark.asyncio
    async def test_exchange_square_oauth_code_success(self):
        """Should exchange OAuth code for token successfully"""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "merchant_id": "test_merchant_id",
            "token_type": "bearer"
        }
        
        # Mock locations API response
        mock_locations_response = MagicMock()
        mock_locations_response.status_code = 200
        mock_locations_response.json.return_value = {
            "locations": [{"id": "test_location_id"}]
        }
        
        with patch('app.services.square_service.settings') as mock_settings:
            mock_settings.square_application_id = "test_app_id"
            mock_settings.square_application_secret = "test_secret"
            mock_settings.square_redirect_url = "https://example.com/callback"
            mock_settings.square_env = "sandbox"
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                # First call (token exchange)
                mock_client.post.return_value = mock_response
                # Second call (locations)
                mock_client.get.return_value = mock_locations_response
                
                result = await exchange_square_oauth_code("test_code")
                
                assert isinstance(result, SquareOAuthResult)
                assert result.access_token == "test_access_token"
                assert result.merchant_id == "test_merchant_id"
                assert result.location_id == "test_location_id"
    
    @pytest.mark.asyncio
    async def test_exchange_square_oauth_code_api_error(self):
        """Should raise ValueError if Square API returns error"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid code"
        
        with patch('app.services.square_service.settings') as mock_settings:
            mock_settings.square_application_id = "test_app_id"
            mock_settings.square_application_secret = "test_secret"
            mock_settings.square_redirect_url = "https://example.com/callback"
            mock_settings.square_env = "sandbox"
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.post.return_value = mock_response
                
                with pytest.raises(ValueError, match="Square OAuth exchange failed"):
                    await exchange_square_oauth_code("invalid_code")
    
    @pytest.mark.asyncio
    async def test_fetch_square_location_stats_with_orders(self):
        """Should calculate AOV from Square orders"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "orders": [
                {"total_money": {"amount": 2000}},  # $20
                {"total_money": {"amount": 1500}},  # $15
                {"total_money": {"amount": 2500}},  # $25
            ]
        }
        
        with patch('app.services.square_service.settings') as mock_settings:
            mock_settings.square_env = "sandbox"
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.post.return_value = mock_response
                
                result = await fetch_square_location_stats("token", "location_id")
                
                assert isinstance(result, SquareLocationStats)
                # Average of 2000, 1500, 2500 = 2000 cents
                assert result.avg_order_value_cents == 2000
    
    @pytest.mark.asyncio
    async def test_fetch_square_location_stats_default(self):
        """Should return default AOV if no orders found"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"orders": []}
        
        with patch('app.services.square_service.settings') as mock_settings:
            mock_settings.square_env = "sandbox"
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.post.return_value = mock_response
                
                result = await fetch_square_location_stats("token", "location_id")
                
                assert isinstance(result, SquareLocationStats)
                assert result.avg_order_value_cents == 1500  # Default $15

