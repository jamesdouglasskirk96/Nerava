from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
import uuid
import json
from .deps import get_db, current_user_id
from .models import Session as MSession, POSEvent
from .config import Config
from .services.telemetry import mark_verified_charge
from .services.correlation import approved
from .services.rewards import issue_reward_atomic

router = APIRouter(prefix="/v1/dev", tags=["dev"])

@router.post("/telemetry/mock")
def dev_mock_telemetry(payload: dict, db: DBSession = Depends(get_db), user_id: str = Depends(current_user_id)):
    """Mock telemetry event to mark session as verified"""
    sid = payload.get("session_id")
    if not sid:
        raise HTTPException(status_code=400, detail="session_id required")
    
    s = db.query(MSession).filter(MSession.id == sid, MSession.user_id == user_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    
    mark_verified_charge(db, s, kwh=3.0, start_at=s.t0, end_at=datetime.utcnow(), confidence="HIGH")
    return {"ok": True, "session_id": s.id, "verified_charge": True, "confidence": "HIGH"}

@router.post("/square/mock-payment")
def dev_mock_payment(payload: dict, db: DBSession = Depends(get_db), user_id: str = Depends(current_user_id)):
    """Mock Square payment event and auto-correlate with latest session"""
    cfg = Config()
    amount_cents = int(payload.get("amount_cents", 500))
    merchant_id = payload.get("merchant_id", "merchant-dev")
    event_id = str(uuid.uuid4())
    t_event = datetime.utcnow()
    
    # Create POS event
    pos = POSEvent(
        id=f"square:{event_id}",
        user_id=user_id,
        merchant_id=merchant_id,
        provider="square",
        event_type="payment.updated",
        event_id=event_id,
        order_id="dev",
        amount_cents=amount_cents,
        t_event=t_event,
        raw_json=json.dumps({"dev": True, "amount": amount_cents})
    )
    db.add(pos)
    db.commit()
    
    # Correlate with latest session
    s = db.query(MSession).filter(MSession.user_id == user_id).order_by(MSession.t0.desc()).first()
    if not s:
        return {"ok": True, "note": "no_session", "pos_event_id": pos.id}
    
    ok, score, reason = approved(s, pos, cfg)
    if not ok:
        return {"ok": True, "approved": False, "score": score, "reason": reason, "pos_event_id": pos.id}
    
    # Issue reward
    res = issue_reward_atomic(
        db, cfg,
        user_id=s.user_id,
        session_id=s.id,
        pos_event_id=pos.id,
        merchant_id=merchant_id,
        pos_amount_cents=amount_cents
    )
    
    return {
        "ok": True,
        "approved": True,
        "score": score,
        "reward": res,
        "pos_event_id": pos.id
    }
