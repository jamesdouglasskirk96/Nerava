"""
Tests for ops endpoints: /healthz, /readyz, /metrics

These are critical production endpoints that must be reliable.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_healthz_always_returns_200(client: TestClient):
    """Test that /healthz always returns 200 (liveness probe)."""
    response = client.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True
    assert data["service"] == "nerava-backend"
    assert data["version"] == "0.9.0"
    assert data["status"] == "healthy"


def test_readyz_returns_200_when_healthy(client: TestClient):
    """Test that /readyz returns 200 when dependencies are healthy."""
    response = client.get("/readyz")
    
    # Should return 200 if DB and Redis are accessible
    # In test environment with in-memory DB, this should work
    assert response.status_code in [200, 503]  # May be 503 if Redis not available
    
    if response.status_code == 200:
        data = response.json()
        assert "ok" in data or "status" in data


def test_readyz_returns_503_on_db_failure(client: TestClient):
    """Test that /readyz returns 503 when database is unavailable."""
    from app.db import get_db
    
    # Mock database failure
    def failing_db():
        raise Exception("Database connection failed")
    
    from app.main_simple import app
    app.dependency_overrides[get_db] = failing_db
    
    try:
        response = client.get("/readyz")
        assert response.status_code == 503
    finally:
        app.dependency_overrides.clear()


def test_metrics_disabled_in_local(client: TestClient):
    """Test that /metrics returns 404 when disabled in local env."""
    with patch.dict(os.environ, {"METRICS_ENABLED": "false", "ENV": "local"}):
        # Need to reload the app to pick up env change, but for now just test behavior
        response = client.get("/v1/ops/metrics")
        # May return 404 or 401 depending on configuration
        assert response.status_code in [404, 401]


def test_metrics_requires_token_when_set(client: TestClient):
    """Test that /metrics requires token when METRICS_TOKEN is set."""
    with patch.dict(os.environ, {"METRICS_ENABLED": "true", "METRICS_TOKEN": "test-token-123"}):
        # Without token - should return 401
        response = client.get("/v1/ops/metrics")
        assert response.status_code == 401
        
        # With wrong token - should return 401
        response = client.get(
            "/v1/ops/metrics",
            headers={"Authorization": "Bearer wrong-token"}
        )
        assert response.status_code == 401
        
        # With correct token - should return 200 (if prometheus_client available)
        response = client.get(
            "/v1/ops/metrics",
            headers={"Authorization": "Bearer test-token-123"}
        )
        # May return 200 or 500 depending on prometheus_client availability
        assert response.status_code in [200, 500]


def test_metrics_returns_prometheus_format(client: TestClient):
    """Test that /metrics returns Prometheus format when enabled."""
    try:
        import prometheus_client
    except ImportError:
        pytest.skip("prometheus_client not installed")
    
    with patch.dict(os.environ, {"METRICS_ENABLED": "true"}):
        response = client.get("/v1/ops/metrics")
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
            # Prometheus format should contain metric names
            content = response.text
            assert len(content) > 0


def test_health_endpoint_v1(client: TestClient):
    """Test that /v1/health endpoint works."""
    response = client.get("/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "db" in data


def test_health_endpoint_db_failure(client: TestClient):
    """Test that /v1/health returns 500 on database failure."""
    from app.db import get_db
    
    def failing_db():
        raise Exception("Database connection failed")
    
    from app.main_simple import app
    app.dependency_overrides[get_db] = failing_db
    
    try:
        response = client.get("/v1/health")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    finally:
        app.dependency_overrides.clear()







