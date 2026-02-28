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

        # Build a stable source_session_id for dedup
        # Use vehicle_id + current date to avoid duplicates within same day
        # (Tesla doesn't provide a unique charge session ID)
        now = datetime.utcnow()
        source_session_id = f"tesla_{vehicle_id}_{now.strftime('%Y%m%d_%H%M')}"

        # Create new session event
        session_event = SessionEvent(
            id=str(uuid.uuid4()),
            driver_user_id=driver_id,
            user_id=driver_id,
            charger_id=charger_id,
            charger_network=charger_network,
            connector_type=charge_data.get("fast_charger_type") or "Tesla",
            power_kw=charge_data.get("charger_power"),
            session_start=now,
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
    async def poll_driver_session(
        db: Session,
        driver_id: int,
        tesla_connection: "TeslaConnection",
        tesla_oauth_service: Any,
        device_lat: Optional[float] = None,
        device_lng: Optional[float] = None,
    ) -> dict:
        """
        Poll Tesla API for a single driver's charging state.
        Creates/updates/ends session events as needed.
        Implements caching and backoff per review.

        Returns: {session_active, session_id, duration_minutes, ...}
        """
        from app.services.incentive_engine import IncentiveEngine

        # Check cache: skip if polled within 15s and still charging
        cache_key = driver_id
        cached = _charging_cache.get(cache_key)
        if cached and cached.get("still_charging"):
            last_poll = cached.get("last_poll", datetime.min)
            if (datetime.utcnow() - last_poll).total_seconds() < 15:
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
        # Includes wake-up + retry for sleeping vehicles
        try:
            vehicle_id = tesla_connection.vehicle_id
            if not vehicle_id:
                return {"session_active": False, "error": "no_vehicle_selected"}

            # Get a valid (refreshed if needed) access token
            from app.services.tesla_oauth import get_valid_access_token
            access_token = await get_valid_access_token(
                db, tesla_connection, tesla_oauth_service
            )
            if not access_token:
                return {"session_active": False, "error": "token_expired"}

            # get_vehicle_data with wake-up and retry on 408/sleeping
            import asyncio
            import httpx
            vehicle_data = None
            for attempt in range(3):
                try:
                    # Wake vehicle before data request (best-effort)
                    if attempt > 0:
                        try:
                            await tesla_oauth_service.wake_vehicle(access_token, vehicle_id)
                        except Exception:
                            pass
                        await asyncio.sleep(3)

                    vehicle_data = await tesla_oauth_service.get_vehicle_data(
                        access_token, vehicle_id
                    )
                    break  # Success
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 408 and attempt < 2:
                        logger.info(
                            "Vehicle %s returned 408 (attempt %d/3), waking and retrying",
                            vehicle_id, attempt + 1
                        )
                        continue
                    raise  # Non-408 or final attempt — propagate

            if vehicle_data is None:
                return {"session_active": False, "error": "vehicle_unavailable"}

            charge_state = vehicle_data.get("charge_state", {})
            drive_state = vehicle_data.get("drive_state", {})
            charging_state = charge_state.get("charging_state")
            is_charging = charging_state in {"Charging", "Starting"}

            # Merge location from drive_state into charge_state for downstream use
            charge_state["lat"] = drive_state.get("latitude")
            charge_state["lng"] = drive_state.get("longitude")

        except Exception as e:
            # Backoff on error — clear cache, don't crash
            logger.warning(f"Tesla poll error for driver {driver_id}: {e}")
            _charging_cache.pop(cache_key, None)

            # Auto-close stale sessions on poll error (>15 min since last update)
            stale = SessionEventService._close_stale_session(db, driver_id)
            if stale:
                db.commit()
                return {
                    "session_active": False,
                    "session_id": stale.id,
                    "duration_minutes": stale.duration_minutes or 0,
                    "session_ended": True,
                    "incentive_granted": False,
                    "incentive_amount_cents": 0,
                }

            return {"session_active": False, "error": "poll_failed"}

        # Update cache
        _charging_cache[cache_key] = {
            "still_charging": is_charging,
            "last_poll": datetime.utcnow(),
        }

        active = SessionEventService.get_active_session(db, driver_id)

        if is_charging and not active:
            # Start new session — match to nearest known charger
            vehicle_info = {"id": vehicle_id, "vin": tesla_connection.vin}
            matched_charger_id = None
            tesla_lat = charge_state.get("lat")
            tesla_lng = charge_state.get("lng")
            if tesla_lat and tesla_lng:
                try:
                    from app.services.intent_service import find_nearest_charger
                    result = find_nearest_charger(db, tesla_lat, tesla_lng, radius_m=500)
                    if result:
                        matched_charger, distance_m = result
                        matched_charger_id = matched_charger.id
                        logger.info(
                            f"Matched session to charger {matched_charger_id} "
                            f"({matched_charger.name}) at {distance_m:.0f}m"
                        )
                except Exception as e:
                    logger.warning(f"Charger matching failed: {e}")

            # Store device location in metadata (start of trail)
            metadata = {}
            if device_lat is not None and device_lng is not None:
                metadata["device_lat"] = device_lat
                metadata["device_lng"] = device_lng
                metadata["location_trail"] = [{
                    "lat": device_lat,
                    "lng": device_lng,
                    "ts": datetime.utcnow().isoformat(),
                }]
                logger.info(f"Device location: {device_lat}, {device_lng}")

            session = SessionEventService.create_from_tesla(
                db, driver_id, charge_state, vehicle_info,
                charger_id=matched_charger_id,
            )
            if metadata:
                session.session_metadata = metadata
                db.flush()
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

            # Backfill Tesla location if missing from session start
            tesla_lat = charge_state.get("lat")
            tesla_lng = charge_state.get("lng")
            if not active.lat and tesla_lat:
                active.lat = tesla_lat
                active.lng = tesla_lng
                # Also try to match charger if not already set
                if not active.charger_id and tesla_lat and tesla_lng:
                    try:
                        from app.services.intent_service import find_nearest_charger
                        result = find_nearest_charger(db, tesla_lat, tesla_lng, radius_m=500)
                        if result:
                            active.charger_id = result[0].id
                            logger.info(f"Backfilled charger_id={active.charger_id} on session {active.id}")
                    except Exception:
                        pass

            # Append device location to location trail in metadata
            if device_lat is not None and device_lng is not None:
                meta = active.session_metadata or {}
                meta["device_lat"] = device_lat
                meta["device_lng"] = device_lng
                trail = meta.get("location_trail", [])
                trail.append({
                    "lat": device_lat,
                    "lng": device_lng,
                    "ts": datetime.utcnow().isoformat(),
                })
                # Keep last 120 points (~60 min at 30s intervals)
                if len(trail) > 120:
                    trail = trail[-120:]
                meta["location_trail"] = trail
                active.session_metadata = meta

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

            # Award base reputation for valid sessions without incentive grants
            if session and not grant and session.duration_minutes and session.duration_minutes > 0:
                quality = session.quality_score or 0
                if quality > 30:
                    try:
                        from app.models_domain import DriverWallet as DomainWallet
                        wallet = db.query(DomainWallet).filter(
                            DomainWallet.user_id == driver_id
                        ).first()
                        if wallet:
                            wallet.energy_reputation_score = (wallet.energy_reputation_score or 0) + 5
                            logger.info(
                                "Awarded 5 base reputation points to driver %s "
                                "(session %s, no incentive grant)", driver_id, session.id
                            )
                    except Exception as e:
                        logger.debug("Base reputation award failed (non-fatal): %s", e)

            db.commit()
            _charging_cache.pop(cache_key, None)

            # Send push notification for incentive earned (best-effort)
            if grant and grant.amount_cents > 0:
                try:
                    from app.services.push_service import send_incentive_earned_push
                    send_incentive_earned_push(db, driver_id, grant.amount_cents)
                except Exception as push_err:
                    logger.debug("Push notification failed (non-fatal): %s", push_err)

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
            # Not charging and no active session — also check for stale sessions
            stale = SessionEventService._close_stale_session(db, driver_id)
            if stale:
                db.commit()
                return {
                    "session_active": False,
                    "session_id": stale.id,
                    "duration_minutes": stale.duration_minutes or 0,
                    "session_ended": True,
                    "incentive_granted": False,
                    "incentive_amount_cents": 0,
                }
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
    def _close_stale_session(
        db: Session,
        driver_id: int,
        stale_minutes: int = 5,
    ) -> Optional[SessionEvent]:
        """
        Find and close any active session that hasn't been updated in
        `stale_minutes`. Returns the closed session or None.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=stale_minutes)
        stale = (
            db.query(SessionEvent)
            .filter(
                SessionEvent.driver_user_id == driver_id,
                SessionEvent.session_end.is_(None),
                SessionEvent.updated_at < cutoff,
            )
            .order_by(desc(SessionEvent.session_start))
            .first()
        )
        if not stale:
            return None

        logger.info(
            f"Auto-closing stale session {stale.id} for driver {driver_id} "
            f"(last updated {stale.updated_at})"
        )
        return SessionEventService.end_session(
            db, stale.id,
            ended_reason="stale_cleanup",
            battery_end_pct=stale.battery_end_pct,
            kwh_delivered=stale.kwh_delivered,
        )

    @staticmethod
    def end_session_manual(
        db: Session,
        session_event_id: str,
        driver_id: int,
    ) -> Optional[SessionEvent]:
        """
        Manually end a session (user-initiated). Verifies ownership.
        Returns the ended session or None if not found / not owned / already ended.
        """
        session = db.query(SessionEvent).filter(
            SessionEvent.id == session_event_id,
            SessionEvent.driver_user_id == driver_id,
            SessionEvent.session_end.is_(None),
        ).first()
        if not session:
            return None

        logger.info(f"Manual session end for {session.id} by driver {driver_id}")
        return SessionEventService.end_session(
            db, session.id,
            ended_reason="manual",
        )

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
