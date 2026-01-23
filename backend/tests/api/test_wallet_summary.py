"""
Tests for GET /v1/drivers/me/wallet/summary endpoint
"""
import pytest
from datetime import datetime
from freezegun import freeze_time
from zoneinfo import ZoneInfo

from app.models.domain import DriverWallet
from app.models import User
from app.models_domain import DomainChargingSession
from app.dependencies.driver import get_current_driver


@pytest.fixture
def authenticated_user(db, test_user):
    """Override auth dependency to return test_user"""
    from app.main_simple import app
    
    def override_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = override_get_current_driver
    
    yield test_user
    
    app.dependency_overrides.clear()


def test_wallet_summary_authenticated_contract(db, authenticated_user, client):
    """Test that authenticated call returns all required fields with correct types"""
    # Create wallet
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1500,
        energy_reputation_score=250,
        charging_detected=True
    )
    db.add(wallet)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all required fields exist
    assert "nova_balance" in data
    assert "nova_balance_cents" in data
    assert "conversion_rate_cents" in data
    assert "usd_equivalent" in data
    assert "charging_detected" in data
    assert "offpeak_active" in data
    assert "window_ends_in_seconds" in data
    assert "reputation" in data
    assert "recent_activity" in data
    assert "last_updated_at" in data
    
    # Check types
    assert isinstance(data["nova_balance"], int)
    assert isinstance(data["nova_balance_cents"], int)
    assert isinstance(data["conversion_rate_cents"], int)
    assert isinstance(data["usd_equivalent"], str)
    assert isinstance(data["charging_detected"], bool)
    assert isinstance(data["offpeak_active"], bool)
    assert isinstance(data["window_ends_in_seconds"], int)
    assert isinstance(data["reputation"], dict)
    assert isinstance(data["recent_activity"], list)
    assert isinstance(data["last_updated_at"], str)
    
    # Check reputation structure (full object with all fields)
    assert "tier" in data["reputation"]
    assert "tier_color" in data["reputation"]
    assert "points" in data["reputation"]
    assert "next_tier" in data["reputation"]
    assert "points_to_next" in data["reputation"]
    assert "progress_to_next" in data["reputation"]
    assert isinstance(data["reputation"]["tier"], str)
    assert isinstance(data["reputation"]["tier_color"], str)
    assert isinstance(data["reputation"]["points"], int)
    assert isinstance(data["reputation"]["progress_to_next"], (int, float))
    # next_tier and points_to_next can be None for Platinum
    assert data["reputation"]["tier"] in ["Bronze", "Silver", "Gold", "Platinum"]
    
    # Check USD equivalent format
    assert data["usd_equivalent"].startswith("$")
    assert "." in data["usd_equivalent"]


@pytest.mark.parametrize("score,expected_tier,expected_points_to_next", [
    (0, "Bronze", 100),
    (99, "Bronze", 1),
    (100, "Silver", 200),
    (299, "Silver", 1),
    (300, "Gold", 400),
    (699, "Gold", 1),
    (700, "Platinum", 0),
    (1000, "Platinum", 0),
])
def test_wallet_summary_tier_mapping(db, authenticated_user, client, score, expected_tier, expected_points_to_next):
    """Test reputation tier mapping for various scores"""
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1000,
        energy_reputation_score=score,
        charging_detected=False
    )
    db.add(wallet)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["reputation"]["tier"] == expected_tier
    assert data["reputation"]["points"] == score
    assert data["reputation"]["points_to_next"] == expected_points_to_next


@freeze_time("2025-01-15 23:00:00")  # 11 PM - in off-peak window
def test_wallet_summary_offpeak_window_end_offpeak(db, authenticated_user, client):
    """Test off-peak window calculation when currently in off-peak"""
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1000,
        energy_reputation_score=100,
        charging_detected=False
    )
    db.add(wallet)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be in off-peak (23:00 is between 22:00 and 06:00)
    assert data["offpeak_active"] is True
    # Window ends at 06:00 next day = 7 hours = 25200 seconds
    assert data["window_ends_in_seconds"] > 0
    assert data["window_ends_in_seconds"] <= 25200  # Should be <= 7 hours


