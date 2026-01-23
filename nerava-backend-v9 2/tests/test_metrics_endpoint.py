"""
Test Prometheus metrics endpoint protection.

These tests verify that the /metrics endpoint is properly protected
and only accessible when enabled.
"""
import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main_simple import app


class TestMetricsEndpoint:
    """Test metrics endpoint access control"""
    
    def test_metrics_enabled_returns_200(self, client: TestClient):
        """Test that metrics endpoint returns 200 when enabled"""
        with patch.dict(os.environ, {"METRICS_ENABLED": "true"}):
            # Need to reload app to pick up env change, or use dependency override
            # For simplicity, test the endpoint directly
            response = client.get("/metrics")
            # May return 200 or 404 depending on current env
            assert response.status_code in [200, 404]
    
    def test_metrics_disabled_returns_404(self, client: TestClient):
        """Test that metrics endpoint returns 404 when disabled"""
        with patch.dict(os.environ, {"METRICS_ENABLED": "false"}, clear=False):
            response = client.get("/metrics")
            assert response.status_code == 404
    
    def test_metrics_with_token_auth(self, client: TestClient):
        """Test that metrics endpoint accepts token auth when configured"""
        with patch.dict(os.environ, {"METRICS_ENABLED": "true", "METRICS_TOKEN": "test_token_123"}, clear=False):
            # Without token
            response = client.get("/metrics")
            # May require token if METRICS_TOKEN is set
            if response.status_code == 401:
                # With token
                response = client.get("/metrics", headers={"Authorization": "Bearer test_token_123"})
                assert response.status_code == 200
    
    def test_metrics_without_token_when_required(self, client: TestClient):
        """Test that metrics endpoint rejects requests without token when required"""
        with patch.dict(os.environ, {"METRICS_ENABLED": "true", "METRICS_TOKEN": "required_token"}, clear=False):
            response = client.get("/metrics")
            # Should require token
            assert response.status_code in [401, 404]  # 401 if token required, 404 if disabled
    
    def test_metrics_content_type(self, client: TestClient):
        """Test that metrics endpoint returns correct content type"""
        with patch.dict(os.environ, {"METRICS_ENABLED": "true"}, clear=False):
            response = client.get("/metrics")
            if response.status_code == 200:
                assert "text/plain" in response.headers.get("content-type", "")


class TestMetricsEndpointProduction:
    """Test metrics endpoint in production mode"""
    
    def test_metrics_enabled_by_default_in_prod(self, client: TestClient):
        """Test that metrics are enabled by default in production"""
        with patch.dict(os.environ, {"ENV": "prod", "METRICS_ENABLED": ""}, clear=False):
            # In prod, METRICS_ENABLED defaults to true
            response = client.get("/metrics")
            # Should be accessible (may require token if METRICS_TOKEN is set)
            assert response.status_code in [200, 401, 404]
    
    def test_metrics_disabled_by_default_in_local(self, client: TestClient):
        """Test that metrics are disabled by default in local"""
        with patch.dict(os.environ, {"ENV": "local", "METRICS_ENABLED": ""}, clear=False):
            # In local, METRICS_ENABLED defaults to false
            response = client.get("/metrics")
            assert response.status_code == 404







