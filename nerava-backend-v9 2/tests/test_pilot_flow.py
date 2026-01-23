"""
Tests for Domain Pilot Driver Flow

End-to-end tests for the pilot API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from app.main_simple import app
from app.services.nova import cents_to_nova
from app.db import get_db, SessionLocal, Base, get_engine

# Import all models to ensure they're registered with Base
from app import models, models_extra, models_while_you_charge, models_demo

client = TestClient(app)


@pytest.fixture
def db():
    """Create a test database session."""
    # Import all models to ensure they're registered with Base
    from app import models, models_extra, models_while_you_charge, models_demo
    
    # Ensure tables exist (they should be created by conftest, but make sure)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user_id():
    """Generate a test user ID"""
    return 123


@pytest.fixture
def seeded_domain_chargers(db: Session):
    """Seed Domain hub chargers for testing"""
    from app.domains.domain_hub import DOMAIN_CHARGERS
    from app.models_while_you_charge import Charger
    
    chargers = []
    for charger_config in DOMAIN_CHARGERS:
        # Check if charger already exists
        existing = db.query(Charger).filter(Charger.id == charger_config["id"]).first()
        if existing:
            chargers.append(existing)
            continue
            
        charger = Charger(
            id=charger_config["id"],
            name=charger_config["name"],
            network_name=charger_config["network_name"],
            lat=charger_config["lat"],
            lng=charger_config["lng"],
            address=charger_config.get("address"),
            city=charger_config.get("city", "Austin"),
            state=charger_config.get("state", "TX"),
            zip_code=charger_config.get("zip_code"),
            connector_types=charger_config.get("connector_types", []),
            power_kw=charger_config.get("power_kw", 50.0),
            is_public=True,
            status="available"
        )
        db.add(charger)
        chargers.append(charger)
    
    db.commit()
    return chargers


@pytest.fixture
def seeded_merchant(db: Session):
    """Seed a test merchant"""
    from app.models_while_you_charge import Merchant
    
    # Check if merchant already exists
    existing = db.query(Merchant).filter(Merchant.id == "m_test_001").first()
    if existing:
        return existing
    
    merchant = Merchant(
        id="m_test_001",
        name="Test Coffee Shop",
        category="coffee",
        lat=30.4021,
        lng=-97.7266,
        address="11601 Domain Dr, Austin, TX 78758"
    )
    db.add(merchant)
    db.commit()
    return merchant


# ============================================
# Test 1: Start session
# ============================================
def test_start_session(db: Session, test_user_id, seeded_domain_chargers):
    """Test that start_session creates a session with hub_id='domain'"""
    
    response = client.post(
        "/v1/pilot/start_session",
        params={"user_id": test_user_id},
        json={
            "user_lat": 30.4021,
            "user_lng": -97.7266
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "session_id" in data
    assert data["hub_id"] == "domain"
    assert data["hub_name"] == "Domain – Austin"
    assert "charger" in data
    assert data["charger"]["id"] in [ch.id for ch in seeded_domain_chargers]
    assert data["status"] in ["started", "active"]
    
    # Verify session exists in DB
    session_row = db.execute(text("""
        SELECT id, user_id, status FROM sessions WHERE id = :session_id
    """), {"session_id": data["session_id"]}).first()
    
    assert session_row is not None
    assert session_row[0] == data["session_id"]
    assert session_row[1] == test_user_id


# ============================================
# Test 2: Verify ping
# ============================================
def test_verify_ping(db: Session, test_user_id, seeded_domain_chargers):
    """Test that verify_ping verifies session and awards Nova"""
    
    # First create a session
    start_response = client.post(
        "/v1/pilot/start_session",
        params={"user_id": test_user_id},
        json={
            "user_lat": 30.4021,
            "user_lng": -97.7266
        }
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["session_id"]
    
    # Create chargers_openmap table if it doesn't exist, then populate it
    # verify_dwell expects this table for charger lookups
    charger = seeded_domain_chargers[0]
    
    # Check if table exists, create if not
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                name TEXT,
                lat REAL,
                lng REAL
            )
        """))
        db.commit()
    except Exception:
        pass
    
    # Insert charger into chargers_openmap
    try:
        db.execute(text("""
            INSERT OR REPLACE INTO chargers_openmap (id, name, lat, lng)
            VALUES (:id, :name, :lat, :lng)
        """), {
            "id": charger.id,
            "name": charger.name,
            "lat": charger.lat,
            "lng": charger.lng
        })
        db.commit()
    except Exception as e:
        db.rollback()
        # Table might already have the charger, continue
    
    # Create session in sessions table with proper structure
    # The verify_dwell service expects specific columns
    db.execute(text("""
        INSERT OR REPLACE INTO sessions (
            id, user_id, status, started_at, 
            started_lat, started_lng, last_lat, last_lng,
            target_type, target_id, target_name, radius_m,
            min_accuracy_m, dwell_required_s, ping_count, dwell_seconds
        ) VALUES (
            :id, :user_id, 'active', :started_at,
            :lat, :lng, :lat, :lng,
            'charger', :charger_id, :charger_name, 100,
            100, 30, 0, 0
        )
    """), {
        "id": session_id,
        "user_id": test_user_id,
        "started_at": datetime.utcnow(),
        "lat": 30.4021,
        "lng": -97.7266,
        "charger_id": charger.id,
        "charger_name": charger.name
    })
    db.commit()
    
    # Simulate multiple pings (need at least 30 seconds of dwell)
    # For testing, we'll directly set dwell_seconds to meet threshold
    db.execute(text("""
        UPDATE sessions
        SET dwell_seconds = 30,
            last_lat = :lat,
            last_lng = :lng,
            last_accuracy_m = 10
        WHERE id = :session_id
    """), {
        "session_id": session_id,
        "lat": 30.4021,
        "lng": -97.7266
    })
    db.commit()
    
    # Make verify ping (should verify and reward)
    ping_response = client.post(
        "/v1/pilot/verify_ping",
        json={
            "session_id": session_id,
            "user_lat": 30.4021,
            "user_lng": -97.7266
        }
    )
    
    assert ping_response.status_code == 200
    data = ping_response.json()
    
    assert "verified" in data
    assert "wallet_balance" in data
    assert "wallet_balance_nova" in data
    
    # If verified, should have Nova awarded
    if data["verified"]:
        assert "nova_awarded" in data
        # Wallet balance should be updated
        assert data["wallet_balance_nova"] == cents_to_nova(data["wallet_balance"])


