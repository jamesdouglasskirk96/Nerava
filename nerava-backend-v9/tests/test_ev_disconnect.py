"""
Test EV disconnect endpoint
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main_simple import app
from app.models import User
from app.models.vehicle import VehicleAccount, VehicleToken
from app.services.refresh_token_service import RefreshTokenService

client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        auth_provider="local",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user, db: Session):
    """Create auth token for test user"""
    _, refresh_token = RefreshTokenService.create_refresh_token(db, test_user)
    db.commit()
    
    from app.core.security import create_access_token
    access_token = create_access_token(test_user.public_id, auth_provider=test_user.auth_provider)
    return access_token


@pytest.fixture
def vehicle_account(test_user, db: Session):
    """Create a vehicle account for test user"""
    account = VehicleAccount(
        id="test-account-id",
        user_id=test_user.id,
        provider="smartcar",
        provider_vehicle_id="test-vehicle-id",
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def test_disconnect_vehicle_deactivates_account(auth_token, test_user, vehicle_account, db: Session):
    """Test POST /v1/ev/disconnect deactivates vehicle account"""
    assert vehicle_account.is_active is True
    
    response = client.post(
        "/v1/ev/disconnect",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    
    # Verify account is deactivated
    db.refresh(vehicle_account)
    assert vehicle_account.is_active is False


def test_disconnect_vehicle_no_account(auth_token, test_user):
    """Test POST /v1/ev/disconnect returns success even if no account exists"""
    response = client.post(
        "/v1/ev/disconnect",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

