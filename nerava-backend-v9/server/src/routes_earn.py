# server/src/routes_earn.py
from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4
from sqlalchemy.orm import Session
from .db import get_db
from .models import ChargeIntent
from .deps import current_user_id

router = APIRouter(prefix="/v1/intent")

@router.post("")
def save_intent(payload: dict, user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    # expected: station_id, station_name, merchant, address, window_text, distance_text
    intent = ChargeIntent(
        id=str(uuid4()), user_id=user_id,
        station_id=payload.get("station_id"), station_name=payload.get("station_name"),
        merchant=payload.get("merchant"), address=payload.get("address"),
        window_text=payload.get("window_text"), distance_text=payload.get("distance_text"),
    )
    db.add(intent); db.commit()
    return {"ok": True, "id": intent.id}

@router.get("")
def list_intents(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    rows = db.query(ChargeIntent).filter(ChargeIntent.user_id==user_id).order_by(ChargeIntent.created_at.desc()).all()
    return [{"id":r.id,"status":r.status,"title":r.station_name or r.merchant or r.station_id,
             "subtitle":f"{r.merchant or ''} • {r.address or ''}".strip(" •"),
             "window_text": r.window_text, "distance_text": r.distance_text} for r in rows]

@router.post("/{intent_id}/start")
def start_intent(intent_id: str, user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    r = db.get(ChargeIntent, intent_id)
    if not r or r.user_id!=user_id: raise HTTPException(404)
    r.status="started"; db.commit()
    return {"ok":True}

@router.post("/{intent_id}/notify")
def notify_intent(intent_id: str, user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    r = db.get(ChargeIntent, intent_id)
    if not r or r.user_id!=user_id: raise HTTPException(404)
    r.status="notified"; db.commit()
    return {"ok":True}
