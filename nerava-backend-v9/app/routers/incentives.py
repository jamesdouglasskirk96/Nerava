# app/routers/incentives.py
from fastapi import APIRouter, Query
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from app.services.wallet import credit_wallet  # existing wallet service

router = APIRouter(prefix="/v1/incentives", tags=["incentives"])

# very simple demo policy: 5 minutes ON, 5 minutes OFF, cycling
def _current_window():
    now = datetime.now(timezone.utc)
    minute_mod = now.minute % 10
    active = minute_mod < 5
    if active:
        start = now.replace(second=0, microsecond=0) - timedelta(minutes=minute_mod)
        end   = start + timedelta(minutes=5)
        return {"active": True, "start_iso": start.isoformat(), "end_iso": end.isoformat(),
                "message": "Cheaper charging now"}
    else:
        # next ON starts when minute_mod hits 0 again
        start = now + timedelta(minutes=(10 - minute_mod))
        start = start.replace(second=0, microsecond=0)
        end   = start + timedelta(minutes=5)
        return {"active": False, "start_iso": start.isoformat(), "end_iso": end.isoformat(),
                "message": "Cheaper charging soon"}

@router.get("/window")
def window_status():
    """UI checks this to show 'Cheaper charging now' or '...in X minutes'."""
    return _current_window()

# Simple guard so we don't credit repeatedly within a short window.
_LAST_AWARD: Dict[str, datetime] = {}

@router.post("/award_off_peak")
def award(user_id: str = Query(...), cents: int = 100):
    """
    Credit a small bonus during ON window. Idempotent-ish: one award per user every 30 minutes.
    UI uses this as a fallback if /window isn't present.
    """
    w = _current_window()
    awarded = 0
    now = datetime.now(timezone.utc)
    last: Optional[datetime] = _LAST_AWARD.get(user_id)

    if w["active"] and (not last or (now - last) > timedelta(minutes=30)):
        out = credit_wallet(user_id, cents)
        _LAST_AWARD[user_id] = now
        awarded = cents
        balance = out.get("balance_cents", 0)
    else:
        balance = credit_wallet(user_id, 0).get("balance_cents", 0)  # no-op read

    return {
        "active": w["active"],
        "awarded_cents": awarded,
        "balance_cents": balance,
        "window": w,
    }
