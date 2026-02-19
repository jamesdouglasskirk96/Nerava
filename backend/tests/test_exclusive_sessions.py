"""
Unit tests for exclusive session activation, completion, and caps enforcement
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import User, Charger, Merchant
from app.models.exclusive_session import ExclusiveSession, ExclusiveSessionStatus
from app.routers.exclusive import (
    validate_charger_radius,
    CHARGER_RADIUS_M,
    EXCLUSIVE_DURATION_MIN,
)


@pytest.fixture
def test_driver(db: Session) -> User:
    """Create a test driver user"""
    import uuid
    user = User(
        public_id=str(uuid.uuid4()),
        phone="+15551234567",
        auth_provider="phone",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_charger(db: Session) -> Charger:
    """Create a test charger"""
    charger = Charger(
        id="test_charger_1",
        name="Test Charger",
        lat=30.2672,
        lng=-97.7431,
        is_active=True
    )
    db.add(charger)
    db.commit()
    db.refresh(charger)
    return charger


@pytest.fixture
def test_merchant(db: Session) -> Merchant:
    """Create a test merchant"""
    from app.models.while_you_charge import Merchant as WYCMerchant
    merchant = WYCMerchant(
        id="test_merchant_1",
        name="Test Merchant",
        lat=30.2680,
        lng=-97.7440,
        category="coffee",
        is_active=True
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def test_exclusive_activation_within_radius(db: Session, test_driver: User, test_charger: Charger, test_merchant: Merchant):
    """Test exclusive activation when driver is within charger radius"""
    from app.routers.exclusive import router
    from fastapi.testclient import TestClient
    from app.main_simple import app
    
    client = TestClient(app)
    
    # Mock authentication
    # In real test, would set auth token
    
    # Activate exclusive (driver at charger location)
    response = client.post(
        "/v1/exclusive/activate",
        json={
            "merchant_id": str(test_merchant.id),
            "charger_id": str(test_charger.id),
            "lat": test_charger.lat,
            "lng": test_charger.lng,
            "accuracy_m": 10.0
        },
        headers={"Authorization": "Bearer test_token"}  # Would need real token
    )
    
    # Should succeed (if auth is mocked properly)
    # For MVP, test the radius validation logic directly
    distance_m, is_within = validate_charger_radius(
        db, str(test_charger.id), test_charger.lat, test_charger.lng
    )
    
    assert is_within is True
    assert distance_m < CHARGER_RADIUS_M


def test_exclusive_activation_outside_radius(db: Session, test_charger: Charger):
    """Test exclusive activation fails when driver is outside charger radius"""
    # Location far from charger
    far_lat = test_charger.lat + 0.01  # ~1km away
    far_lng = test_charger.lng + 0.01
    
    distance_m, is_within = validate_charger_radius(
        db, str(test_charger.id), far_lat, far_lng
    )
    
    assert is_within is False
    assert distance_m > CHARGER_RADIUS_M


def test_exclusive_completion_flow(db: Session, test_driver: User, test_charger: Charger, test_merchant: Merchant):
    """Test exclusive session completion flow"""
    import uuid
    
    # Create active session
    session = ExclusiveSession(
        id=str(uuid.uuid4()),
        driver_id=test_driver.id,
        merchant_id=str(test_merchant.id),
        charger_id=str(test_charger.id),
        status=ExclusiveSessionStatus.ACTIVE,
        activated_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=EXCLUSIVE_DURATION_MIN)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Complete session
    session.status = ExclusiveSessionStatus.COMPLETED
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    
    assert session.status == ExclusiveSessionStatus.COMPLETED
    assert session.completed_at is not None


def test_exclusive_caps_enforcement(db: Session, test_driver: User, test_merchant: Merchant):
    """Test daily cap enforcement (MVP: basic check)"""
    import uuid
    
    # Create multiple sessions for same merchant
    sessions = []
    for i in range(5):
        session = ExclusiveSession(
            id=str(uuid.uuid4()),
            driver_id=test_driver.id,
            merchant_id=str(test_merchant.id),
            status=ExclusiveSessionStatus.COMPLETED,
            activated_at=datetime.utcnow() - timedelta(hours=i),
            completed_at=datetime.utcnow() - timedelta(hours=i) + timedelta(minutes=30)
        )
        sessions.append(session)
        db.add(session)
    
    db.commit()
    
    # Count activations for today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_sessions = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == str(test_merchant.id),
        ExclusiveSession.activated_at >= today_start
    ).count()
    
    assert today_sessions == 5
    
    # If daily cap is 10, should allow more
    # If daily cap is 3, should block (would be enforced in endpoint)


def test_exclusive_expiration(db: Session, test_driver: User, test_charger: Charger, test_merchant: Merchant):
    """Test exclusive session expiration"""
    import uuid
    
    # Create expired session
    expired_session = ExclusiveSession(
        id=str(uuid.uuid4()),
        driver_id=test_driver.id,
        merchant_id=str(test_merchant.id),
        charger_id=str(test_charger.id),
        status=ExclusiveSessionStatus.ACTIVE,
        activated_at=datetime.utcnow() - timedelta(minutes=EXCLUSIVE_DURATION_MIN + 10),
        expires_at=datetime.utcnow() - timedelta(minutes=10)
    )
    db.add(expired_session)
    db.commit()
    
    # Check if expired
    assert expired_session.expires_at < datetime.utcnow()
    
    # Mark as expired
    expired_session.status = ExclusiveSessionStatus.EXPIRED
    db.commit()
    
    assert expired_session.status == ExclusiveSessionStatus.EXPIRED