# ============================================
# Test 3: While-you-charge
# ============================================
def test_while_you_charge(db: Session, seeded_domain_chargers, seeded_merchant):
    """Test that while_you_charge returns chargers and merchants"""
    
    response = client.get("/v1/pilot/while_you_charge")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "hub_id" in data
    assert data["hub_id"] == "domain"
    assert "hub_name" in data
    assert "chargers" in data
    assert len(data["chargers"]) > 0
    
    # Verify charger structure
    charger = data["chargers"][0]
    assert "id" in charger
    assert "name" in charger
    assert "lat" in charger
    assert "lng" in charger
    
    # Merchants may or may not be present (depends on seeding)
    assert "merchants" in data


# ============================================
# Test 4: Verify visit
# ============================================
def test_verify_visit(db: Session, test_user_id, seeded_merchant):
    """Test that verify_visit verifies merchant visit and awards Nova"""
    
    # Create a session first
    session_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO sessions (
            id, user_id, status, started_at, started_lat, started_lng
        ) VALUES (
            :id, :user_id, 'active', :started_at, :lat, :lng
        )
    """), {
        "id": session_id,
        "user_id": test_user_id,
        "started_at": datetime.utcnow(),
        "lat": 30.4021,
        "lng": -97.7266
    })
    db.commit()
    
    # Verify visit at merchant location
    response = client.post(
        "/v1/pilot/verify_visit",
        json={
            "session_id": session_id,
            "merchant_id": seeded_merchant.id,
            "user_lat": 30.4021,  # Same as merchant
            "user_lng": -97.7266
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "verified" in data
    assert data["verified"] is True
    assert "nova_awarded" in data
    assert data["nova_awarded"] == 25  # Merchant visit reward
    assert "wallet_balance" in data
    assert "wallet_balance_nova" in data
    
    # Verify reward was recorded
    reward = db.execute(text("""
        SELECT id FROM reward_events
        WHERE user_id = :user_id
        AND source = 'merchant_visit'
        LIMIT 1
    """), {"user_id": str(test_user_id)}).first()
    
    assert reward is not None
    
    # Test idempotency - second visit should not award again
    response2 = client.post(
        "/v1/pilot/verify_visit",
        json={
            "session_id": session_id,
            "merchant_id": seeded_merchant.id,
            "user_lat": 30.4021,
            "user_lng": -97.7266
        }
    )
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["verified"] is True
    assert data2["nova_awarded"] == 0  # Already rewarded
    assert data2["reason"] == "already_rewarded"


# ============================================
# Test 5: Activity feed
# ============================================
def test_activity_feed(db: Session, test_user_id):
    """Test that activity feed returns wallet entries and rewards"""
    
    # Create some wallet activity
    from app.models_extra import CreditLedger
    
    ledger1 = CreditLedger(
        user_ref=str(test_user_id),
        cents=100,
        reason="TEST_CREDIT",
        meta={}
    )
    ledger2 = CreditLedger(
        user_ref=str(test_user_id),
        cents=-50,
        reason="TEST_DEBIT",
        meta={}
    )
    db.add(ledger1)
    db.add(ledger2)
    
    # Create a reward event
    from app.models_extra import RewardEvent
    reward = RewardEvent(
        user_id=str(test_user_id),
        source="test_reward",
        gross_cents=200,
        net_cents=180,
        community_cents=20,
        meta={}
    )
    db.add(reward)
    db.commit()
    
    # Get activity feed
    response = client.get(
        "/v1/pilot/activity",
        params={"user_id": str(test_user_id), "limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "activities" in data
    assert "count" in data
    assert len(data["activities"]) > 0
    
    # Check that we have wallet entries
    wallet_activities = [a for a in data["activities"] if a["type"] == "wallet"]
    assert len(wallet_activities) >= 2
    
    # Check Nova delta is present
    for activity in wallet_activities:
        assert "nova_delta" in activity
        assert activity["nova_delta"] == cents_to_nova(activity["cents"])
    
    # Check reward events have Nova
    reward_activities = [a for a in data["activities"] if a["type"] == "reward"]
    if reward_activities:
        assert "nova_awarded" in reward_activities[0]
        assert reward_activities[0]["nova_awarded"] == cents_to_nova(reward_activities[0]["gross_cents"])
