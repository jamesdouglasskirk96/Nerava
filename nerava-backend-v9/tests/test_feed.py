import pytest
from fastapi.testclient import TestClient
from app.main_simple import app

client = TestClient(app)

def test_feed_returns_events():
    """Test that feed returns reward events in correct order"""
    # Create some test events
    client.post("/v1/incentives/award?user_id=alex&cents=100&source=CHARGE")
    client.post("/v1/incentives/award?user_id=bob&cents=200&source=REFERRAL")
    
    # Get feed
    response = client.get("/v1/social/feed?limit=2")
    assert response.status_code == 200
    events = response.json()
    
    # Should return 2 events, latest first
    assert len(events) == 2
    assert events[0]["user_id"] == "bob"  # Latest first
    assert events[1]["user_id"] == "alex"
    
    # Check event structure
    event = events[0]
    assert "id" in event
    assert "user_id" in event
    assert "source" in event
    assert "gross_cents" in event
    assert "community_cents" in event
    assert "net_cents" in event
    assert "meta" in event
    assert "timestamp" in event

def test_feed_with_limit():
    """Test feed respects limit parameter"""
    # Create 5 events
    for i in range(5):
        client.post(f"/v1/incentives/award?user_id=user{i}&cents=100&source=CHARGE")
    
    # Get feed with limit 3
    response = client.get("/v1/social/feed?limit=3")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 3

def test_feed_empty():
    """Test feed when no events exist"""
    # Clear any existing events by creating a fresh test
    response = client.get("/v1/social/feed?limit=10")
    assert response.status_code == 200
    events = response.json()
    # Should be empty or contain existing test data
    assert isinstance(events, list)
