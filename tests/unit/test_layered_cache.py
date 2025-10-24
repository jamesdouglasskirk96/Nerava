import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

import asyncio
from unittest.mock import patch, MagicMock
from app.cache.layers import L1Cache, L2Cache, LayeredCache, cached

class TestL1Cache:
    
    def test_get_set_delete(self):
        """Test basic L1 cache operations"""
        cache = L1Cache(max_size=10, default_ttl=60)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test delete
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_ttl_expiration(self):
        """Test TTL expiration"""
        cache = L1Cache(max_size=10, default_ttl=1)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        import time
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = L1Cache(max_size=3, default_ttl=60)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add another key, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Still there
        assert cache.get("key4") == "value4"  # New key
    
    def test_stats(self):
        """Test cache statistics"""
        cache = L1Cache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.get("key1")
        
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 10

class TestL2Cache:
    
    @pytest.mark.asyncio
    async def test_get_set_delete(self):
        """Test basic L2 cache operations"""
        with patch('redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            
            cache = L2Cache("redis://localhost:6379/0")
            
            # Test get
            mock_client.get.return_value = '{"test": "value"}'
            result = await cache.get("key1")
            assert result == {"test": "value"}
            
            # Test set
            mock_client.setex.return_value = True
            result = await cache.set("key1", {"test": "value"}, ttl=60)
            assert result is True
            
            # Test delete
            mock_client.delete.return_value = 1
            result = await cache.delete("key1")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in L2 cache"""
        with patch('redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            
            cache = L2Cache("redis://localhost:6379/0")
            
            # Test get error
            mock_client.get.side_effect = Exception("Redis error")
            result = await cache.get("key1")
            assert result is None
            
            # Test set error
            mock_client.setex.side_effect = Exception("Redis error")
            result = await cache.set("key1", "value", ttl=60)
            assert result is False

class TestLayeredCache:
    
    @pytest.fixture
    def layered_cache(self):
        with patch('redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            return LayeredCache("redis://localhost:6379/0", "test-region")
    
    @pytest.mark.asyncio
    async def test_get_set_delete(self, layered_cache):
        """Test basic layered cache operations"""
        # Test set
        result = await layered_cache.set("key1", "value1", ttl=60)
        assert result is True
        
        # Test get
        result = await layered_cache.get("key1")
        assert result == "value1"
        
        # Test delete
        result = await layered_cache.delete("key1")
        assert result is True
        
        # Test get after delete
        result = await layered_cache.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_or_set(self, layered_cache):
        """Test get_or_set with factory function"""
        call_count = 0
        
        async def factory():
            nonlocal call_count
            call_count += 1
            return f"value-{call_count}"
        
        # First call should use factory
        result = await layered_cache.get_or_set("key1", factory, ttl=60)
        assert result == "value-1"
        assert call_count == 1
        
        # Second call should use cache
        result = await layered_cache.get_or_set("key1", factory, ttl=60)
        assert result == "value-1"
        assert call_count == 1  # Should not call factory again
    
    @pytest.mark.asyncio
    async def test_single_flight_protection(self, layered_cache):
        """Test single-flight protection against thundering herd"""
        call_count = 0
        
        async def factory():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate slow operation
            return f"value-{call_count}"
        
        # Start multiple concurrent requests
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(layered_cache.get_or_set("key1", factory, ttl=60))
            tasks.append(task)
        
        # Wait for all tasks
        results = await asyncio.gather(*tasks)
        
        # All results should be the same
        assert all(r == "value-1" for r in results)
        assert call_count == 1  # Factory should only be called once
    
    @pytest.mark.asyncio
    async def test_cache_key_prefixing(self, layered_cache):
        """Test that cache keys are prefixed with region"""
        await layered_cache.set("key1", "value1", ttl=60)
        
        # Check that L1 cache has region-prefixed key
        assert "test-region:key1" in layered_cache.l1.cache
    
    def test_stats(self, layered_cache):
        """Test cache statistics"""
        stats = layered_cache.stats()
        assert "l1" in stats
        assert "l2" in stats
        assert "region" in stats
        assert stats["region"] == "test-region"

class TestCacheDecorator:
    
    @pytest.mark.asyncio
    async def test_cached_decorator(self):
        """Test the @cached decorator"""
        call_count = 0
        
        @cached(ttl=60)
        async def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result = await expensive_function(5)
        assert result == 10
        assert call_count == 1
        
        # Second call should use cache
        result = await expensive_function(5)
        assert result == 10
        assert call_count == 1  # Should not call function again
    
    @pytest.mark.asyncio
    async def test_cached_decorator_with_key_func(self):
        """Test the @cached decorator with custom key function"""
        call_count = 0
        
        def custom_key_func(x, y):
            return f"custom:{x}:{y}"
        
        @cached(ttl=60, key_func=custom_key_func)
        async def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call
        result = await expensive_function(5, 3)
        assert result == 8
        assert call_count == 1
        
        # Second call should use cache
        result = await expensive_function(5, 3)
        assert result == 8
        assert call_count == 1
