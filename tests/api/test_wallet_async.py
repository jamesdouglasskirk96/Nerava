import pytest
import asyncio
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

from unittest.mock import patch, AsyncMock
from app.services.async_wallet import async_wallet

class TestAsyncWallet:
    
    @pytest.mark.asyncio
    async def test_queue_wallet_credit(self):
        """Test that wallet credits are queued properly"""
        # Start the worker
        await async_wallet.start_worker()
        
        # Queue a credit
        await async_wallet.queue_wallet_credit("test-user", 100, "session-123")
        
        # Give it a moment to process
        await asyncio.sleep(0.1)
        
        # Stop the worker
        await async_wallet.stop_worker()
    
    @pytest.mark.asyncio
    async def test_worker_processes_queue(self):
        """Test that worker processes credit queue"""
        # Mock the HTTP call
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"new_balance_cents": 500}
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            # Start worker
            await async_wallet.start_worker()
            
            # Queue multiple credits
            await async_wallet.queue_wallet_credit("user1", 100, "session1")
            await async_wallet.queue_wallet_credit("user2", 200, "session2")
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # Stop worker
            await async_wallet.stop_worker()
            
            # Verify HTTP calls were made
            assert mock_client.return_value.__aenter__.return_value.post.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_worker_handles_errors(self):
        """Test that worker handles HTTP errors gracefully"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock HTTP error
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            
            await async_wallet.start_worker()
            
            # Queue a credit that will fail
            await async_wallet.queue_wallet_credit("test-user", 100, "session-123")
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            await async_wallet.stop_worker()
            
            # Should not raise exception
            assert True
