import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_metrics_middleware_emits_histograms():
    """Test that metrics middleware emits Prometheus histograms"""
    # Make a request to trigger middleware
    response = client.get("/v1/energyhub/windows")
    assert response.status_code == 200
    
    # Check that metrics endpoint exists
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    
    # Check that metrics contain expected data
    metrics_text = metrics_response.text
    assert "http_requests_total" in metrics_text
    assert "http_request_duration_seconds" in metrics_text
    assert "http_active_requests" in metrics_text

def test_metrics_endpoint_format():
    """Test that metrics endpoint returns proper Prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    
    # Check for specific metric types
    metrics_text = response.text
    assert "# TYPE http_requests_total counter" in metrics_text
    assert "# TYPE http_request_duration_seconds histogram" in metrics_text
    assert "# TYPE http_active_requests gauge" in metrics_text

def test_metrics_increment_on_requests():
    """Test that metrics increment with each request"""
    # Get initial metrics
    initial_response = client.get("/metrics")
    initial_text = initial_response.text
    
    # Make some requests
    for _ in range(3):
        client.get("/v1/energyhub/windows")
    
    # Get updated metrics
    updated_response = client.get("/metrics")
    updated_text = updated_response.text
    
    # Metrics should have increased
    assert len(updated_text) > len(initial_text)

def test_metrics_include_endpoint_labels():
    """Test that metrics include proper endpoint labels"""
    # Make requests to different endpoints
    client.get("/v1/energyhub/windows")
    client.post("/v1/energyhub/events/charge-start", json={"user_id": "test", "hub_id": "test"})
    
    # Check metrics
    response = client.get("/metrics")
    metrics_text = response.text
    
    # Should include endpoint labels
    assert "endpoint=\"/v1/energyhub/windows\"" in metrics_text
    assert "endpoint=\"/v1/energyhub/events/charge-start\"" in metrics_text

def test_active_requests_gauge():
    """Test that active requests gauge works correctly"""
    # Initially should be 0 or low
    response = client.get("/metrics")
    metrics_text = response.text
    
    # Should contain active requests metric
    assert "http_active_requests" in metrics_text
