"""
Tests for wallet summary activity aggregation by day.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models_domain import DomainChargingSession, NovaTransaction, DriverWallet
from app.models import User
from app.routers.drivers_domain import get_driver_wallet_summary


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        id=999,
        username="test_driver",
        email="test@example.com",
        full_name="Test Driver",
        hashed_password="test_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_wallet(db: Session, test_user: User) -> DriverWallet:
    """Create a test wallet."""
    wallet = DriverWallet(
        user_id=test_user.id,
        nova_balance=1000,
        energy_reputation_score=50
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def test_wallet_summary_aggregates_sessions_by_day(db: Session, test_user: User, test_wallet: DriverWallet):
    """
    Test that wallet summary aggregates charging sessions by day.
    
    Creates:
    - 2 sessions on the same day (should aggregate to 1 entry)
    - 1 session on a different day (should be separate entry)
    """
    from app.services.nova_service import NovaService
    
    # Get conversion rate
    from app.core.config import settings
    conversion_rate = settings.NOVA_TO_USD_CONVERSION_RATE_CENTS
    
    # Create sessions on same day (today)
    today = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
    session1_id = "test_session_1"
    session2_id = "test_session_2"
    
    session1 = DomainChargingSession(
        id=session1_id,
        driver_user_id=test_user.id,
        start_time=today,
        end_time=today + timedelta(hours=1),
        kwh_estimate=10.0,
        verified=True,
        verification_source="test"
    )
    db.add(session1)
    
    session2 = DomainChargingSession(
        id=session2_id,
        driver_user_id=test_user.id,
        start_time=today + timedelta(hours=2),
        end_time=today + timedelta(hours=3),
        kwh_estimate=15.0,
        verified=True,
        verification_source="test"
    )
    db.add(session2)
    db.commit()
    
    # Grant Nova for each session
    NovaService.grant_to_driver(
        db=db,
        driver_id=test_user.id,
        amount=50,  # 50 Nova
        type="driver_earn",
        session_id=session1_id
    )
    
    NovaService.grant_to_driver(
        db=db,
        driver_id=test_user.id,
        amount=75,  # 75 Nova
        type="driver_earn",
        session_id=session2_id
    )
    
    # Create session on different day (yesterday)
    yesterday = today - timedelta(days=1)
    session3_id = "test_session_3"
    
    session3 = DomainChargingSession(
        id=session3_id,
        driver_user_id=test_user.id,
        start_time=yesterday,
        end_time=yesterday + timedelta(hours=1),
        kwh_estimate=8.0,
        verified=True,
        verification_source="test"
    )
    db.add(session3)
    db.commit()
    
    NovaService.grant_to_driver(
        db=db,
        driver_id=test_user.id,
        amount=40,  # 40 Nova
        type="driver_earn",
        session_id=session3_id
    )
    
    # Mock get_current_driver to return test_user
    def mock_get_current_driver():
        return test_user
    
    # Call wallet summary
    summary = get_driver_wallet_summary(
        user=test_user,
        db=db
    )
    
    # Verify response structure
    assert "recent_activity" in summary
    activities = summary["recent_activity"]
    
    # Should have aggregated entries (at least 2: today aggregated, yesterday separate)
    assert len(activities) >= 2
    
    # Find aggregated daily entries
    daily_activities = [a for a in activities if a.get("type") == "charging_session" and a.get("aggregation") == "daily"]
    assert len(daily_activities) >= 2
    
    # Find today's aggregated entry
    today_activity = next(
        (a for a in daily_activities if a.get("session_date") == today.date().isoformat()),
        None
    )
    assert today_activity is not None
    
    # Verify aggregation: should have session_count=2 and summed nova_earned
    assert today_activity["session_count"] == 2
    assert today_activity["nova_earned"] == 125  # 50 + 75
    assert today_activity["amount_cents"] == 125 * conversion_rate
    
    # Verify yesterday's entry
    yesterday_activity = next(
        (a for a in daily_activities if a.get("session_date") == yesterday.date().isoformat()),
        None
    )
    assert yesterday_activity is not None
    assert yesterday_activity["session_count"] == 1
    assert yesterday_activity["nova_earned"] == 40
    assert yesterday_activity["amount_cents"] == 40 * conversion_rate

