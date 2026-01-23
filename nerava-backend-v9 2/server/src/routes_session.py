from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import uuid
from sqlalchemy.orm import Session as DBSession
from .deps import get_db, current_user_id
from .models import Session as MSession
from .services.telemetry import maybe_mark_medium_confidence

router = APIRouter(prefix="/v1/session", tags=["session"])

@router.post("/start")
def start_session(payload: dict, db: DBSession = Depends(get_db), user_id: str = Depends(current_user_id)):
    """Start a new charging session"""
    sid = str(uuid.uuid4())
    s = MSession(
        id=sid,
        user_id=user_id,
        t0=datetime.utcnow(),
        station_id_guess=payload.get("station_id_guess"),
        start_lat=payload.get("lat"),
        start_lng=payload.get("lng"),
        confidence="NONE"
    )
    db.add(s)
    db.commit()
    return {"id": sid, "t0": s.t0.isoformat()}

@router.post("/end")
def end_session(payload: dict, db: DBSession = Depends(get_db), user_id: str = Depends(current_user_id)):
    """End an active charging session"""
    sid = payload.get("session_id")
    if not sid:
        raise HTTPException(status_code=400, detail="session_id required")
    
    s = db.query(MSession).filter(MSession.id == sid, MSession.user_id == user_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    
    s.end_at = datetime.utcnow()
    s.last_lat = payload.get("lat")
    s.last_lng = payload.get("lng")
    db.commit()
    
    # Mark medium confidence if not already verified
    maybe_mark_medium_confidence(db, s)
    
    return {"ok": True, "session_id": sid}

@router.get("/active")
def active_session(db: DBSession = Depends(get_db), user_id: str = Depends(current_user_id)):
    """Get the most recent session for the user"""
    s = db.query(MSession).filter(MSession.user_id == user_id).order_by(MSession.t0.desc()).first()
    if not s:
        return {"active": False}
    
    return {
        "active": True,
        "session_id": s.id,
        "t0": s.t0.isoformat(),
        "verified_charge": s.verified_charge,
        "confidence": s.confidence
    }
