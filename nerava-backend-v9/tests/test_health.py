"""
Tests for health and pilot status endpoints.

Uses conftest fixtures for test database isolation.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_ok(client: TestClient):
    """Test that /health endpoint returns 200 with required keys."""
    response = client.get("/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "status" in data
    assert "db" in data
    assert data["status"] == "ok"
    assert data["db"] == "ok"


def test_pilot_status(client: TestClient):
    """Test that /v1/pilot/status returns pilot mode and hub configuration."""
    response = client.get("/v1/pilot/status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "pilot_mode" in data
    assert "pilot_hub" in data
    assert "domain_seeded" in data
    
    # Check types
    assert isinstance(data["pilot_mode"], bool)
    assert isinstance(data["pilot_hub"], str)
    assert isinstance(data["domain_seeded"], bool)
