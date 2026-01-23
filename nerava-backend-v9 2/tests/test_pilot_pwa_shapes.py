"""
Tests for PWA Response Shapes

Ensures all pilot endpoints return clean, consistent, PWA-friendly JSON shapes.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import uuid

from app.main_simple import app as app_instance
from app.db import get_db, SessionLocal, Base, get_engine
from app.models_while_you_charge import Charger, Merchant
from app.models_extra import CreditLedger, RewardEvent

# Import all models to ensure they're registered with Base
from app import models, models_extra, models_while_you_charge, models_demo

client = TestClient(app_instance)


@pytest.fixture
def db():
    """Create a test database session."""
    from app import models, models_extra, models_while_you_charge, models_demo
    
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
def seeded_domain_charger(db: Session):
    """Seed a Domain charger for testing"""
    from app.domains.domain_hub import DOMAIN_CHARGERS
    
    charger_config = DOMAIN_CHARGERS[0]
    charger = Charger(
        id=charger_config["id"],
        name=charger_config["name"],
        network_name=charger_config["network_name"],
        lat=charger_config["lat"],
        lng=charger_config["lng"],
        address=charger_config.get("address"),
        city="Austin",
        state="TX",
        is_public=True,
        status="available"
    )
    db.add(charger)
    
    # Also add to chargers_openmap for verify_dwell
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS chargers_openmap (
            id TEXT PRIMARY KEY,
            name TEXT,
            lat REAL,
            lng REAL
        )
    """))
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
    return charger


@pytest.fixture
def seeded_merchant(db: Session):
    """Seed a test merchant"""
    merchant = Merchant(
        id="m_test_001",
        name="Test Merchant",
        category="coffee",
        lat=30.4021,
        lng=-97.7266,
        address="Test Address"
    )
    db.add(merchant)
    db.commit()
    return merchant


