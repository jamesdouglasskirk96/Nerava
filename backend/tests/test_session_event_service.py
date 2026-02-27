"""
Tests for SessionEventService — session lifecycle, polling, deduplication,
quality scoring, and driver session counting.
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from app.models.user import User
from app.models.session_event import SessionEvent
from app.models.tesla_connection import TeslaConnection
from app.services.session_event_service import SessionEventService, _charging_cache


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


def _make_session(db, driver_id, **overrides):
    defaults = dict(
        id=str(uuid.uuid4()),
        driver_user_id=driver_id,
        charger_id="charger_001",
        charger_network="Tesla",
        connector_type="Tesla",
        power_kw=150.0,
        session_start=datetime.utcnow() - timedelta(minutes=30),
        source="tesla_api",
        source_session_id=f"tesla_{uuid.uuid4()}",
        verified=True,
    )
    defaults.update(overrides)
    session = SessionEvent(**defaults)
    db.add(session)
    db.flush()
    return session


class TestCreateFromTesla:
    """Tests for creating sessions from Tesla API data."""

    def test_create_new_session(self, db):
        """Should create a new SessionEvent from Tesla charge data."""
        driver = _make_user(db)
        charge_data = {
            "charge_energy_added": 12.5,
            "battery_level": 65,
            "charger_power": 11,
            "fast_charger_type": "CCS",
            "lat": 30.4,
            "lng": -97.7,
            "timestamp": "2025-01-01T12:00:00Z",
        }
        vehicle_info = {"id": 99999, "vin": "5YJ3E1EA0JF000001"}

        session = SessionEventService.create_from_tesla(
            db, driver.id, charge_data, vehicle_info, charger_id="ch_001"
        )

        assert session.driver_user_id == driver.id
        assert session.charger_id == "ch_001"
        assert session.charger_network == "Tesla"
        assert session.kwh_delivered == 12.5
        assert session.vehicle_vin == "5YJ3E1EA0JF000001"
        assert session.verified is True
        assert session.session_end is None  # Still active

    def test_update_existing_active_session(self, db):
        """If an active session exists for the driver+vehicle, update telemetry."""
        driver = _make_user(db)
        existing = _make_session(db, driver.id, vehicle_id="99999", kwh_delivered=5.0)

        charge_data = {
            "charge_energy_added": 15.0,
            "battery_level": 80,
            "charger_power": 50,
            "timestamp": "2025-01-01T12:30:00Z",
        }
        vehicle_info = {"id": 99999, "vin": "5YJ3E1EA0JF000001"}

        result = SessionEventService.create_from_tesla(
            db, driver.id, charge_data, vehicle_info
        )

        assert result.id == existing.id
        assert result.kwh_delivered == 15.0
        assert result.battery_end_pct == 80


class TestEndSession:
    """Tests for ending sessions and computing duration."""

    def test_end_session_computes_duration(self, db):
        """Ending a session should compute duration_minutes."""
        driver = _make_user(db)
        start = datetime.utcnow() - timedelta(minutes=45)
        session = _make_session(db, driver.id, session_start=start)

        ended = SessionEventService.end_session(
            db, session.id,
            ended_reason="unplugged",
            battery_end_pct=85,
            kwh_delivered=20.0,
        )

        assert ended is not None
        assert ended.session_end is not None
        assert ended.duration_minutes >= 44  # allow 1 min variance
        assert ended.ended_reason == "unplugged"
        assert ended.battery_end_pct == 85
        assert ended.quality_score is not None

    def test_end_already_ended_session(self, db):
        """Ending an already-ended session should return it unchanged."""
        driver = _make_user(db)
        session = _make_session(
            db, driver.id,
            session_end=datetime.utcnow(),
            duration_minutes=30,
        )

        result = SessionEventService.end_session(db, session.id)
        # Should return the same session without modification
        assert result.id == session.id
        assert result.duration_minutes == 30

    def test_end_nonexistent_session(self, db):
        """Ending a session that doesn't exist should return None."""
        result = SessionEventService.end_session(db, str(uuid.uuid4()))
        assert result is None


