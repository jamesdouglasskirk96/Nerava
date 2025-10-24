import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

from fastapi.testclient import TestClient
from app.main import app
from app.middleware.region import RegionMiddleware, ReadWriteRoutingMiddleware, CanaryRoutingMiddleware
from app.db.routing import DatabaseRouter

client = TestClient(app)

def test_region_headers():
    """Test that region headers are added to responses"""
    response = client.get("/v1/energyhub/windows")
    
    # Check region headers
    assert "X-Region" in response.headers
    assert "X-Primary-Region" in response.headers
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time" in response.headers
    
    # Check header values are reasonable
    assert response.headers["X-Region"] is not None
    assert response.headers["X-Primary-Region"] is not None
    assert response.headers["X-Request-ID"] is not None
    assert response.headers["X-Response-Time"].isdigit()

def test_request_id_preservation():
    """Test that existing request IDs are preserved"""
    request_id = "test-request-123"
    response = client.get("/v1/energyhub/windows", headers={"X-Request-ID": request_id})
    
    assert response.headers["X-Request-ID"] == request_id

def test_flags_endpoint():
    """Test the flags endpoint returns configuration"""
    response = client.get("/v1/flags/")
    assert response.status_code == 200
    
    data = response.json()
    assert "region" in data
    assert "primary_region" in data
    assert "enable_multi_region" in data
    assert "events_driver" in data
    assert "enable_sync_credit" in data

def test_health_flags_endpoint():
    """Test the health flags endpoint"""
    response = client.get("/v1/flags/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "region" in data
    assert "primary_region" in data
    assert "database_connected" in data
    assert "redis_connected" in data
    assert "canary_enabled" in data
    assert "maintenance_mode" in data

def test_read_write_routing_middleware():
    """Test read/write routing middleware"""
    middleware = ReadWriteRoutingMiddleware(app)
    
    # Test write operation detection
    from fastapi import Request
    from unittest.mock import MagicMock
    
    # Mock request for write operation
    write_request = MagicMock()
    write_request.method = "POST"
    write_request.url.path = "/v1/energyhub/events/charge-start"
    
    assert middleware._is_write_operation(write_request) is True
    
    # Mock request for read operation
    read_request = MagicMock()
    read_request.method = "GET"
    read_request.url.path = "/v1/energyhub/windows"
    
    assert middleware._is_write_operation(read_request) is False

def test_canary_routing_middleware():
    """Test canary routing middleware"""
    middleware = CanaryRoutingMiddleware(app, canary_percentage=0.5)
    
    # Test canary header detection
    from fastapi import Request
    from unittest.mock import MagicMock
    
    # Mock request with canary header
    canary_request = MagicMock()
    canary_request.headers = {"X-Canary-Version": "v2.0.0"}
    
    # Test canary detection
    assert middleware._detect_canary(canary_request) is True
    
    # Mock request without canary header
    normal_request = MagicMock()
    normal_request.headers = {}
    
    # Test normal request
    assert middleware._detect_canary(normal_request) is False

def test_database_router():
    """Test database router functionality"""
    router = DatabaseRouter()
    
    # Test session creation
    session = router.get_session(use_primary=True)
    assert session is not None
    
    # Test engine selection
    engine = router.get_engine(use_primary=True)
    assert engine is not None
    
    # Test health check
    health = router.health_check()
    assert "primary" in health
    assert "read_replica" in health
    assert "healthy" in health["primary"]
    assert "healthy" in health["read_replica"]

def test_multi_region_configuration():
    """Test multi-region configuration"""
    response = client.get("/v1/flags/")
    data = response.json()
    
    # Check that multi-region flag is set correctly
    if data["region"] != data["primary_region"]:
        assert data["enable_multi_region"] is True
    else:
        assert data["enable_multi_region"] is False

def test_canary_headers():
    """Test that canary headers are added to responses"""
    response = client.get("/v1/energyhub/windows")
    
    # Check canary headers
    assert "X-Canary-Request" in response.headers
    assert "X-Canary-Version" in response.headers
    
    # Check header values
    assert response.headers["X-Canary-Request"] in ["true", "false"]
    assert response.headers["X-Canary-Version"] in ["canary", "stable"]

def test_region_middleware_order():
    """Test that middleware is applied in correct order"""
    # This test verifies that the middleware stack is properly configured
    # by checking that all expected headers are present
    response = client.get("/v1/energyhub/windows")
    
    # All middleware should add their headers
    expected_headers = [
        "X-Request-ID",
        "X-Region", 
        "X-Primary-Region",
        "X-Response-Time",
        "X-Canary-Request",
        "X-Canary-Version"
    ]
    
    for header in expected_headers:
        assert header in response.headers, f"Missing header: {header}"
