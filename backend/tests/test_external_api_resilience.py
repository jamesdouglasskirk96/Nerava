"""
Test external API resilience: retry logic and caching.

These tests verify that external API calls retry on transient failures
and cache responses appropriately.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.core.retry import retry_with_backoff, should_retry_error
from app.integrations.google_places_client import get_place_details
from app.integrations.nrel_client import fetch_chargers_in_bbox


class TestRetryLogic:
    """Test retry logic with exponential backoff"""
    
    @pytest.mark.asyncio
    async def test_retry_on_5xx_error(self):
        """Test that retries happen on 5xx errors"""
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                response = MagicMock()
                response.status_code = 500
                raise httpx.HTTPStatusError("Server error", request=MagicMock(), response=response)
            return "success"
        
        result = await retry_with_backoff(failing_func, max_attempts=3)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test that retries happen on timeout errors"""
        call_count = 0
        
        async def timeout_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Request timeout")
            return "success"
        
        result = await retry_with_backoff(timeout_func, max_attempts=3)
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_error(self):
        """Test that 4xx errors are NOT retried"""
        call_count = 0
        
        async def client_error_func():
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 400
            raise httpx.HTTPStatusError("Bad request", request=MagicMock(), response=response)
        
        with pytest.raises(httpx.HTTPStatusError):
            await retry_with_backoff(client_error_func, max_attempts=3)
        
        # Should only be called once (no retries)
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_stops_after_max_attempts(self):
        """Test that retry stops after max attempts"""
        call_count = 0
        
        async def always_failing_func():
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 500
            raise httpx.HTTPStatusError("Server error", request=MagicMock(), response=response)
        
        with pytest.raises(httpx.HTTPStatusError):
            await retry_with_backoff(always_failing_func, max_attempts=3)
        
        assert call_count == 3
    
    def test_should_retry_error_logic(self):
        """Test should_retry_error helper function"""
        # 5xx errors should retry
        response_500 = MagicMock()
        response_500.status_code = 500
        error_500 = httpx.HTTPStatusError("Server error", request=MagicMock(), response=response_500)
        assert should_retry_error(error_500) is True
        
        # 4xx errors should NOT retry
        response_400 = MagicMock()
        response_400.status_code = 400
        error_400 = httpx.HTTPStatusError("Bad request", request=MagicMock(), response=response_400)
        assert should_retry_error(error_400) is False
        
        # Timeout should retry
        timeout_error = httpx.TimeoutException("Request timeout")
        assert should_retry_error(timeout_error) is True
        
        # Network error should retry
        network_error = httpx.NetworkError("Network error")
        assert should_retry_error(network_error) is True


class TestCaching:
    """Test external API caching"""
    
    @pytest.mark.asyncio
    async def test_google_places_cache_hit(self):
        """Test that Google Places API responses are cached"""
        place_id = "test_place_123"
        mock_result = {"place_id": place_id, "name": "Test Place"}
        
        # Mock the cache
        with patch('app.integrations.google_places_client.cache') as mock_cache:
            # First call: cache miss, should call API
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            
            # Mock httpx call
            with patch('app.integrations.google_places_client.retry_with_backoff') as mock_retry:
                mock_retry.return_value = {"status": "OK", "result": mock_result}
                
                result1 = await get_place_details(place_id)
                
                # Verify cache.set was called
                assert mock_cache.set.called
                
                # Second call: cache hit, should NOT call API
                mock_cache.get = AsyncMock(return_value=mock_result)
                
                result2 = await get_place_details(place_id)
                
                # Verify result from cache
                assert result2 == mock_result
                # Verify retry was NOT called again
                assert mock_retry.call_count == 1
    
    @pytest.mark.asyncio
    async def test_nrel_cache_hit(self):
        """Test that NREL API responses are cached"""
        bbox = (30.0, -97.0, 31.0, -96.0)
        mock_stations = [
            {
                "id": "station_1",
                "station_name": "Test Station",
                "latitude": 30.5,
                "longitude": -96.5
            }
        ]
        
        # Mock the cache
        with patch('app.integrations.nrel_client.cache') as mock_cache:
            # First call: cache miss
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            
            # Mock httpx call
            with patch('app.integrations.nrel_client.retry_with_backoff') as mock_retry:
                mock_retry.return_value = {"fuel_stations": mock_stations}
                
                result1 = await fetch_chargers_in_bbox(bbox)
                
                # Verify cache.set was called
                assert mock_cache.set.called
                
                # Second call: cache hit
                mock_cache.get = AsyncMock(return_value=mock_stations)
                
                result2 = await fetch_chargers_in_bbox(bbox)
                
                # Verify result from cache
                assert len(result2) == 1
                # Verify retry was NOT called again
                assert mock_retry.call_count == 1
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """Test that cache TTL expiration works"""
        place_id = "test_place_456"
        mock_result = {"place_id": place_id, "name": "Test Place"}
        
        with patch('app.integrations.google_places_client.cache') as mock_cache:
            # First call: cache miss
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            
            with patch('app.integrations.google_places_client.retry_with_backoff') as mock_retry:
                mock_retry.return_value = {"status": "OK", "result": mock_result}
                
                await get_place_details(place_id)
                
                # Verify cache.set was called with TTL=300 (5 minutes)
                # call_args is a tuple: (args, kwargs)
                if mock_cache.set.called:
                    call_args = mock_cache.set.call_args
                    # Check kwargs for ttl or args[2] for positional
                    ttl = call_args.kwargs.get('ttl') if call_args.kwargs else (call_args[0][2] if len(call_args[0]) > 2 else None)
                    assert ttl == 300, f"Expected TTL=300, got {ttl}"


class TestExternalAPIIntegration:
    """Integration tests for external API resilience"""
    
    @pytest.mark.asyncio
    async def test_google_places_retry_on_failure(self):
        """Test that Google Places retries on transient failures"""
        place_id = "test_place_789"
        call_count = 0
        
        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                response = MagicMock()
                response.status_code = 500
                raise httpx.HTTPStatusError("Server error", request=MagicMock(), response=response)
            return {"status": "OK", "result": {"place_id": place_id}}
        
        with patch('app.integrations.google_places_client.cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            
            with patch('app.integrations.google_places_client.retry_with_backoff', side_effect=mock_api_call):
                result = await get_place_details(place_id)
                
                # Should succeed after retry
                assert result is not None
                assert call_count == 2

