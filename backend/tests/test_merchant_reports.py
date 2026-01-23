"""
Tests for Merchant Reports Service and API

Tests merchant report aggregation, API endpoints, and Domain report generation.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import text

from app.main_simple import app as app_instance
from app.db import get_db
from app.services.merchant_reports import (
    get_merchant_report,
    get_domain_merchant_reports_for_period,
    MerchantReport,
    DEFAULT_AVG_TICKET_CENTS
)
from app.models_while_you_charge import Merchant
from app.models_extra import RewardEvent
from app.services.nova import cents_to_nova

# Import app for dependency override
# Use conftest fixtures: db, client


@pytest.fixture
def test_merchant(db: Session):
    """Create a test merchant."""
    merchant = Merchant(
        id="m_test_coffee_001",
        name="Test Coffee Shop",
        category="coffee",
        lat=30.4021,
        lng=-97.7266,
        address="11601 Domain Dr, Austin, TX 78758"
    )
    db.add(merchant)
    db.commit()
    return merchant


@pytest.fixture
def test_users():
    """Generate test user IDs."""
    return ["user_001", "user_002", "user_003"]


@pytest.fixture
def test_reward_events(db: Session, test_merchant, test_users):
    """Create test reward events for merchant visits."""
    now = datetime.utcnow()
    
    events = []
    
    # User 1: 2 visits
    for i in range(2):
        event = RewardEvent(
            user_id=test_users[0],
            source="merchant_visit",
            gross_cents=25,
            net_cents=25,
            community_cents=0,
            meta={"merchant_id": test_merchant.id, "session_id": f"session_{i}"},
            created_at=now - timedelta(days=3)
        )
        db.add(event)
        events.append(event)
    
    # User 2: 1 visit
    event = RewardEvent(
        user_id=test_users[1],
        source="merchant_visit",
        gross_cents=25,
        net_cents=25,
        community_cents=0,
        meta={"merchant_id": test_merchant.id, "session_id": "session_2"},
        created_at=now - timedelta(days=2)
    )
    db.add(event)
    events.append(event)
    
    # User 3: 1 visit (outside period)
    event = RewardEvent(
        user_id=test_users[2],
        source="merchant_visit",
        gross_cents=25,
        net_cents=25,
        community_cents=0,
        meta={"merchant_id": test_merchant.id, "session_id": "session_3"},
        created_at=now - timedelta(days=10)  # Outside 7-day window
    )
    db.add(event)
    events.append(event)
    
    db.commit()
    return events


# ============================================
# Test 1: Merchant report aggregates correctly
# ============================================
def test_merchant_report_aggregation(db: Session, test_merchant, test_reward_events):
    """Test that merchant report correctly aggregates visit data."""
    now = datetime.utcnow()
    period_start = now - timedelta(days=7)
    period_end = now
    
    report = get_merchant_report(
        db=db,
        merchant_id=test_merchant.id,
        period_start=period_start,
        period_end=period_end
    )
    
    assert report is not None
    assert report.merchant_id == test_merchant.id
    assert report.merchant_name == test_merchant.name
    assert report.period_start == period_start
    assert report.period_end == period_end
    
    # Should have 3 visits (2 from user_001, 1 from user_002)
    # Note: user_003's visit is outside the period
    assert report.ev_visits == 3
    
    # Should have 2 unique drivers (user_001 and user_002)
    assert report.unique_drivers == 2
    
    # Total rewards: 3 visits * 25 cents = 75 cents
    assert report.total_rewards_cents == 75
    
    # Nova should equal cents (1:1 mapping)
    assert report.total_nova_awarded == cents_to_nova(75)
    
    # Implied revenue: 3 visits * 800 cents (default) = 2400 cents
    assert report.implied_revenue_cents == 2400


def test_merchant_report_with_custom_avg_ticket(db: Session, test_merchant, test_reward_events):
    """Test merchant report with custom average ticket size."""
    now = datetime.utcnow()
    period_start = now - timedelta(days=7)
    period_end = now
    
    custom_ticket = 1200  # $12
    
    report = get_merchant_report(
        db=db,
        merchant_id=test_merchant.id,
        period_start=period_start,
        period_end=period_end,
        avg_ticket_cents=custom_ticket
    )
    
    assert report is not None
    assert report.ev_visits == 3
    # Implied revenue: 3 visits * 1200 cents = 3600 cents
    assert report.implied_revenue_cents == 3600


def test_merchant_report_nonexistent_merchant(db: Session):
    """Test that None is returned for nonexistent merchant."""
    now = datetime.utcnow()
    period_start = now - timedelta(days=7)
    period_end = now
    
    report = get_merchant_report(
        db=db,
        merchant_id="nonexistent_merchant",
        period_start=period_start,
        period_end=period_end
    )
    
    assert report is None


# ============================================
# Test 2: API returns report
# ============================================
def test_api_merchant_report(db: Session, test_merchant, test_reward_events):
    """Test that API endpoint returns merchant report."""
    # Override get_db dependency for this test
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        response = client.get(f"/v1/merchants/{test_merchant.id}/report?period=week")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "merchant_id" in data
        assert "merchant_name" in data
        assert "ev_visits" in data
        assert "unique_drivers" in data
        assert "total_nova_awarded" in data
        assert "total_rewards_cents" in data
        
        assert data["merchant_id"] == test_merchant.id
        assert data["ev_visits"] == 3
        assert data["unique_drivers"] == 2
    finally:
        app_instance.dependency_overrides.clear()


def test_api_merchant_report_30d(db: Session, test_merchant, test_reward_events):
    """Test API endpoint with 30d period."""
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        response = client.get(f"/v1/merchants/{test_merchant.id}/report?period=30d")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include the visit from 10 days ago
        assert data["ev_visits"] == 4  # 3 from last week + 1 from 10 days ago
    finally:
        app_instance.dependency_overrides.clear()


def test_api_merchant_report_not_found(db: Session):
    """Test API endpoint returns 404 for nonexistent merchant."""
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        response = client.get("/v1/merchants/nonexistent/report?period=week")
        
        assert response.status_code == 404
    finally:
        app_instance.dependency_overrides.clear()


def test_api_merchant_report_invalid_period(db: Session, test_merchant):
    """Test API endpoint returns 400 for invalid period."""
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        response = client.get(f"/v1/merchants/{test_merchant.id}/report?period=invalid")
        
        assert response.status_code == 400
    finally:
        app_instance.dependency_overrides.clear()


def test_api_merchant_report_custom_ticket(db: Session, test_merchant, test_reward_events):
    """Test API endpoint with custom avg_ticket_cents."""
    from app.db import get_db
    app_instance.dependency_overrides[get_db] = lambda: db
    
    try:
        response = client.get(
            f"/v1/merchants/{test_merchant.id}/report?period=week&avg_ticket_cents=1200"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["implied_revenue_cents"] == 3600  # 3 visits * 1200 cents
    finally:
        app_instance.dependency_overrides.clear()


# ============================================
# Test 3: Domain reports service
# ============================================
def test_domain_merchant_reports_for_period(db: Session, test_merchant, test_reward_events):
    """Test Domain merchant reports aggregation across multiple merchants."""
    # Create a second merchant with visits
    merchant2 = Merchant(
        id="m_test_restaurant_001",
        name="Test Restaurant",
        category="restaurant",
        lat=30.4030,
        lng=-97.7270,
        address="11602 Domain Dr, Austin, TX 78758"
    )
    db.add(merchant2)
    
    # Add visit for second merchant
    now = datetime.utcnow()
    event = RewardEvent(
        user_id="user_004",
        source="merchant_visit",
        gross_cents=25,
        net_cents=25,
        community_cents=0,
        meta={"merchant_id": merchant2.id, "session_id": "session_4"},
        created_at=now - timedelta(days=1)
    )
    db.add(event)
    db.commit()
    
    # Get reports for period
    period_start = now - timedelta(days=7)
    period_end = now
    
    reports = get_domain_merchant_reports_for_period(
        db=db,
        period_start=period_start,
        period_end=period_end
    )
    
    # Should have reports for both merchants
    assert len(reports) >= 2
    
    # Find reports
    report1 = next((r for r in reports if r.merchant_id == test_merchant.id), None)
    report2 = next((r for r in reports if r.merchant_id == merchant2.id), None)
    
    assert report1 is not None
    assert report2 is not None
    
    # Verify metrics
    assert report1.ev_visits == 3
    assert report2.ev_visits == 1
    
    # Reports should be sorted by ev_visits descending
    assert reports[0].ev_visits >= reports[1].ev_visits


def test_domain_merchant_reports_no_visits(db: Session):
    """Test Domain reports with no visits in period."""
    # Use a period far in the past to ensure no visits
    now = datetime.utcnow()
    period_start = now - timedelta(days=365)
    period_end = now - timedelta(days=360)
    
    reports = get_domain_merchant_reports_for_period(
        db=db,
        period_start=period_start,
        period_end=period_end
    )
    
    # Should return empty list (or list with zero visits per merchant)
    assert isinstance(reports, list)
    # Reports may exist but should have 0 visits

