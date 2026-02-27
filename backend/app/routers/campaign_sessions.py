"""
Campaign Sessions Router — Driver charging session endpoints.

GET /v1/charging-sessions/         — list my sessions
GET /v1/charging-sessions/active   — current active session
GET /v1/charging-sessions/reputation — energy reputation + streak
GET /v1/charging-sessions/{id}     — session details + grant info
POST /v1/charging-sessions/poll    — poll Tesla for current charging state
"""
import logging
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from typing import Optional

from ..db import get_db
from ..dependencies.domain import get_current_user
from ..models.user import User
from ..models.session_event import SessionEvent, IncentiveGrant
from ..services.session_event_service import SessionEventService

logger = logging.getLogger(__name__)


class PollSessionRequest(BaseModel):
    """Optional device location sent with each poll."""
    lat: Optional[float] = None
    lng: Optional[float] = None

router = APIRouter(prefix="/v1/charging-sessions", tags=["charging-sessions"])


@router.get("/")
async def list_sessions(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List driver's charging sessions, most recent first."""
    sessions = SessionEventService.get_driver_sessions(
        db, current_user.id, limit=limit, offset=offset
    )
    return {
        "sessions": [_session_to_dict(s, db) for s in sessions],
        "count": len(sessions),
    }


@router.get("/active")
async def get_active_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current active (un-ended) session, if any."""
    session = SessionEventService.get_active_session(db, current_user.id)
    if not session:
        return {"session": None, "active": False}
    return {
        "session": _session_to_dict(session, db),
        "active": True,
    }


@router.get("/reputation")
async def get_reputation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get driver's energy reputation tier, points, progress, and charging streak."""
    from ..models_domain import DriverWallet
    from ..services.reputation import compute_reputation

    # Get wallet with energy_reputation_score
    wallet = db.query(DriverWallet).filter(
        DriverWallet.user_id == current_user.id
    ).first()
    score = wallet.energy_reputation_score if wallet else 0
    reputation = compute_reputation(score or 0)

    # Compute streak: count consecutive days with completed sessions ending today
    streak_days = _compute_streak(db, current_user.id)
    reputation["streak_days"] = streak_days

    return reputation


def _compute_streak(db: Session, driver_id: int) -> int:
    """
    Count consecutive days with at least one completed session,
    going backwards from today. Works with both PostgreSQL and SQLite.
    """
    try:
        # Detect dialect
        dialect = db.bind.dialect.name if db.bind else "sqlite"

        if dialect == "postgresql":
            date_expr = "session_start::date"
        else:
            date_expr = "date(session_start)"

        rows = db.execute(
            text(
                f"SELECT DISTINCT {date_expr} AS d "
                "FROM session_events "
                "WHERE driver_user_id = :did AND session_end IS NOT NULL "
                f"ORDER BY {date_expr} DESC "
                "LIMIT 365"
            ),
            {"did": driver_id},
        ).fetchall()

        if not rows:
            return 0

        # Parse dates and count consecutive days backwards from today
        today = date.today()
        streak = 0
        expected = today

        for row in rows:
            d = row[0]
            if isinstance(d, str):
                d = date.fromisoformat(d)
            elif isinstance(d, datetime):
                d = d.date()

            if d == expected:
                streak += 1
                expected -= timedelta(days=1)
            elif d < expected:
                # Gap found — stop counting
                break
            # d > expected shouldn't happen with DESC ordering, skip

        return streak

    except Exception as e:
        logger.warning("Streak computation failed: %s", e)
        return 0


@router.get("/{session_id}")
async def get_session_detail(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed session info including any incentive grant earned."""
    session = db.query(SessionEvent).filter(
        SessionEvent.id == session_id,
        SessionEvent.driver_user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": _session_to_dict(session, db)}


@router.post("/{session_id}/end")
async def end_session_manual(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually end an active charging session (user-initiated)."""
    session = SessionEventService.end_session_manual(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    db.commit()
    return {"session": _session_to_dict(session, db), "ended": True}


@router.post("/poll")
async def poll_session(
    body: Optional[PollSessionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Poll Tesla API for current charging state.
    Creates/updates/ends session events as needed.
    Call every 60s while app is open.

    Optionally accepts device GPS coordinates for cross-validation
    and charger matching.
    """
    from ..models.tesla_connection import TeslaConnection
    from ..services.tesla_oauth import get_tesla_oauth_service

    tesla_conn = (
        db.query(TeslaConnection)
        .filter(
            TeslaConnection.user_id == current_user.id,
            TeslaConnection.is_active == True,
        )
        .first()
    )
    if not tesla_conn:
        return {"session_active": False, "error": "no_tesla_connection"}

    oauth_service = get_tesla_oauth_service()
    result = await SessionEventService.poll_driver_session(
        db, current_user.id, tesla_conn, oauth_service,
        device_lat=body.lat if body else None,
        device_lng=body.lng if body else None,
    )
    return result


def _session_to_dict(session: SessionEvent, db: Session) -> dict:
    """Convert session to API response dict."""
    # incentive_grants.session_event_id is varchar in production but
    # session_events.id is UUID — use raw SQL text comparison to avoid type mismatch
    grant = None
    try:
        from sqlalchemy import text
        result = db.execute(
            text("SELECT id, campaign_id, amount_cents, status, granted_at "
                 "FROM incentive_grants WHERE session_event_id = :sid LIMIT 1"),
            {"sid": str(session.id)}
        ).first()
        if result:
            grant = result
    except Exception:
        pass

    result = {
        "id": str(session.id),
        "session_start": session.session_start.isoformat() if session.session_start else None,
        "session_end": session.session_end.isoformat() if session.session_end else None,
        "duration_minutes": session.duration_minutes,
        "charger_id": session.charger_id,
        "charger_network": session.charger_network,
        "connector_type": session.connector_type,
        "power_kw": session.power_kw,
        "kwh_delivered": session.kwh_delivered,
        "verified": session.verified,
        "lat": session.lat,
        "lng": session.lng,
        "battery_start_pct": session.battery_start_pct,
        "battery_end_pct": session.battery_end_pct,
        "quality_score": session.quality_score,
        "ended_reason": session.ended_reason,
    }

    if grant:
        granted_at = grant[4]  # granted_at column
        result["incentive"] = {
            "grant_id": str(grant[0]),
            "campaign_id": str(grant[1]),
            "amount_cents": grant[2],
            "status": grant[3],
            "granted_at": granted_at.isoformat() if granted_at else None,
        }
    else:
        result["incentive"] = None

    return result
