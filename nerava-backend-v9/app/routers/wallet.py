from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models_extra import CreditLedger, IncentiveRule
from app.services.incentives import calc_award_cents

router = APIRouter(prefix="/v1", tags=["wallet"])

# ---- helpers ----
def _balance(db: Session, user_ref: str) -> int:
    rows = db.query(CreditLedger).filter(CreditLedger.user_ref == user_ref).all()
    return sum(r.cents for r in rows)

def _add_ledger(db: Session, user_ref: str, cents: int, reason: str, meta: Dict[str, Any] = None) -> int:
    row = CreditLedger(user_ref=user_ref, cents=cents, reason=reason, meta=meta or {})
    db.add(row)
    db.commit()
    return _balance(db, user_ref)

# ---- endpoints ----
@router.get("/wallet")
def get_wallet(user_id: str, db: Session = Depends(get_db)):
    return {"balance_cents": _balance(db, user_id)}

@router.post("/wallet/credit_qs")
def wallet_credit_qs(
    user_id: str = Query(...),
    cents: int = Query(...),
    db: Session = Depends(get_db),
):
    if cents <= 0:
        raise HTTPException(status_code=400, detail="cents must be > 0")
    new_bal = _add_ledger(db, user_id, cents, "ADJUST", {"via": "credit_qs"})
    return {"new_balance_cents": new_bal}

@router.post("/wallet/debit_qs")
def wallet_debit_qs(
    user_id: str = Query(...),
    cents: int = Query(...),
    db: Session = Depends(get_db),
):
    if cents <= 0:
        raise HTTPException(status_code=400, detail="cents must be > 0")
    bal = _balance(db, user_id)
    if bal < cents:
        raise HTTPException(status_code=400, detail="insufficient_funds")
    new_bal = _add_ledger(db, user_id, -cents, "ADJUST", {"via": "debit_qs"})
    return {"new_balance_cents": new_bal}

@router.get("/wallet/history")
def wallet_history(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = (
        db.query(CreditLedger)
        .filter(CreditLedger.user_ref == user_id)
        .order_by(CreditLedger.id.desc())
        .limit(limit)
    )
    return [
        {"cents": r.cents, "reason": r.reason, "meta": r.meta, "ts": r.created_at.isoformat()}
        for r in q.all()
    ]

class RedeemReq(BaseModel):
    user_id: str
    cents: int
    perk: str

@router.post("/wallet/redeem")
def wallet_redeem(req: RedeemReq, db: Session = Depends(get_db)):
    user_id = req.user_id
    cents = int(req.cents)
    perk = req.perk
    if cents <= 0:
        raise HTTPException(status_code=400, detail="invalid_request")
    bal = _balance(db, user_id)
    if bal < cents:
        raise HTTPException(status_code=400, detail="insufficient_funds")
    new_bal = _add_ledger(db, user_id, -cents, "REDEEM", {"perk": perk})
    return {"new_balance_cents": new_bal, "redeemed": cents, "perk": perk}

@router.post("/incentives/award_off_peak")
def award_off_peak(user_id: str, db: Session = Depends(get_db)):
    # ensure default rule exists
    rule = db.query(IncentiveRule).filter(IncentiveRule.code == "OFF_PEAK_BASE").first()
    if not rule:
        rule = IncentiveRule(code="OFF_PEAK_BASE", active=True, params={"cents": 25, "window": ["22:00", "06:00"]})
        db.add(rule)
        db.commit()

    rules = db.query(IncentiveRule).all()
    rules_dicts = [{"code": r.code, "active": r.active, "params": r.params or {}} for r in rules]
    amt = calc_award_cents(datetime.utcnow(), rules_dicts)
    if amt > 0:
        new_bal = _add_ledger(db, user_id, amt, "OFF_PEAK_AWARD", {"rule": "OFF_PEAK_BASE"})
        return {"awarded_cents": amt, "new_balance_cents": new_bal}
    return {"awarded_cents": 0, "message": "Not in off-peak window"}
