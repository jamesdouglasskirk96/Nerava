"""
Tests for Exclusive Session API endpoints
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.models import User, Charger, Merchant, ExclusiveSession, ExclusiveSessionStatus
from app.main import app
from app.db import get_db


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = User(
        id=1,
        public_id="test-driver-123",
        email="driver@test.com",
        is_active=True,
        role_flags="driver",
        auth_provider="local"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_charger(db):
    """Create a test charger"""
    charger = Charger(
        id="ch_test_1",
        name="Test Charger",
        lat=30.2672,
        lng=-97.7431,
        is_public=True,
        network_name="Test Network",
    )
    db.add(charger)
    db.commit()
    db.refresh(charger)
    return charger


@pytest.fixture
def test_merchant(db):
    """Create a test merchant"""
    merchant = Merchant(
        id="m_test_1",
        name="Test Merchant",
        lat=30.2680,
        lng=-97.7440,
        category="coffee",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant




class TestActivateExclusive:
    """Test POST /v1/exclusive/activate"""
    
    def test_activate_requires_auth(self, client, db, test_charger, test_merchant):
        """Test that activation requires authentication"""
        # Clear dependency overrides to test auth requirement
        from app.dependencies.driver import get_current_driver
        if get_current_driver in app.dependency_overrides:
            del app.dependency_overrides[get_current_driver]
        
        response = client.post(
            "/v1/exclusive/activate",
            json={
                "merchant_id": test_merchant.id,
                "charger_id": test_charger.id,
                "lat": test_charger.lat,
                "lng": test_charger.lng,
            }
        )
        assert response.status_code == 401
    
    def test_activate_outside_radius(self, client, db, test_user, test_charger, test_merchant):
        """Test activation fails when outside charger radius"""
        # Mock get_current_driver to return test_user
        from app.dependencies.driver import get_current_driver
        app.dependency_overrides[get_current_driver] = lambda: test_user
        
        # Location far from charger (500m away)
        far_lat = 30.2720  # ~500m north
        far_lng = -97.7431
        
        response = client.post(
            "/v1/exclusive/activate",
            json={
                "merchant_id": test_merchant.id,
                "charger_id": test_charger.id,
                "lat": far_lat,
                "lng": far_lng,
            }
        )
        
        assert response.status_code == 403
        assert "must be at the charger" in response.json()["detail"].lower()
        
        app.dependency_overrides.clear()
    
    def test_activate_success_creates_active_session(
        self, client, db, test_user, test_charger, test_merchant
    ):
        """Test successful activation creates active session"""
        from app.dependencies.driver import get_current_driver
        app.dependency_overrides[get_current_driver] = lambda: test_user
        
        # Location at charger (within radius)
        response = client.post(
            "/v1/exclusive/activate",
            json={
                "merchant_id": test_merchant.id,
                "charger_id": test_charger.id,
                "lat": test_charger.lat,
                "lng": test_charger.lng,
                "accuracy_m": 10.0,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACTIVE"
        assert "exclusive_session" in data
        assert data["exclusive_session"]["merchant_id"] == test_merchant.id
        assert data["exclusive_session"]["charger_id"] == test_charger.id
        assert "expires_at" in data["exclusive_session"]
        assert "remaining_seconds" in data["exclusive_session"]
        assert data["exclusive_session"]["remaining_seconds"] > 0
        
        # Verify session in DB
        session = db.query(ExclusiveSession).filter(
            ExclusiveSession.driver_id == test_user.id,
            ExclusiveSession.status == ExclusiveSessionStatus.ACTIVE
        ).first()
        assert session is not None
        assert session.merchant_id == test_merchant.id
        assert session.charger_id == test_charger.id
        
        # Verify expires_at is ~60 minutes from now
        expires_at = datetime.fromisoformat(data["exclusive_session"]["expires_at"].replace('Z', '+00:00'))
        now = datetime.utcnow()
        duration_minutes = (expires_at - now).total_seconds() / 60
        assert 59 <= duration_minutes <= 61  # Allow 1 minute tolerance
        
        app.dependency_overrides.clear()
    
    def test_activate_when_active_exists(
        self, client, db, test_user, test_charger, test_merchant
    ):
        """Test activation when active session exists returns existing session"""
        from app.dependencies.driver import get_current_driver
        app.dependency_overrides[get_current_driver] = lambda: test_user
        
        # Create existing active session
        existing_session = ExclusiveSession(
            id="existing-session-123",
            driver_id=test_user.id,
            merchant_id=test_merchant.id,
            charger_id=test_charger.id,
            status=ExclusiveSessionStatus.ACTIVE,
            activated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=60),
        )
        db.add(existing_session)
        db.commit()
        
        # Try to activate again
        response = client.post(
            "/v1/exclusive/activate",
            json={
                "merchant_id": test_merchant.id,
                "charger_id": test_charger.id,
                "lat": test_charger.lat,
                "lng": test_charger.lng,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACTIVE"
        assert data["exclusive_session"]["id"] == "existing-session-123"
        
        # Verify only one active session exists
        active_sessions = db.query(ExclusiveSession).filter(
            ExclusiveSession.driver_id == test_user.id,
            ExclusiveSession.status == ExclusiveSessionStatus.ACTIVE
        ).all()
        assert len(active_sessions) == 1
        
        app.dependency_overrides.clear()


class TestCompleteExclusive:
    """Test POST /v1/exclusive/complete"""
    
    def test_complete_success(
        self, client, db, test_user, test_charger, test_merchant
    ):
        """Test successful completion marks session as COMPLETED"""
        from app.dependencies.driver import get_current_driver
        app.dependency_overrides[get_current_driver] = lambda: test_user
        
        # Create active session
        session = ExclusiveSession(
            id="session-to-complete",
            driver_id=test_user.id,
            merchant_id=test_merchant.id,
            charger_id=test_charger.id,
            status=ExclusiveSessionStatus.ACTIVE,
            activated_at=datetime.utcnow() - timedelta(minutes=30),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db.add(session)
        db.commit()
        
        # Complete session
        response = client.post(
            "/v1/exclusive/complete",
            json={
                "exclusive_session_id": "session-to-complete",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        
        # Verify session is marked as completed
        db.refresh(session)
        assert session.status == ExclusiveSessionStatus.COMPLETED
        assert session.completed_at is not None
        
        app.dependency_overrides.clear()
    
    def test_complete_not_active(
        self, client, db, test_user, test_charger, test_merchant
    ):
        """Test completing a non-active session returns 409"""
        from app.dependencies.driver import get_current_driver
        app.dependency_overrides[get_current_driver] = lambda: test_user
        
        # Create completed session
        session = ExclusiveSession(
            id="already-completed",
            driver_id=test_user.id,
            merchant_id=test_merchant.id,
            charger_id=test_charger.id,
            status=ExclusiveSessionStatus.COMPLETED,
            activated_at=datetime.utcnow() - timedelta(hours=1),
            expires_at=datetime.utcnow() - timedelta(minutes=30),
            completed_at=datetime.utcnow() - timedelta(minutes=30),
        )
        db.add(session)
        db.commit()
        
        # Try to complete again
        response = client.post(
            "/v1/exclusive/complete",
            json={
                "exclusive_session_id": "already-completed",
            }
        )
        
        assert response.status_code == 409
        assert "not active" in response.json()["detail"].lower()
        
        app.dependency_overrides.clear()


class TestGetActiveExclusive:
    """Test GET /v1/exclusive/active"""
    
    def test_active_endpoint_returns_active(
        self, client, db, test_user, test_charger, test_merchant
    ):
        """Test active endpoint returns active session"""
        from app.dependencies.driver import get_current_driver
        app.dependency_overrides[get_current_driver] = lambda: test_user
        
        # Create active session
        session = ExclusiveSession(
            id="active-session",
            driver_id=test_user.id,
            merchant_id=test_merchant.id,
            charger_id=test_charger.id,
            status=ExclusiveSessionStatus.ACTIVE,
            activated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=60),
        )
        db.add(session)
        db.commit()
        
        # Get active session
        response = client.get("/v1/exclusive/active")
        
        assert response.status_code == 200
        data = response.json()
        assert data["exclusive_session"] is not None
        assert data["exclusive_session"]["id"] == "active-session"
        assert data["exclusive_session"]["remaining_seconds"] > 0
        
        app.dependency_overrides.clear()
    
    def test_active_endpoint_returns_null_when_no_active(
        self, client, db, test_user
    ):
        """Test active endpoint returns null when no active session"""
        from app.dependencies.driver import get_current_driver
        app.dependency_overrides[get_current_driver] = lambda: test_user
        
        response = client.get(
            "/v1/exclusive/active",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exclusive_session"] is None
        
        app.dependency_overrides.clear()
    
    def test_active_endpoint_expires_old(
        self, client, db, test_user, test_charger, test_merchant
    ):
        """Test active endpoint marks expired sessions and returns null"""
        from app.dependencies.driver import get_current_driver
        app.dependency_overrides[get_current_driver] = lambda: test_user
        
        # Create expired session (expires_at in the past)
        session = ExclusiveSession(
            id="expired-session",
            driver_id=test_user.id,
            merchant_id=test_merchant.id,
            charger_id=test_charger.id,
            status=ExclusiveSessionStatus.ACTIVE,
            activated_at=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(minutes=30),  # Expired 30 min ago
        )
        db.add(session)
        db.commit()
        
        # Get active session (should mark as expired and return null)
        response = client.get("/v1/exclusive/active")
        
        assert response.status_code == 200
        data = response.json()
        assert data["exclusive_session"] is None
        
        # Verify session was marked as expired
        db.refresh(session)
        assert session.status == ExclusiveSessionStatus.EXPIRED
        
        app.dependency_overrides.clear()