# ============================================
# Test 1: /v1/pilot/start_session shape
# ============================================
def test_start_session_shape(db: Session, test_user_id, seeded_domain_charger):
    """Test that start_session returns clean PWA shape."""
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        response = client.post(
            "/v1/pilot/start_session",
            params={"user_id": test_user_id},
            json={"user_lat": 30.4021, "user_lng": -97.7266}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "session_id" in data
        assert "hub_id" in data
        assert "hub_name" in data
        assert "charger" in data
        assert "status" in data
        assert "dwell_required_s" in data
        assert "min_accuracy_m" in data
        
        # Charger shape
        charger = data["charger"]
        assert "id" in charger
        assert "name" in charger
        assert "lat" in charger
        assert "lng" in charger
        assert "distance_m" in charger
        
        # All numbers should be integers
        assert isinstance(data["dwell_required_s"], int)
        assert isinstance(data["min_accuracy_m"], int)
        assert isinstance(charger["distance_m"], int)
        
        # No internal fields
        assert "created_at" not in data
        assert "user_id" not in data
    finally:
        app_instance.dependency_overrides.clear()


# ============================================
# Test 2: /v1/pilot/verify_ping shape
# ============================================
def test_verify_ping_shape(db: Session, test_user_id, seeded_domain_charger):
    """Test that verify_ping returns reward_earned flag and clean shape."""
    from app.db import get_db
    from app.services.verify_dwell import start_session as verify_start_session
    
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        # Create session first
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
        # Ensure session exists
        db.execute(text("""
            INSERT OR IGNORE INTO sessions (id, user_id, status, started_at)
            VALUES (:id, :user_id, 'pending', :started_at)
        """), {
            "id": session_id,
            "user_id": test_user_id,
            "started_at": datetime.utcnow()
        })
        db.commit()
        
        verify_start_session(
            db=db,
            session_id=session_id,
            user_id=test_user_id,
            lat=30.4021,
            lng=-97.7266,
            accuracy_m=10.0,
            ua="test",
            event_id=None
        )
        
        # Call verify_ping
        response = client.post(
            "/v1/pilot/verify_ping",
            json={
                "session_id": session_id,
                "user_lat": 30.4021,
                "user_lng": -97.7266
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "verified" in data
        assert "reward_earned" in data  # PWA flag
        assert isinstance(data["reward_earned"], bool)
        assert "verification_score" in data
        assert "wallet_balance_nova" in data
        
        # All numbers should be integers
        assert isinstance(data["verification_score"], int)
        assert isinstance(data["wallet_balance_nova"], int)
        
        # If reward_earned is True, nova_awarded should be present
        if data["reward_earned"]:
            assert "nova_awarded" in data
            assert isinstance(data["nova_awarded"], int)
    finally:
        app_instance.dependency_overrides.clear()


# ============================================
# Test 3: /v1/pilot/while_you_charge shape
# ============================================
def test_while_you_charge_shape(db: Session, seeded_domain_charger, seeded_merchant):
    """Test that while_you_charge returns consistent object shapes."""
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        response = client.get("/v1/pilot/while_you_charge")
        
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "hub_id" in data
        assert "hub_name" in data
        assert "chargers" in data
        assert "recommended_merchants" in data  # Renamed from "merchants"
        
        # Check charger shapes
        for charger in data["chargers"]:
            assert "id" in charger
            assert "name" in charger
            assert "lat" in charger
            assert "lng" in charger
            # No nulls (optional fields may be absent, but required fields present)
            assert charger["id"] is not None
            assert charger["name"] is not None
        
        # Check merchant shapes
        for merchant in data["recommended_merchants"]:
            assert "id" in merchant
            assert "name" in merchant
            assert "lat" in merchant
            assert "lng" in merchant
    finally:
        app_instance.dependency_overrides.clear()


# ============================================
# Test 4: /v1/pilot/app/bootstrap
# ============================================
def test_bootstrap_shape(db: Session, seeded_domain_charger):
    """Test that bootstrap endpoint returns pilot_mode flag and required fields."""
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        response = client.get("/v1/pilot/app/bootstrap")
        
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "pilot_mode" in data
        assert isinstance(data["pilot_mode"], bool)
        assert "hub_id" in data
        assert "hub_name" in data
        assert "chargers" in data
        assert "merchant_count" in data
        assert "nova_balance" in data
        
        # All numbers should be integers
        assert isinstance(data["merchant_count"], int)
        assert isinstance(data["nova_balance"], int)
        
        # Chargers should be shaped correctly
        for charger in data["chargers"]:
            assert "id" in charger
            assert "name" in charger
    finally:
        app_instance.dependency_overrides.clear()


# ============================================
# Test 5: Error shape test
# ============================================
def test_error_shape_normalized(db: Session):
    """Test that 404 errors return normalized error response."""
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        # Trigger a 404 by requesting nonexistent merchant
        response = client.post(
            "/v1/pilot/verify_visit",
            json={
                "session_id": "nonexistent",
                "merchant_id": "nonexistent",
                "user_lat": 30.4021,
                "user_lng": -97.7266
            }
        )
        
        # Should return 404 with normalized error shape
        assert response.status_code == 404
        data = response.json()
        
        assert "error" in data
        assert "type" in data["error"]
        assert "message" in data["error"]
        assert data["error"]["type"] == "NotFound"
    finally:
        app_instance.dependency_overrides.clear()


# ============================================
# Test 6: verify_visit reward_earned flag
# ============================================
def test_verify_visit_reward_earned_flag(db: Session, test_user_id, seeded_merchant):
    """Test that verify_visit returns reward_earned flag."""
    from app.db import get_db
    
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        # Create a session first
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        db.execute(text("""
            INSERT INTO sessions (id, user_id, status, started_at)
            VALUES (:id, :user_id, 'active', :started_at)
        """), {
            "id": session_id,
            "user_id": test_user_id,
            "started_at": datetime.utcnow()
        })
        db.commit()
        
        # Call verify_visit
        response = client.post(
            "/v1/pilot/verify_visit",
            json={
                "session_id": session_id,
                "merchant_id": seeded_merchant.id,
                "user_lat": 30.4021,
                "user_lng": -97.7266
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Must have reward_earned flag
        assert "reward_earned" in data
        assert isinstance(data["reward_earned"], bool)
        
        # All numbers should be integers
        assert isinstance(data["nova_awarded"], int)
        assert isinstance(data["wallet_balance_nova"], int)
        
        # If verified, should have reward flag
        if data["verified"]:
            # reward_earned should be True for new rewards
            assert data.get("reward_earned") is not False or data.get("reason") == "already_rewarded"
    finally:
        app_instance.dependency_overrides.clear()