@freeze_time("2025-01-15 14:00:00")  # 2 PM - in peak hours
def test_wallet_summary_offpeak_window_end_peak(db, authenticated_user, client):
    """Test off-peak window calculation when currently in peak"""
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1000,
        energy_reputation_score=100,
        charging_detected=False
    )
    db.add(wallet)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be in peak (14:00 is between 06:00 and 22:00)
    assert data["offpeak_active"] is False
    # Window ends at 06:00 next morning = 16 hours from 14:00 = 57600 seconds
    assert data["window_ends_in_seconds"] > 0
    assert data["window_ends_in_seconds"] >= 57600  # Should be >= 16 hours (14:00 to 06:00 next day)
    assert data["window_ends_in_seconds"] < 86400  # Should be < 24 hours


def test_wallet_summary_charging_detected_reflects_wallet(db, authenticated_user, client):
    """Test that charging_detected reflects wallet state"""
    # Test with charging_detected=True
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1000,
        energy_reputation_score=100,
        charging_detected=True
    )
    db.add(wallet)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["charging_detected"] is True
    
    # Update to False
    wallet.charging_detected = False
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["charging_detected"] is False


def test_wallet_summary_activity_limit_5(db, authenticated_user, client):
    """Test that recent_activity is limited to 5 items"""
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1000,
        energy_reputation_score=100,
        charging_detected=False
    )
    db.add(wallet)
    db.commit()
    
    # Create 7 charging sessions
    for i in range(7):
        session = DomainChargingSession(
            id=f"session_{i}",
            driver_user_id=authenticated_user.id,
            charger_provider="test",
            start_time=datetime.utcnow(),
            verified=False
        )
        db.add(session)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return at most 5 items
    assert len(data["recent_activity"]) <= 5
    assert len(data["recent_activity"]) == 5  # Should be exactly 5 if we have 7


def test_wallet_summary_handles_null_score(db, authenticated_user, client):
    """Test that null/zero reputation score returns Bronze tier without error"""
    # Create wallet with no reputation score (None)
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1000,
        energy_reputation_score=None,
        charging_detected=False
    )
    db.add(wallet)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert "reputation" in data
    assert data["reputation"]["tier"] == "Bronze"
    assert data["reputation"]["points"] == 0
    assert data["reputation"]["tier_color"] == "#78716c"  # Bronze color
    assert data["reputation"]["next_tier"] == "Silver"
    assert data["reputation"]["points_to_next"] == 100


def test_wallet_summary_reputation_structure(db, authenticated_user, client):
    """Test that reputation object has all required fields with correct types"""
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1000,
        energy_reputation_score=142,  # Silver tier
        charging_detected=False
    )
    db.add(wallet)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    
    assert response.status_code == 200
    data = response.json()
    rep = data["reputation"]
    
    # Required fields
    assert "points" in rep
    assert "tier" in rep
    assert "tier_color" in rep
    assert "next_tier" in rep
    assert "points_to_next" in rep
    assert "progress_to_next" in rep
    
    # Types
    assert isinstance(rep["points"], int)
    assert isinstance(rep["tier"], str)
    assert isinstance(rep["tier_color"], str)
    assert isinstance(rep["progress_to_next"], (int, float))
    
    # Values
    assert rep["points"] == 142
    assert rep["tier"] == "Silver"
    assert rep["tier_color"] == "#64748b"
    assert rep["next_tier"] == "Gold"
    assert rep["points_to_next"] == 158
    assert 0.0 <= rep["progress_to_next"] <= 1.0


def test_wallet_summary_platinum_returns_max_progress(db, authenticated_user, client):
    """Test that Platinum tier returns progress_to_next = 1.0 and next_tier = None"""
    wallet = DriverWallet(
        user_id=authenticated_user.id,
        nova_balance=1000,
        energy_reputation_score=700,  # Platinum tier
        charging_detected=False
    )
    db.add(wallet)
    db.commit()
    
    response = client.get("/v1/drivers/me/wallet/summary")
    
    assert response.status_code == 200
    data = response.json()
    rep = data["reputation"]
    
    assert rep["tier"] == "Platinum"
    assert rep["progress_to_next"] == 1.0
    assert rep["next_tier"] is None
    assert rep["points_to_next"] is None

