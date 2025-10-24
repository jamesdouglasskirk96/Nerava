"""Test demo autorun functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models_demo import DemoState
from app.core.config import settings

client = TestClient(app)

@pytest.fixture
def demo_headers():
    """Demo API headers."""
    return {"X-API-Key": "demo-key", "Authorization": "Bearer demo-token"}

def test_autorun_start_stop():
    """Test autorun start/stop endpoints."""
    # Start autorun
    response = client.post("/v1/demo/autorun/start", headers=demo_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is True
    assert "session_id" in data
    
    # Check status
    response = client.get("/v1/demo/autorun/status", headers=demo_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is True
    
    # Stop autorun
    response = client.post("/v1/demo/autorun/stop", headers=demo_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False

def test_autorun_scenarios():
    """Test autorun scenario switching."""
    # Start autorun
    response = client.post("/v1/demo/autorun/start", headers=demo_headers)
    assert response.status_code == 200
    
    # Set scenario
    response = client.post("/v1/demo/autorun/scenario", 
                          json={"scenario": "peak_grid"}, 
                          headers=demo_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "peak_grid"
    
    # Get status
    response = client.get("/v1/demo/autorun/status", headers=demo_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "peak_grid"

def test_autorun_unauthorized():
    """Test autorun endpoints require demo mode."""
    # Without demo headers
    response = client.post("/v1/demo/autorun/start")
    assert response.status_code == 403
    
    response = client.get("/v1/demo/autorun/status")
    assert response.status_code == 403

def test_autorun_script_execution():
    """Test autorun script execution."""
    # Start autorun
    response = client.post("/v1/demo/autorun/start", headers=demo_headers)
    assert response.status_code == 200
    
    # Execute script
    response = client.post("/v1/demo/autorun/execute", 
                          json={"script": "investor_tour"}, 
                          headers=demo_headers)
    assert response.status_code == 200
    data = response.json()
    assert "executed" in data
    assert "duration_ms" in data

def test_autorun_polling():
    """Test autorun polling endpoint."""
    # Start autorun
    response = client.post("/v1/demo/autorun/start", headers=demo_headers)
    assert response.status_code == 200
    
    # Poll for updates
    response = client.get("/v1/demo/autorun/poll", headers=demo_headers)
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
    assert "scenario" in data
    assert "last_activity" in data

def test_autorun_cleanup():
    """Test autorun cleanup on stop."""
    # Start autorun
    response = client.post("/v1/demo/autorun/start", headers=demo_headers)
    assert response.status_code == 200
    
    # Stop autorun
    response = client.post("/v1/demo/autorun/stop", headers=demo_headers)
    assert response.status_code == 200
    
    # Check status is stopped
    response = client.get("/v1/demo/autorun/status", headers=demo_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
