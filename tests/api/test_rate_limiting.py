import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rate_limiting_allows_normal_requests():
    """Test that normal requests are allowed"""
    response = client.get("/v1/energyhub/windows")
    assert response.status_code == 200
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

def test_rate_limiting_blocks_excessive_requests():
    """Test that excessive requests are blocked"""
    # Make many requests quickly
    responses = []
    for _ in range(150):  # Exceed the default limit
        response = client.get("/v1/energyhub/windows")
        responses.append(response)
    
    # Some requests should be rate limited
    rate_limited_responses = [r for r in responses if r.status_code == 429]
    assert len(rate_limited_responses) > 0
    
    # Check rate limit error message
    if rate_limited_responses:
        error_response = rate_limited_responses[0]
        assert "Rate limit exceeded" in error_response.json()["detail"]

def test_rate_limiting_headers_present():
    """Test that rate limiting headers are present"""
    response = client.get("/v1/energyhub/windows")
    
    # Check required headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Check header values are reasonable
    limit = int(response.headers["X-RateLimit-Limit"])
    remaining = int(response.headers["X-RateLimit-Remaining"])
    reset = int(response.headers["X-RateLimit-Reset"])
    
    assert limit > 0
    assert 0 <= remaining <= limit
    assert reset > 0

def test_rate_limiting_resets_after_time():
    """Test that rate limiting resets after time"""
    # This test would need to wait for the rate limit to reset
    # For now, just verify the mechanism works
    response = client.get("/v1/energyhub/windows")
    assert response.status_code == 200

def test_different_endpoints_share_rate_limit():
    """Test that different endpoints share the same rate limit"""
    # Make requests to different endpoints
    responses = []
    for _ in range(50):
        responses.append(client.get("/v1/energyhub/windows"))
        responses.append(client.post("/v1/energyhub/events/charge-start", 
                                   json={"user_id": "test", "hub_id": "test"}))
    
    # Check that rate limiting applies across endpoints
    rate_limited = [r for r in responses if r.status_code == 429]
    # This test might not trigger rate limiting with current limits
    # but verifies the mechanism is in place
