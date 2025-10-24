import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

import asyncio
from unittest.mock import patch, AsyncMock
from app.services.circuit_breaker import CircuitBreaker, HTTPCircuitBreaker

class TestCircuitBreaker:
    
    @pytest.fixture
    def circuit_breaker(self):
        return CircuitBreaker(failure_threshold=2, timeout=1, success_threshold=1)
    
    @pytest.mark.asyncio
    async def test_closed_state_allows_requests(self, circuit_breaker):
        """Test that CLOSED state allows requests"""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.value == "closed"
    
    @pytest.mark.asyncio
    async def test_failure_threshold_opens_circuit(self, circuit_breaker):
        """Test that reaching failure threshold opens circuit"""
        async def failing_func():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_func)
        assert circuit_breaker.state.value == "closed"
        
        # Second failure should open circuit
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_func)
        assert circuit_breaker.state.value == "open"
    
    @pytest.mark.asyncio
    async def test_open_state_blocks_requests(self, circuit_breaker):
        """Test that OPEN state blocks requests"""
        # Open the circuit
        circuit_breaker.state = circuit_breaker.state.__class__("open")
        circuit_breaker.failure_count = circuit_breaker.failure_threshold
        
        async def any_func():
            return "should not be called"
        
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(any_func)
    
    @pytest.mark.asyncio
    async def test_timeout_allows_half_open(self, circuit_breaker):
        """Test that timeout allows circuit to go half-open"""
        # Open the circuit
        circuit_breaker.state = circuit_breaker.state.__class__("open")
        circuit_breaker.failure_count = circuit_breaker.failure_threshold
        circuit_breaker.last_failure_time = 0  # Old timestamp
        
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.value == "half_open"
    
    @pytest.mark.asyncio
    async def test_success_threshold_closes_circuit(self, circuit_breaker):
        """Test that success threshold closes circuit"""
        # Set to half-open
        circuit_breaker.state = circuit_breaker.state.__class__("half_open")
        
        async def success_func():
            return "success"
        
        # First success
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state.value == "closed"

class TestHTTPCircuitBreaker:
    
    @pytest.fixture
    def http_circuit_breaker(self):
        return HTTPCircuitBreaker("http://test.com", failure_threshold=2, timeout=1)
    
    @pytest.mark.asyncio
    async def test_get_request_success(self, http_circuit_breaker):
        """Test successful GET request"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "test"}
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            response = await http_circuit_breaker.get("/test")
            
            assert response.status_code == 200
            assert response.json() == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_post_request_success(self, http_circuit_breaker):
        """Test successful POST request"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": "123"}
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            response = await http_circuit_breaker.post("/test", json={"data": "test"})
            
            assert response.status_code == 201
            assert response.json() == {"id": "123"}
    
    @pytest.mark.asyncio
    async def test_request_failure_opens_circuit(self, http_circuit_breaker):
        """Test that request failures open circuit"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            # First failure
            with pytest.raises(Exception):
                await http_circuit_breaker.get("/test")
            
            # Second failure should open circuit
            with pytest.raises(Exception):
                await http_circuit_breaker.get("/test")
            
            assert http_circuit_breaker.circuit_breaker.state.value == "open"
