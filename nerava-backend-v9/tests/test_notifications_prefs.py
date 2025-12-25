"""
Test notification preferences endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main_simple import app
from app.models import User
from app.models.notification_prefs import UserNotificationPrefs
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


def test_get_notification_prefs_returns_defaults(auth_token, test_user):
    """Test GET /v1/notifications/prefs returns defaults if not set"""
    response = client.get(
        "/v1/notifications/prefs",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["earned_nova"] is True
    assert data["nearby_nova"] is True
    assert data["wallet_reminders"] is True


def test_update_notification_prefs(auth_token, test_user, db: Session):
    """Test PUT /v1/notifications/prefs updates preferences"""
    response = client.put(
        "/v1/notifications/prefs",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "earned_nova": False,
            "nearby_nova": True,
            "wallet_reminders": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["earned_nova"] is False
    assert data["nearby_nova"] is True
    assert data["wallet_reminders"] is False
    
    # Verify in database
    prefs = db.query(UserNotificationPrefs).filter(
        UserNotificationPrefs.user_id == test_user.id
    ).first()
    
    assert prefs is not None
    assert prefs.earned_nova is False
    assert prefs.nearby_nova is True
    assert prefs.wallet_reminders is False


def test_update_notification_prefs_partial(auth_token, test_user, db: Session):
    """Test PUT /v1/notifications/prefs with partial update"""
    # First create prefs
    prefs = UserNotificationPrefs(
        user_id=test_user.id,
        earned_nova=True,
        nearby_nova=True,
        wallet_reminders=True
    )
    db.add(prefs)
    db.commit()
    
    # Update only one field
    response = client.put(
        "/v1/notifications/prefs",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "earned_nova": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["earned_nova"] is False
    assert data["nearby_nova"] is True  # Unchanged
    assert data["wallet_reminders"] is True  # Unchanged

