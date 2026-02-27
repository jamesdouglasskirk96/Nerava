"""
Tests for IncentiveEngine — session-to-campaign matching and grant creation.

Covers: rule matching, grant creation, budget decrement, edge cases
(no matching rules, exhausted budget, duplicate grants).
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from app.models.user import User
from app.models.campaign import Campaign
from app.models.session_event import SessionEvent, IncentiveGrant
from app.services.incentive_engine import IncentiveEngine


def _make_user(db, email="driver@test.com"):
    user = User(
        email=email,
        password_hash="hashed",
        is_active=True,
        role_flags="driver",
    )
    db.add(user)
    db.flush()
    return user


def _make_campaign(db, user, **overrides):
    defaults = dict(
        id=str(uuid.uuid4()),
        sponsor_name="Test Sponsor",
        name="Test Campaign",
        campaign_type="custom",
        status="active",
        priority=10,
        budget_cents=100000,  # $1000
        spent_cents=0,
        cost_per_session_cents=500,  # $5 per session
        sessions_granted=0,
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=30),
        rule_min_duration_minutes=15,
        created_by_user_id=user.id,
    )
    defaults.update(overrides)
    campaign = Campaign(**defaults)
    db.add(campaign)
    db.flush()
    return campaign


def _make_session(db, driver, **overrides):
    defaults = dict(
        id=str(uuid.uuid4()),
        driver_user_id=driver.id,
        charger_id="charger_001",
        charger_network="Tesla",
        zone_id="domain_austin",
        connector_type="Tesla",
        power_kw=150.0,
        session_start=datetime.utcnow() - timedelta(minutes=45),
        session_end=datetime.utcnow(),
        duration_minutes=45,
        source="tesla_api",
        source_session_id=f"tesla_{uuid.uuid4()}",
        verified=True,
        lat=30.4,
        lng=-97.7,
    )
    defaults.update(overrides)
    session = SessionEvent(**defaults)
    db.add(session)
    db.flush()
    return session


class TestIncentiveEngine:
    """Tests for IncentiveEngine.evaluate_session and rule matching."""

    @patch("app.services.incentive_engine.CampaignService.get_active_campaigns")
    @patch("app.services.incentive_engine.CampaignService.decrement_budget_atomic", return_value=True)
    @patch("app.services.incentive_engine.CampaignService.check_driver_caps", return_value=True)
    @patch("app.services.nova_service.NovaService.grant_to_driver")
    def test_evaluate_session_creates_grant(
        self, mock_nova_grant, mock_caps, mock_decrement, mock_active, db
    ):
        """A completed session matching an active campaign should create a grant."""
        driver = _make_user(db)
        campaign = _make_campaign(db, driver)
        session = _make_session(db, driver)

        mock_active.return_value = [campaign]
        mock_nova_grant.return_value = MagicMock(id=str(uuid.uuid4()))

        grant = IncentiveEngine.evaluate_session(db, session)

        assert grant is not None
        assert grant.amount_cents == campaign.cost_per_session_cents
        assert grant.campaign_id == campaign.id
        assert grant.session_event_id == session.id
        assert grant.status == "granted"
        mock_decrement.assert_called_once_with(db, campaign.id, campaign.cost_per_session_cents)

    def test_evaluate_session_skips_if_not_ended(self, db):
        """Sessions without session_end should be skipped."""
        driver = _make_user(db)
        session = _make_session(db, driver, session_end=None, duration_minutes=None)

        result = IncentiveEngine.evaluate_session(db, session)
        assert result is None

    def test_evaluate_session_skips_if_too_short(self, db):
        """Sessions shorter than 1 minute should be skipped."""
        driver = _make_user(db)
        session = _make_session(db, driver, duration_minutes=0)

        result = IncentiveEngine.evaluate_session(db, session)
        assert result is None

    @patch("app.services.incentive_engine.CampaignService.get_active_campaigns")
    def test_evaluate_session_no_active_campaigns(self, mock_active, db):
        """Returns None when no active campaigns exist."""
        driver = _make_user(db)
        session = _make_session(db, driver)
        mock_active.return_value = []

        result = IncentiveEngine.evaluate_session(db, session)
        assert result is None

    @patch("app.services.incentive_engine.CampaignService.get_active_campaigns")
    @patch("app.services.incentive_engine.CampaignService.decrement_budget_atomic", return_value=True)
    @patch("app.services.incentive_engine.CampaignService.check_driver_caps", return_value=True)
    @patch("app.services.nova_service.NovaService.grant_to_driver")
    def test_idempotent_existing_grant_returned(
        self, mock_nova, mock_caps, mock_decrement, mock_active, db
    ):
        """If a grant already exists for the session, return it (idempotency)."""
        driver = _make_user(db)
        campaign = _make_campaign(db, driver)
        session = _make_session(db, driver)

        # Pre-create a grant for this session
        existing_grant = IncentiveGrant(
            id=str(uuid.uuid4()),
            session_event_id=session.id,
            campaign_id=campaign.id,
            driver_user_id=driver.id,
            amount_cents=500,
            status="granted",
            idempotency_key=f"campaign_{campaign.id}_session_{session.id}",
            granted_at=datetime.utcnow(),
        )
        db.add(existing_grant)
        db.flush()

        result = IncentiveEngine.evaluate_session(db, session)
        assert result is not None
        assert result.id == existing_grant.id
        # Should NOT have called decrement budget again
        mock_decrement.assert_not_called()

    @patch("app.services.incentive_engine.CampaignService.get_active_campaigns")
    @patch("app.services.incentive_engine.CampaignService.decrement_budget_atomic", return_value=False)
    @patch("app.services.incentive_engine.CampaignService.check_driver_caps", return_value=True)
    def test_exhausted_budget_returns_none(self, mock_caps, mock_decrement, mock_active, db):
        """Returns None when the campaign budget is exhausted."""
        driver = _make_user(db)
        campaign = _make_campaign(db, driver)
        session = _make_session(db, driver)
        mock_active.return_value = [campaign]

        result = IncentiveEngine.evaluate_session(db, session)
        assert result is None

    def test_session_matches_campaign_duration_too_short(self, db):
        """Session below minimum duration should not match."""
        driver = _make_user(db)
        campaign = _make_campaign(db, driver, rule_min_duration_minutes=30)
        session = _make_session(db, driver, duration_minutes=20)

        with patch("app.services.incentive_engine.CampaignService.check_driver_caps", return_value=True):
            result = IncentiveEngine._session_matches_campaign(db, session, campaign)
        assert result is False

    def test_session_matches_campaign_charger_id_filter(self, db):
        """Session at a non-matching charger should not match."""
        driver = _make_user(db)
        campaign = _make_campaign(db, driver, rule_charger_ids=["charger_999"])
        session = _make_session(db, driver, charger_id="charger_001")

        with patch("app.services.incentive_engine.CampaignService.check_driver_caps", return_value=True):
            result = IncentiveEngine._session_matches_campaign(db, session, campaign)
        assert result is False

    def test_haversine_m_calculation(self):
        """Haversine should compute reasonable distance between two points."""
        # Austin TX Domain area: approx 0 distance for same point
        dist = IncentiveEngine._haversine_m(30.4, -97.7, 30.4, -97.7)
        assert dist == pytest.approx(0.0, abs=1.0)

        # ~111km per degree of latitude at equator
        dist2 = IncentiveEngine._haversine_m(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < dist2 < 112_000

    def test_time_in_window_normal(self):
        """Time within a normal daytime window."""
        assert IncentiveEngine._time_in_window("10:00", "09:00", "17:00") is True
        assert IncentiveEngine._time_in_window("08:00", "09:00", "17:00") is False

    def test_time_in_window_overnight(self):
        """Time within an overnight window (e.g., 22:00-06:00)."""
        assert IncentiveEngine._time_in_window("23:00", "22:00", "06:00") is True
        assert IncentiveEngine._time_in_window("03:00", "22:00", "06:00") is True
        assert IncentiveEngine._time_in_window("12:00", "22:00", "06:00") is False
