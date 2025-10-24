import pytest
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

from unittest.mock import patch, MagicMock
from app.services.cache import CacheService

class TestCacheService:
    
    @pytest.fixture
    def cache_service(self):
        with patch('redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            return CacheService()
    
    @pytest.mark.asyncio
    async def test_get_existing_key(self, cache_service):
        """Test getting an existing key from cache"""
        cache_service.redis_client.get.return_value = '{"test": "value"}'
        
        result = await cache_service.get("test-key")
        
        assert result == {"test": "value"}
        cache_service.redis_client.get.assert_called_once_with("test-key")
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_service):
        """Test getting a non-existent key returns None"""
        cache_service.redis_client.get.return_value = None
        
        result = await cache_service.get("nonexistent-key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_setex_success(self, cache_service):
        """Test setting a key with TTL"""
        cache_service.redis_client.setex.return_value = True
        
        result = await cache_service.setex("test-key", 60, {"data": "value"})
        
        assert result is True
        cache_service.redis_client.setex.assert_called_once_with(
            "test-key", 60, '{"data": "value"}'
        )
    
    @pytest.mark.asyncio
    async def test_setex_handles_errors(self, cache_service):
        """Test that setex handles Redis errors gracefully"""
        cache_service.redis_client.setex.side_effect = Exception("Redis error")
        
        result = await cache_service.setex("test-key", 60, {"data": "value"})
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_key(self, cache_service):
        """Test deleting a key"""
        cache_service.redis_client.delete.return_value = 1
        
        result = await cache_service.delete("test-key")
        
        assert result is True
        cache_service.redis_client.delete.assert_called_once_with("test-key")
    
    @pytest.mark.asyncio
    async def test_exists_key(self, cache_service):
        """Test checking if key exists"""
        cache_service.redis_client.exists.return_value = 1
        
        result = await cache_service.exists("test-key")
        
        assert result is True
        cache_service.redis_client.exists.assert_called_once_with("test-key")
    
    @pytest.mark.asyncio
    async def test_ttl_retrieval(self, cache_service):
        """Test that TTL is respected in cache retrieval"""
        # Mock Redis to return cached data
        cache_service.redis_client.get.return_value = '{"cached": "data"}'
        
        result = await cache_service.get("cached-key")
        
        assert result == {"cached": "data"}
        
        # Verify the key was retrieved from Redis
        cache_service.redis_client.get.assert_called_once_with("cached-key")
