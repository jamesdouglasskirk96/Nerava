import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

from unittest.mock import patch, AsyncMock
from app.services.idempotency import IdempotencyService

class TestIdempotencyService:
    
    @pytest.fixture
    def idempotency_service(self):
        with patch('app.services.cache.cache') as mock_cache:
            service = IdempotencyService(ttl_seconds=60)
            service.cache = mock_cache
            return service
    
    @pytest.mark.asyncio
    async def test_duplicate_operation_returns_cached_result(self, idempotency_service):
        """Test that duplicate operations return cached results"""
        # Mock cache to return existing result
        idempotency_service.cache.get.return_value = {
            "status": "completed",
            "result": {"session_id": "test-123", "total_reward_usd": 5.50}
        }
        
        operation = "charge-stop"
        payload = {"session_id": "test-123", "kwh_consumed": 10.0}
        
        result = await idempotency_service.get_result(operation, payload)
        
        assert result is not None
        assert result["session_id"] == "test-123"
        assert result["total_reward_usd"] == 5.50
    
    @pytest.mark.asyncio
    async def test_new_operation_returns_none(self, idempotency_service):
        """Test that new operations return None"""
        # Mock cache to return None (no existing result)
        idempotency_service.cache.get.return_value = None
        
        operation = "charge-stop"
        payload = {"session_id": "test-456", "kwh_consumed": 15.0}
        
        result = await idempotency_service.get_result(operation, payload)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_store_result(self, idempotency_service):
        """Test that results are stored correctly"""
        operation = "charge-stop"
        payload = {"session_id": "test-789", "kwh_consumed": 20.0}
        result = {"session_id": "test-789", "total_reward_usd": 8.75}
        
        await idempotency_service.store_result(operation, payload, result)
        
        # Verify cache.setex was called
        idempotency_service.cache.setex.assert_called_once()
        call_args = idempotency_service.cache.setex.call_args
        
        # Check that the key contains the operation
        assert "idempotency:" in call_args[0][0]
        assert call_args[0][1] == 60  # TTL
        assert call_args[0][2]["status"] == "completed"
        assert call_args[0][2]["result"] == result
    
    @pytest.mark.asyncio
    async def test_generate_key_consistency(self, idempotency_service):
        """Test that the same operation and payload generate the same key"""
        operation = "charge-stop"
        payload = {"session_id": "test-123", "kwh_consumed": 10.0}
        
        key1 = idempotency_service._generate_key(operation, payload)
        key2 = idempotency_service._generate_key(operation, payload)
        
        assert key1 == key2
        assert key1.startswith("idempotency:")
    
    @pytest.mark.asyncio
    async def test_different_payloads_generate_different_keys(self, idempotency_service):
        """Test that different payloads generate different keys"""
        operation = "charge-stop"
        payload1 = {"session_id": "test-123", "kwh_consumed": 10.0}
        payload2 = {"session_id": "test-123", "kwh_consumed": 15.0}
        
        key1 = idempotency_service._generate_key(operation, payload1)
        key2 = idempotency_service._generate_key(operation, payload2)
        
        assert key1 != key2
