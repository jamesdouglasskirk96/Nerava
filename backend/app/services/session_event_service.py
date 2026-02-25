"""
Session Event Service — Manages charging session lifecycle.

Creates SessionEvent records from Tesla API data (or other sources).
Triggers incentive evaluation on session END, not session start.
Polls one vehicle only, with backoff and caching.
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.session_event import SessionEvent
from app.models.tesla_connection import TeslaConnection

logger = logging.getLogger(__name__)

# Cache: driver_id -> last_poll_result to reduce redundant API calls
_charging_cache: Dict[int, Dict[str, Any]] = {}


class SessionEventService:
    """Manages charging session lifecycle and incentive triggering."""

    @staticmethod
    def create_from_tesla(
        db: Session,
        driver_id: int,
        charge_data: dict,
        vehicle_info: dict,
        charger_id: Optional[str] = None,
        charger_network: str = "Tesla",
    ) -> SessionEvent:
        """
        Create or update a session event from Tesla API charge_state data.

        Args:
            charge_data: Tesla charge_state response
            vehicle_info: Vehicle metadata (id, vin, display_name)
        """
        vehicle_id = str(vehicle_info.get("id", ""))
        vin = vehicle_info.get("vin")

        # Build a source_session_id for dedup
        # Tesla doesn't give a unique session ID, so use vehicle_id + approximate start time
        source_session_id = f"tesla_{vehicle_id}_{charge_data.get('timestamp', '')}"

        # Check for existing active session for this driver+vehicle
        active = SessionEventService.get_active_session(db, driver_id, vehicle_id=vehicle_id)
        if active:
            # Update telemetry on existing session
            active.kwh_delivered = charge_data.get("charge_energy_added")
            active.battery_end_pct = charge_data.get("battery_level")
            active.power_kw = charge_data.get("charger_power")
            active.updated_at = datetime.utcnow()
            db.flush()
            return active

        # Create new session event
        session_event = SessionEvent(
            id=str(uuid.uuid4()),
            driver_user_id=driver_id,
            charger_id=charger_id,
            charger_network=charger_network,
            connector_type=charge_data.get("fast_charger_type") or "Tesla",
            power_kw=charge_data.get("charger_power"),
            session_start=datetime.utcnow(),
            source="tesla_api",
            source_session_id=source_session_id,
            verified=True,
            verification_method="api_polling",
            lat=charge_data.get("lat"),
            lng=charge_data.get("lng"),
            battery_start_pct=charge_data.get("battery_level"),
            vehicle_id=vehicle_id,
            vehicle_vin=vin,
            kwh_delivered=charge_data.get("charge_energy_added"),
        )
        db.add(session_event)
        db.flush()
        logger.info(f"Created session_event {session_event.id} for driver {driver_id}")
        return session_event

    @staticmethod
    def end_session(
        db: Session,
        session_event_id: str,
        ended_reason: str = "unplugged",
        battery_end_pct: Optional[int] = None,
        kwh_delivered: Optional[float] = None,
    ) -> Optional[SessionEvent]:
        """
        End an active session. Computes duration.
        IncentiveEngine should be called AFTER this returns.
        """
        session = db.query(SessionEvent).filter(SessionEvent.id == session_event_id).first()
        if not session or session.session_end is not None:
            return session

        now = datetime.utcnow()
        session.session_end = now
        session.duration_minutes = int((now - session.session_start).total_seconds() / 60)
        session.ended_reason = ended_reason
        if battery_end_pct is not None:
            session.battery_end_pct = battery_end_pct
        if kwh_delivered is not None:
            session.kwh_delivered = kwh_delivered

        # Compute quality score (basic heuristics)
        session.quality_score = SessionEventService._compute_quality_score(session)
        session.updated_at = now
        db.flush()

        logger.info(
            f"Ended session {session.id}: {session.duration_minutes}min, "
            f"reason={ended_reason}, quality={session.quality_score}"
        )
        return session

    @staticmethod
    def get_active_session(
        db: Session,
        driver_id: int,
        vehicle_id: Optional[str] = None,
    ) -> Optional[SessionEvent]:
        """Find the active (un-ended) session for a driver."""
        query = db.query(SessionEvent).filter(
            SessionEvent.driver_user_id == driver_id,
            SessionEvent.session_end.is_(None),
        )
        if vehicle_id:
            query = query.filter(SessionEvent.vehicle_id == vehicle_id)
        return query.order_by(desc(SessionEvent.session_start)).first()

    @staticmethod
    def get_driver_sessions(
        db: Session,
        driver_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionEvent]:
        """Get a driver's charging sessions, most recent first."""
        return (
            db.query(SessionEvent)
            .filter(SessionEvent.driver_user_id == driver_id)
            .order_by(desc(SessionEvent.session_start))
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_charger_sessions(
        db: Session,
        charger_id: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SessionEvent]:
        """Get sessions at a specific charger."""
        query = db.query(SessionEvent).filter(SessionEvent.charger_id == charger_id)
        if since:
            query = query.filter(SessionEvent.session_start >= since)
        if until:
            query = query.filter(SessionEvent.session_start <= until)
        return query.order_by(desc(SessionEvent.session_start)).limit(limit).all()

    @staticmethod
    def poll_driver_session(
        db: Session,
        driver_id: int,
        tesla_connection: "TeslaConnection",
        tesla_oauth_service: Any,
    ) -> dict:
        """
        Poll Tesla API for a single driver's charging state.
        Creates/updates/ends session events as needed.
        Implements caching and backoff per review.

        Returns: {session_active, session_id, duration_minutes, ...}
        """
        from app.services.incentive_engine import IncentiveEngine

        # Check cache: skip if polled within 30s and still charging
        cache_key = driver_id
        cached = _charging_cache.get(cache_key)
        if cached and cached.get("still_charging"):
            last_poll = cached.get("last_poll", datetime.min)
            if (datetime.utcnow() - last_poll).total_seconds() < 30:
                active = SessionEventService.get_active_session(db, driver_id)
                if active:
                    return {
                        "session_active": True,
                        "session_id": active.id,
                        "duration_minutes": int((datetime.utcnow() - active.session_start).total_seconds() / 60),
                        "kwh_delivered": active.kwh_delivered,
                        "cached": True,
                    }

        # Poll Tesla API — ONE vehicle only (per review)
        try:
            vehicle_id = tesla_connection.vehicle_id
            if not vehicle_id:
                return {"session_active": False, "error": "no_vehicle_selected"}

            vehicle_data = tesla_oauth_service.get_vehicle_data(
                tesla_connection.access_token, vehicle_id
            )
            charge_state = vehicle_data.get("response", {}).get("charge_state", {})
            charging_state = charge_state.get("charging_state")
            is_charging = charging_state in {"Charging", "Starting"}

        except Exception as e:
            # Backoff on error — clear cache, don't crash
            logger.warning(f"Tesla poll error for driver {driver_id}: {e}")
            _charging_cache.pop(cache_key, None)
            return {"session_active": False, "error": "poll_failed"}

        # Update cache
        _charging_cache[cache_key] = {
            "still_charging": is_charging,
            "last_poll": datetime.utcnow(),
        }

        active = SessionEventService.get_active_session(db, driver_id)

        if is_charging and not active:
            # Start new session
            vehicle_info = {"id": vehicle_id, "vin": tesla_connection.vin}
            session = SessionEventService.create_from_tesla(
                db, driver_id, charge_state, vehicle_info
            )
            db.commit()
            return {
                "session_active": True,
                "session_id": session.id,
                "duration_minutes": 0,
                "kwh_delivered": session.kwh_delivered,
            }

        elif is_charging and active:
            # Update existing session telemetry
            active.kwh_delivered = charge_state.get("charge_energy_added")
            active.battery_end_pct = charge_state.get("battery_level")
            active.power_kw = charge_state.get("charger_power")
            active.updated_at = datetime.utcnow()
            db.commit()
            return {
                "session_active": True,
                "session_id": active.id,
                "duration_minutes": int((datetime.utcnow() - active.session_start).total_seconds() / 60),
                "kwh_delivered": active.kwh_delivered,
            }

        elif not is_charging and active:
            # Session ended — evaluate incentives (per review: pay on END)
            session = SessionEventService.end_session(
                db, active.id,
                ended_reason="unplugged",
                battery_end_pct=charge_state.get("battery_level"),
                kwh_delivered=charge_state.get("charge_energy_added"),
            )
            # Evaluate incentives now that session is complete
            grant = None
            if session and session.duration_minutes and session.duration_minutes > 0:
                grant = IncentiveEngine.evaluate_session(db, session)

            db.commit()
            _charging_cache.pop(cache_key, None)

            return {
                "session_active": False,
                "session_id": session.id if session else None,
                "duration_minutes": session.duration_minutes if session else 0,
                "kwh_delivered": session.kwh_delivered if session else None,
                "session_ended": True,
                "incentive_granted": grant is not None,
                "incentive_amount_cents": grant.amount_cents if grant else 0,
            }

        else:
            # Not charging and no active session
            return {"session_active": False}

    @staticmethod
    def _compute_quality_score(session: SessionEvent) -> int:
        """
        Basic anti-fraud quality score (0-100).
        Higher is better. Can be expanded with more heuristics later.
        """
        score = 50  # baseline

        # Duration bonus: longer sessions are more likely genuine
        if session.duration_minutes:
            if session.duration_minutes >= 15:
                score += 20
            elif session.duration_minutes >= 5:
                score += 10
            elif session.duration_minutes < 2:
                score -= 30  # suspiciously short

        # Energy delivered bonus
        if session.kwh_delivered and session.kwh_delivered > 1.0:
            score += 15
        elif session.kwh_delivered and session.kwh_delivered > 0:
            score += 5

        # Verified bonus
        if session.verified:
            score += 10

        # Battery change bonus (battery_end > battery_start = real charging)
        if session.battery_start_pct and session.battery_end_pct:
            if session.battery_end_pct > session.battery_start_pct:
                score += 5

        return max(0, min(100, score))

    @staticmethod
    def count_driver_sessions(
        db: Session,
        driver_id: int,
        charger_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> int:
        """Count completed sessions for a driver, optionally filtered."""
        query = db.query(SessionEvent).filter(
            SessionEvent.driver_user_id == driver_id,
            SessionEvent.session_end.is_not(None),
        )
        if charger_id:
            query = query.filter(SessionEvent.charger_id == charger_id)
        if since:
            query = query.filter(SessionEvent.session_start >= since)
        return query.count()
