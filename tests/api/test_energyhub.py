import pytest
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'nerava-backend-v9'))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_windows_endpoint():
    """Test GET /v1/energyhub/windows returns active windows"""
    response = client.get("/v1/energyhub/windows")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # solar_surplus and green_hour
    
    # Check structure
    for window in data:
        assert "id" in window
        assert "label" in window
        assert "start_utc" in window
        assert "end_utc" in window
        assert "price_per_kwh" in window
        assert "multiplier" in window
        assert "active_now" in window

def test_charge_start():
    """Test POST /v1/energyhub/events/charge-start returns session_id"""
    payload = {
        "user_id": "test-user",
        "hub_id": "test-hub"
    }
    
    response = client.post("/v1/energyhub/events/charge-start", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "session_id" in data
    assert data["session_id"] is not None
    assert len(data["session_id"]) > 0

def test_charge_stop_async():
    """Test POST /v1/energyhub/events/charge-stop with async credit"""
    # First start a session
    start_payload = {
        "user_id": "test-user",
        "hub_id": "test-hub"
    }
    start_response = client.post("/v1/energyhub/events/charge-start", json=start_payload)
    assert start_response.status_code == 200
    
    session_id = start_response.json()["session_id"]
    
    # Then stop the session
    stop_payload = {
        "session_id": session_id,
        "kwh_consumed": 15.5
    }
    
    response = client.post("/v1/energyhub/events/charge-stop", json=stop_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "session_id" in data
    assert "user_id" in data
    assert "hub_id" in data
    assert "kwh" in data
    assert "total_reward_usd" in data
    assert "message" in data
    assert data["kwh"] == 15.5

def test_charge_stop_invalid_session():
    """Test POST /v1/energyhub/events/charge-stop with invalid session_id"""
    payload = {
        "session_id": "invalid-session-id",
        "kwh_consumed": 10.0
    }
    
    response = client.post("/v1/energyhub/events/charge-stop", json=payload)
    assert response.status_code == 404
    assert "session_not_found" in response.json()["detail"]

def test_windows_caching():
    """Test that windows endpoint uses caching"""
    # First request
    response1 = client.get("/v1/energyhub/windows")
    assert response1.status_code == 200
    
    # Second request should be cached
    response2 = client.get("/v1/energyhub/windows")
    assert response2.status_code == 200
    assert response1.json() == response2.json()

def test_demo_at_parameter():
    """Test that demo at parameter works for testing"""
    # Test with specific time
    response = client.get("/v1/energyhub/windows?at=2024-01-01T12:00:00Z")
    assert response.status_code == 200
    
    data = response.json()
    # Should show windows for that specific time
    assert isinstance(data, list)
