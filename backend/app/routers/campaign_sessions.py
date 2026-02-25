"""
Campaign Sessions Router — Driver charging session endpoints.

GET /v1/charging-sessions/         — list my sessions
GET /v1/charging-sessions/active   — current active session
GET /v1/charging-sessions/{id}     — session details + grant info
POST /v1/charging-sessions/poll    — poll Tesla for current charging state
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..db import get_db
from ..dependencies.domain import get_current_user
from ..models.user import User
from ..models.session_event import SessionEvent, IncentiveGrant
from ..services.session_event_service import SessionEventService

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


@router.post("/poll")
async def poll_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Poll Tesla API for current charging state.
    Creates/updates/ends session events as needed.
    Call every 60s while app is open.
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
    result = SessionEventService.poll_driver_session(
        db, current_user.id, tesla_conn, oauth_service
    )
    return result


def _session_to_dict(session: SessionEvent, db: Session) -> dict:
    """Convert session to API response dict."""
    grant = db.query(IncentiveGrant).filter(
        IncentiveGrant.session_event_id == session.id
    ).first()

    result = {
        "id": session.id,
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
        result["incentive"] = {
            "grant_id": grant.id,
            "campaign_id": grant.campaign_id,
            "amount_cents": grant.amount_cents,
            "status": grant.status,
            "granted_at": grant.granted_at.isoformat() if grant.granted_at else None,
        }
    else:
        result["incentive"] = None

    return result
