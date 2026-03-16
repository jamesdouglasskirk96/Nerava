"""
Tests for TelemetryProcessor — Fleet Telemetry event processing.

Covers: session creation, updates, ending, incentive evaluation,
push notifications, and edge cases (unknown VIN, idempotency).
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from app.services.telemetry_processor import TelemetryProcessor
from app.services.session_event_service import SessionEventService
from app.models.tesla_connection import TeslaConnection
from app.models.session_event import SessionEvent


@pytest.fixture
def tesla_user(db):
    """Create a test user with a Tesla connection."""
    from app.models.user import User

    user = User(
        email="tesla_driver@test.com",
        password_hash="hashed",
        is_active=True,
        role_flags="driver",
    )
    db.add(user)
    db.flush()

    conn = TeslaConnection(
        id=str(uuid.uuid4()),
        user_id=user.id,
        access_token="encrypted_token",
        refresh_token="encrypted_refresh",
        token_expires_at=datetime.utcnow() + timedelta(hours=1),
        vehicle_id="vehicle_123",
        vin="5YJ3E1EA1PF000001",
        vehicle_name="Test Model 3",
        is_active=True,
        telemetry_enabled=True,
        telemetry_configured_at=datetime.utcnow(),
    )
    db.add(conn)
    db.commit()
    db.refresh(user)
    return user


def _charging_telemetry(battery=50, power=11.0, kwh=5.0, lat=30.4, lng=-97.7):
    """Build a telemetry data list for an active charging session."""
    return [
        {"key": "DetailedChargeState", "value": "Charging"},
        {"key": "BatteryLevel", "value": battery},
        {"key": "ACChargingPower", "value": power},
        {"key": "ACChargingEnergyIn", "value": kwh},
        {"key": "Latitude", "value": lat},
        {"key": "Longitude", "value": lng},
    ]


def _disconnected_telemetry(battery=80, kwh=20.0):
    """Build a telemetry data list for a disconnected vehicle."""
    return [
        {"key": "DetailedChargeState", "value": "Disconnected"},
        {"key": "BatteryLevel", "value": battery},
        {"key": "ACChargingEnergyIn", "value": kwh},
    ]


class TestTelemetryProcessorStartSession:
    """Test session creation from telemetry events."""

    def test_charging_creates_session(self, db, tesla_user):
        """Charging state with no active session should create a new session."""
        result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(),
        )

        assert result is not None
        assert result["action"] == "created"
        assert result["session_id"] is not None

        # Verify session was created
        session = db.query(SessionEvent).filter(
            SessionEvent.id == result["session_id"]
        ).first()
        assert session is not None
        assert session.source == "fleet_telemetry"
        assert session.verification_method == "telemetry"
        assert session.driver_user_id == tesla_user.id
        assert session.battery_start_pct == 50

    def test_charging_creates_session_with_push(self, db, tesla_user):
        """Session creation should attempt to send a push notification."""
        with patch("app.services.push_service.send_charging_detected_push") as mock_push:
            result = TelemetryProcessor.process_telemetry(
                db,
                vin="5YJ3E1EA1PF000001",
                telemetry_data=_charging_telemetry(),
            )

            assert result["action"] == "created"
            mock_push.assert_called_once()
            call_args = mock_push.call_args
            assert call_args[0][1] == tesla_user.id  # user_id
            assert call_args[0][2] == result["session_id"]  # session_id

    def test_unknown_vin_returns_none(self, db, tesla_user):
        """Unknown VIN should return None without creating a session."""
        result = TelemetryProcessor.process_telemetry(
            db,
            vin="UNKNOWN_VIN_12345",
            telemetry_data=_charging_telemetry(),
        )
        assert result is None


class TestTelemetryProcessorUpdateSession:
    """Test session updates from telemetry events."""

    def test_charging_updates_existing_session(self, db, tesla_user):
        """Charging state with active session should update telemetry."""
        # Create initial session
        TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(battery=40, kwh=2.0),
        )

        # Update with new data
        result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(battery=60, kwh=10.0, power=22.0),
        )

        assert result is not None
        assert result["action"] == "updated"

        # Verify telemetry was updated
        session = db.query(SessionEvent).filter(
            SessionEvent.id == result["session_id"]
        ).first()
        assert session.battery_end_pct == 60
        assert session.kwh_delivered == 10.0
        assert session.power_kw == 22.0

    def test_no_charge_state_updates_existing(self, db, tesla_user):
        """Location-only telemetry should update an existing active session."""
        # Create session
        TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(),
        )

        # Send location-only update (no DetailedChargeState)
        result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=[
                {"key": "BatteryLevel", "value": 65},
            ],
        )

        assert result is not None
        assert result["action"] == "updated"


class TestTelemetryProcessorEndSession:
    """Test session ending from telemetry events."""

    def test_disconnected_ends_session(self, db, tesla_user):
        """Disconnected state with active session should end it."""
        # Create session
        create_result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(),
        )

        # Manually set session_start back so duration > 0
        session = db.query(SessionEvent).filter(
            SessionEvent.id == create_result["session_id"]
        ).first()
        session.session_start = datetime.utcnow() - timedelta(minutes=30)
        db.commit()

        # End session
        result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_disconnected_telemetry(battery=80, kwh=20.0),
        )

        assert result is not None
        assert result["action"] == "ended"
        assert result["duration_minutes"] >= 29  # ~30 min

        # Verify session was ended
        session = db.query(SessionEvent).filter(
            SessionEvent.id == create_result["session_id"]
        ).first()
        assert session.session_end is not None
        assert session.ended_reason == "telemetry_disconnected"

    def test_complete_state_ends_session(self, db, tesla_user):
        """Complete charge state should end session."""
        TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(),
        )

        result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=[{"key": "DetailedChargeState", "value": "Complete"}],
        )

        assert result is not None
        assert result["action"] == "ended"

    def test_no_active_session_no_action(self, db, tesla_user):
        """Disconnected state with no active session should be no-op."""
        result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_disconnected_telemetry(),
        )
        assert result is None


class TestTelemetryProcessorEdgeCases:
    """Test edge cases and idempotency."""

    def test_duplicate_create_returns_update(self, db, tesla_user):
        """Second charging event should update, not create duplicate."""
        result1 = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(battery=40),
        )
        result2 = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(battery=50),
        )

        assert result1["action"] == "created"
        assert result2["action"] == "updated"
        # Should be the same session
        assert result1["session_id"] == result2["session_id"]

    def test_inactive_connection_ignored(self, db, tesla_user):
        """Inactive Tesla connection should be ignored."""
        conn = db.query(TeslaConnection).filter(
            TeslaConnection.vin == "5YJ3E1EA1PF000001"
        ).first()
        conn.is_active = False
        db.commit()

        result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=_charging_telemetry(),
        )
        assert result is None

    def test_no_charge_state_no_session_noop(self, db, tesla_user):
        """Location-only telemetry with no active session should be no-op."""
        result = TelemetryProcessor.process_telemetry(
            db,
            vin="5YJ3E1EA1PF000001",
            telemetry_data=[
                {"key": "Latitude", "value": 30.4},
                {"key": "Longitude", "value": -97.7},
            ],
        )
        assert result is None
