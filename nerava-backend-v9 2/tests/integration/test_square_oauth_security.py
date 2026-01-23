"""
Integration tests for Square OAuth security (state validation)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main_simple import app
from app.services.square_service import create_oauth_state, validate_oauth_state, OAuthStateInvalidError
from app.db import get_db
from unittest.mock import patch, AsyncMock


client = TestClient(app)


@pytest.fixture
def db_session():
    """Get database session"""
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_create_oauth_state(db_session: Session):
    """Test that OAuth state is created and persisted"""
    state = create_oauth_state(db_session)
    
    assert state is not None
    assert len(state) > 20  # Should be a long random string
    
    # Verify state exists in DB
    from app.models.domain import SquareOAuthState
    oauth_state = db_session.query(SquareOAuthState).filter(
        SquareOAuthState.state == state
    ).first()
    
    assert oauth_state is not None
    assert oauth_state.used is False
    assert oauth_state.expires_at is not None


def test_validate_oauth_state_success(db_session: Session):
    """Test that valid OAuth state can be validated"""
    state = create_oauth_state(db_session)
    
    # Should not raise
    validate_oauth_state(db_session, state)
    
    # Verify state is marked as used
    from app.models.domain import SquareOAuthState
    oauth_state = db_session.query(SquareOAuthState).filter(
        SquareOAuthState.state == state
    ).first()
    
    assert oauth_state.used is True


def test_validate_oauth_state_not_found(db_session: Session):
    """Test that validating non-existent state raises error"""
    with pytest.raises(OAuthStateInvalidError, match="not found"):
        validate_oauth_state(db_session, "nonexistent_state_12345")


def test_validate_oauth_state_already_used(db_session: Session):
    """Test that validating already-used state raises error"""
    state = create_oauth_state(db_session)
    
    # Use it once
    validate_oauth_state(db_session, state)
    
    # Try to use again - should fail
    with pytest.raises(OAuthStateInvalidError, match="already been used"):
        validate_oauth_state(db_session, state)


@patch('app.services.square_service.exchange_square_oauth_code')
@patch('app.services.square_service.get_square_oauth_authorize_url')
def test_square_connect_creates_state(mock_get_url, mock_exchange, db_session: Session):
    """Test that /v1/merchants/square/connect creates and returns state"""
    mock_get_url.return_value = AsyncMock(return_value="https://squareupsandbox.com/oauth2/authorize?state=test")
    
    # Mock the async function
    async def mock_url(state):
        return f"https://squareupsandbox.com/oauth2/authorize?state={state}"
    
    mock_get_url.return_value = mock_url
    
    response = client.get("/v1/merchants/square/connect")
    
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "state" in data
    assert len(data["state"]) > 20
    
    # Verify state exists in DB
    from app.models.domain import SquareOAuthState
    oauth_state = db_session.query(SquareOAuthState).filter(
        SquareOAuthState.state == data["state"]
    ).first()
    
    assert oauth_state is not None
    assert oauth_state.used is False


@patch('app.services.square_service.exchange_square_oauth_code')
@patch('app.services.square_service.onboard_merchant_via_square')
def test_square_callback_validates_state(mock_onboard, mock_exchange, db_session: Session):
    """Test that /v1/merchants/square/callback validates state before processing"""
    # Create a valid state
    state = create_oauth_state(db_session)
    
    # Mock OAuth exchange and onboarding
    from app.services.square_service import SquareOAuthResult
    mock_exchange.return_value = AsyncMock(return_value=SquareOAuthResult(
        merchant_id="test_merchant",
        location_id="test_location",
        access_token="test_token"
    ))
    
    async def mock_exchange_func(code):
        return SquareOAuthResult(
            merchant_id="test_merchant",
            location_id="test_location",
            access_token="test_token"
        )
    
    mock_exchange.return_value = mock_exchange_func
    
    from app.services.merchant_onboarding import onboard_merchant_via_square
    from app.models.domain import DomainMerchant
    
    async def mock_onboard_func(db, user_id, square_result):
        merchant = DomainMerchant(
            id="test_merchant_id",
            name="Test Merchant",
            status="active",
            zone_slug="national",
            nova_balance=0,
            lat=0.0,
            lng=0.0
        )
        db.add(merchant)
        db.commit()
        return merchant
    
    mock_onboard.return_value = mock_onboard_func
    
    # Call callback with valid state
    response = client.get(f"/v1/merchants/square/callback?code=test_code&state={state}")
    
    # Should process (may fail on onboarding, but state validation should pass)
    # If state validation fails, we'd get 400 with OAUTH_STATE_MISMATCH
    if response.status_code == 400:
        error_data = response.json()
        # Should not be state mismatch if state is valid
        assert error_data.get("error") != "OAUTH_STATE_MISMATCH"


@patch('app.services.square_service.exchange_square_oauth_code')
def test_square_callback_invalid_state(mock_exchange, db_session: Session):
    """Test that /v1/merchants/square/callback rejects invalid state"""
    # Don't create a state - use a fake one
    fake_state = "fake_state_12345"
    
    response = client.get(f"/v1/merchants/square/callback?code=test_code&state={fake_state}")
    
    assert response.status_code == 400
    error_data = response.json()
    assert error_data["error"] == "OAUTH_STATE_MISMATCH"
    assert "invalid or expired" in error_data["message"].lower()

