"""
Tests for Perk Unlock API
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app.models import PerkUnlock, MerchantPerk, Merchant, WalletPassState, User
from app.services.perk_service import unlock_perk
from app.services.wallet_pass_state import (
    get_or_create_wallet_pass_state,
    transition_to_charging_moment,
    transition_to_perk_unlocked,
    reset_to_idle,
)


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
        name="Test Merchant",
        lat=37.7749,
        lng=-122.4194,
    )
    db.add(merchant)
    db.commit()
    return merchant


@pytest.fixture
def mock_perk(db, mock_merchant):
    """Create a test perk"""
    perk = MerchantPerk(
        id=1,
        merchant_id=mock_merchant.id,
        title="Test Perk",
        description="Test description",
        nova_reward=100,
        is_active=True,
    )
    db.add(perk)
    db.commit()
    return perk


class TestPerkService:
    """Test PerkService functions"""
    
    def test_unlock_perk_dwell_time(self, db, mock_user, mock_perk):
        """Test unlocking perk via dwell time"""
        unlock = unlock_perk(
            db=db,
            user_id=mock_user.id,
            perk_id=mock_perk.id,
            unlock_method="dwell_time",
            dwell_time_seconds=300,
        )
        
        assert unlock.user_id == mock_user.id
        assert unlock.perk_id == mock_perk.id
        assert unlock.unlock_method == "dwell_time"
        assert unlock.dwell_time_seconds == 300
        
        # Verify wallet pass state updated
        state = get_or_create_wallet_pass_state(db, mock_user.id)
        assert state.state == "PERK_UNLOCKED"
        assert state.perk_id == mock_perk.id
    
    def test_unlock_perk_user_confirmation(self, db, mock_user, mock_perk):
        """Test unlocking perk via user confirmation"""
        unlock = unlock_perk(
            db=db,
            user_id=mock_user.id,
            perk_id=mock_perk.id,
            unlock_method="user_confirmation",
        )
        
        assert unlock.unlock_method == "user_confirmation"
    
    def test_unlock_perk_idempotency(self, db, mock_user, mock_perk):
        """Test that unlocking same perk twice is idempotent"""
        unlock1 = unlock_perk(
            db=db,
            user_id=mock_user.id,
            perk_id=mock_perk.id,
            unlock_method="user_confirmation",
        )
        
        unlock2 = unlock_perk(
            db=db,
            user_id=mock_user.id,
            perk_id=mock_perk.id,
            unlock_method="user_confirmation",
        )
        
        assert unlock1.id == unlock2.id  # Same unlock record


class TestWalletPassState:
    """Test WalletPassState service"""
    
    def test_get_or_create_wallet_pass_state(self, db, mock_user):
        """Test getting or creating wallet pass state"""
        state = get_or_create_wallet_pass_state(db, mock_user.id)
        assert state.user_id == mock_user.id
        assert state.state == "IDLE"
        
        # Second call should return same state
        state2 = get_or_create_wallet_pass_state(db, mock_user.id)
        assert state.id == state2.id
    
    def test_transition_to_charging_moment(self, db, mock_user):
        """Test transitioning to CHARGING_MOMENT"""
        state = transition_to_charging_moment(
            db=db,
            user_id=mock_user.id,
            intent_session_id="session-123",
        )
        
        assert state.state == "CHARGING_MOMENT"
        assert state.intent_session_id == "session-123"
    
    def test_transition_to_perk_unlocked(self, db, mock_user, mock_perk):
        """Test transitioning to PERK_UNLOCKED"""
        # First transition to charging moment
        transition_to_charging_moment(db, mock_user.id, "session-123")
        
        # Then unlock perk
        state = transition_to_perk_unlocked(
            db=db,
            user_id=mock_user.id,
            perk_id=mock_perk.id,
        )
        
        assert state.state == "PERK_UNLOCKED"
        assert state.perk_id == mock_perk.id
    
    def test_reset_to_idle(self, db, mock_user):
        """Test resetting to IDLE"""
        # Set to charging moment first
        transition_to_charging_moment(db, mock_user.id, "session-123")
        
        # Reset to idle
        state = reset_to_idle(db, mock_user.id)
        
        assert state.state == "IDLE"
        assert state.intent_session_id is None


class TestPerkUnlockEndpoint:
    """Test perk unlock endpoint"""
    
    @patch('app.services.perk_service.unlock_perk')
    @patch('app.routers.perks.get_current_user')
    def test_unlock_perk_endpoint(self, mock_get_user, mock_unlock, client, mock_user, mock_perk):
        """Test POST /v1/perks/unlock"""
        mock_get_user.return_value = mock_user
        
        unlock = PerkUnlock(
            id="unlock-123",
            user_id=mock_user.id,
            perk_id=mock_perk.id,
            unlock_method="user_confirmation",
            unlocked_at=datetime.utcnow(),
        )
        mock_unlock.return_value = unlock
        
        response = client.post(
            "/v1/perks/unlock",
            json={
                "perk_id": mock_perk.id,
                "unlock_method": "user_confirmation",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["perk_id"] == mock_perk.id
        assert "unlocked_at" in data
    
    @patch('app.routers.perks.get_current_user')
    def test_unlock_perk_invalid_method(self, mock_get_user, client, mock_user):
        """Test unlocking with invalid method"""
        mock_get_user.return_value = mock_user
        
        response = client.post(
            "/v1/perks/unlock",
            json={
                "perk_id": 1,
                "unlock_method": "invalid_method",
            },
        )
        
        assert response.status_code == 400