class TestGetSessions:
    """Tests for querying sessions."""

    def test_get_active_session(self, db):
        """Should find the active (un-ended) session for a driver."""
        driver = _make_user(db)
        active = _make_session(db, driver.id)
        # Create an ended session too
        _make_session(
            db, driver.id,
            session_end=datetime.utcnow(),
            duration_minutes=20,
        )

        result = SessionEventService.get_active_session(db, driver.id)
        assert result is not None
        assert result.id == active.id

    def test_get_active_session_with_vehicle_filter(self, db):
        """Should filter by vehicle_id when provided."""
        driver = _make_user(db)
        _make_session(db, driver.id, vehicle_id="vehicle_A")
        sess_b = _make_session(db, driver.id, vehicle_id="vehicle_B")

        result = SessionEventService.get_active_session(db, driver.id, vehicle_id="vehicle_B")
        assert result.id == sess_b.id

    def test_get_driver_sessions(self, db):
        """Should return sessions ordered by most recent first."""
        driver = _make_user(db)
        old = _make_session(
            db, driver.id,
            session_start=datetime.utcnow() - timedelta(hours=2),
        )
        new = _make_session(
            db, driver.id,
            session_start=datetime.utcnow() - timedelta(minutes=5),
        )

        sessions = SessionEventService.get_driver_sessions(db, driver.id)
        assert len(sessions) >= 2
        assert sessions[0].id == new.id

    def test_get_charger_sessions(self, db):
        """Should return sessions for a specific charger."""
        driver = _make_user(db)
        _make_session(db, driver.id, charger_id="target_charger")
        _make_session(db, driver.id, charger_id="other_charger")

        results = SessionEventService.get_charger_sessions(db, "target_charger")
        assert all(s.charger_id == "target_charger" for s in results)


class TestCountDriverSessions:
    """Tests for counting completed driver sessions."""

    def test_count_completed_sessions(self, db):
        """Should only count sessions that have session_end set."""
        driver = _make_user(db)
        # Completed sessions
        _make_session(db, driver.id, session_end=datetime.utcnow(), duration_minutes=30)
        _make_session(db, driver.id, session_end=datetime.utcnow(), duration_minutes=20)
        # Active (not ended)
        _make_session(db, driver.id)

        count = SessionEventService.count_driver_sessions(db, driver.id)
        assert count == 2

    def test_count_with_charger_filter(self, db):
        """Should filter by charger_id when provided."""
        driver = _make_user(db)
        _make_session(
            db, driver.id, charger_id="ch_A",
            session_end=datetime.utcnow(), duration_minutes=30,
        )
        _make_session(
            db, driver.id, charger_id="ch_B",
            session_end=datetime.utcnow(), duration_minutes=30,
        )

        count = SessionEventService.count_driver_sessions(db, driver.id, charger_id="ch_A")
        assert count == 1


class TestQualityScore:
    """Tests for the quality score computation."""

    def test_quality_score_long_verified_session(self, db):
        """A 30-min verified session with energy should score high."""
        session = MagicMock()
        session.duration_minutes = 30
        session.kwh_delivered = 10.0
        session.verified = True
        session.battery_start_pct = 40
        session.battery_end_pct = 80

        score = SessionEventService._compute_quality_score(session)
        # 50 baseline + 20 (duration>=15) + 15 (kwh>1) + 10 (verified) + 5 (battery change) = 100
        assert score == 100

    def test_quality_score_suspiciously_short(self, db):
        """A <2 minute session should get a penalty."""
        session = MagicMock()
        session.duration_minutes = 1
        session.kwh_delivered = 0
        session.verified = False
        session.battery_start_pct = None
        session.battery_end_pct = None

        score = SessionEventService._compute_quality_score(session)
        # 50 baseline - 30 (duration<2) = 20
        assert score == 20

    def test_quality_score_clamped_to_0_100(self, db):
        """Score should never go below 0 or above 100."""
        session = MagicMock()
        session.duration_minutes = 60
        session.kwh_delivered = 50.0
        session.verified = True
        session.battery_start_pct = 10
        session.battery_end_pct = 90

        score = SessionEventService._compute_quality_score(session)
        assert 0 <= score <= 100
