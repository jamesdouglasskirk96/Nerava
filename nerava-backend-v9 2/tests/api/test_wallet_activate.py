"""
Tests for Wallet Pass Activation API
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main_simple import app
from app.models.wallet_pass import WalletPassActivation, WalletPassStateEnum
from app.models.intent import IntentSession
from app.models.while_you_charge import Merchant
from app.models import User


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user(db):
    """Create a test user"""
    user = User(
        id=1,
        public_id="test-user-123",
        email="test@example.com",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def mock_merchant(db):
    """Create a test merchant"""
    merchant = Merchant(
        id="m_test_1",
        external_id="mock_asadas_grill",
        name="Asadas Grill",
        category="Restaurant",
        lat=30.2680,
        lng=-97.7435,
    )
    db.add(merchant)
    db.commit()
    return merchant


@pytest.fixture
def mock_intent_session(db, mock_user):
    """Create a test intent session"""
    session = IntentSession(
        id="session-123",
        user_id=mock_user.id,
        lat=30.2672,
        lng=-97.7431,
        accuracy_m=50.0,
        confidence_tier="A",
        source="web",
    )
    db.add(session)
    db.commit()
    return session


class TestWalletActivateEndpoint:
    """Test POST /v1/wallet/pass/activate endpoint"""
    
    def test_activate_wallet_pass_creates_new(self, client, mock_intent_session, mock_merchant):
        """Test activating wallet pass creates new record"""
        response = client.post(
            "/v1/wallet/pass/activate",
            json={
                "session_id": str(mock_intent_session.id),
                "merchant_id": mock_merchant.id,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert data["wallet_state"]["state"] == "ACTIVE"
        assert data["wallet_state"]["merchant_id"] == mock_merchant.id
        assert "expires_at" in data["wallet_state"]
        assert "active_copy" in data["wallet_state"]
        
        # Verify expiry is ~60 minutes from now
        expires_at = datetime.fromisoformat(data["wallet_state"]["expires_at"].replace('Z', '+00:00'))
        expected_expiry = datetime.utcnow() + timedelta(minutes=60)
        time_diff = abs((expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    def test_activate_wallet_pass_updates_existing(self, client, db, mock_intent_session, mock_merchant):
        """Test activating wallet pass updates existing record"""
        # Create existing wallet pass
        existing = WalletPassActivation(
            id="wallet-pass-123",
            session_id=str(mock_intent_session.id),
            merchant_id=mock_merchant.id,
            state=WalletPassStateEnum.INACTIVE,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db.add(existing)
        db.commit()
        
        # Activate it
        response = client.post(
            "/v1/wallet/pass/activate",
            json={
                "session_id": str(mock_intent_session.id),
                "merchant_id": mock_merchant.id,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["wallet_state"]["state"] == "ACTIVE"
        
        # Verify it was updated (not duplicated)
        db.refresh(existing)
        assert existing.state == WalletPassStateEnum.ACTIVE
    
    def test_activate_wallet_pass_invalid_session(self, client, mock_merchant):
        """Test 404 when session not found"""
        response = client.post(
            "/v1/wallet/pass/activate",
            json={
                "session_id": "nonexistent-session",
                "merchant_id": mock_merchant.id,
            }
        )
        
        assert response.status_code == 404
        assert "session" in response.json()["detail"].lower()
    
    def test_activate_wallet_pass_invalid_merchant(self, client, mock_intent_session):
        """Test 404 when merchant not found"""
        response = client.post(
            "/v1/wallet/pass/activate",
            json={
                "session_id": str(mock_intent_session.id),
                "merchant_id": "nonexistent-merchant",
            }
        )
        
        assert response.status_code == 404
        assert "merchant" in response.json()["detail"].lower()
    
    def test_activate_wallet_pass_response_schema(self, client, mock_intent_session, mock_merchant):
        """Test that response matches expected schema"""
        response = client.post(
            "/v1/wallet/pass/activate",
            json={
                "session_id": str(mock_intent_session.id),
                "merchant_id": mock_merchant.id,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert "status" in data
        assert "wallet_state" in data
        
        # Check wallet_state fields
        assert "state" in data["wallet_state"]
        assert "merchant_id" in data["wallet_state"]
        assert "expires_at" in data["wallet_state"]
        assert "active_copy" in data["wallet_state"]
        
        # Verify state is ACTIVE
        assert data["wallet_state"]["state"] == "ACTIVE"

