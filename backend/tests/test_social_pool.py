import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main_simple import app
from app.db import get_db
from app.models_extra import Follow, RewardEvent, FollowerShare, CommunityPeriod

client = TestClient(app)

def test_follow_toggle():
    """Test follow/unfollow functionality"""
    # Follow
    response = client.post("/v1/social/follow", json={
        "follower_id": "jane",
        "followee_id": "alex", 
        "follow": True
    })
    assert response.status_code == 200
    assert response.json()["following"] == True
    
    # Unfollow
    response = client.post("/v1/social/follow", json={
        "follower_id": "jane",
        "followee_id": "alex",
        "follow": False
    })
    assert response.status_code == 200
    assert response.json()["following"] == False

def test_followers_following():
    """Test getting followers and following lists"""
    # Create a follow relationship
    client.post("/v1/social/follow", json={
        "follower_id": "jane",
        "followee_id": "alex",
        "follow": True
    })
    
    # Get followers of alex
    response = client.get("/v1/social/followers?user_id=alex")
    assert response.status_code == 200
    followers = response.json()
    assert len(followers) == 1
    assert followers[0]["follower_id"] == "jane"
    
    # Get who jane is following
    response = client.get("/v1/social/following?user_id=jane")
    assert response.status_code == 200
    following = response.json()
    assert len(following) == 1
    assert following[0]["followee_id"] == "alex"

def test_award_with_community():
    """Test award endpoint with community pool distribution"""
    # Create follow relationship first
    client.post("/v1/social/follow", json={
        "follower_id": "jane",
        "followee_id": "alex",
        "follow": True
    })
    
    # Award to alex
    response = client.post("/v1/incentives/award?user_id=alex&cents=100&source=CHARGE")
    assert response.status_code == 200
    data = response.json()
    assert data["gross_cents"] == 100
    assert data["net_cents"] == 90  # 90% to user
    assert data["community_cents"] == 10  # 10% to community
    assert data["user_id"] == "alex"
    assert data["source"] == "CHARGE"

def test_settle_shares():
    """Test settlement of follower shares"""
    # Create follow and award first
    client.post("/v1/social/follow", json={
        "follower_id": "jane",
        "followee_id": "alex",
        "follow": True
    })
    client.post("/v1/incentives/award?user_id=alex&cents=100&source=CHARGE")
    
    # Settle shares
    response = client.post("/v1/admin/settle")
    assert response.status_code == 200
    data = response.json()
    assert data["settled"] >= 1  # jane should get at least 1 share

def test_community_pool():
    """Test community pool statistics"""
    # Create follow and award first
    client.post("/v1/social/follow", json={
        "follower_id": "jane",
        "followee_id": "alex",
        "follow": True
    })
    client.post("/v1/incentives/award?user_id=alex&cents=100&source=CHARGE")
    
    # Get pool stats
    response = client.get("/v1/social/pool")
    assert response.status_code == 200
    data = response.json()
    assert data["total_gross_cents"] >= 100  # At least our test amount
    assert data["total_community_cents"] >= 10  # At least our test amount
    assert data["total_distributed_cents"] >= 0
