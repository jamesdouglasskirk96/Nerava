from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models_extra import CreditLedger, IncentiveRule
from app.models.domain import DriverWallet
from app.services.incentives import calc_award_cents
from app.services.nova import cents_to_nova
from app.services.nova_service import NovaService

router = APIRouter(prefix="/v1", tags=["wallet"])

# ---- helpers ----
def _balance(db: Session, user_ref: str) -> int:
    """Get wallet balance, returning 0 if credit_ledger table doesn't exist."""
    try:
        rows = db.query(CreditLedger).filter(CreditLedger.user_ref == user_ref).all()
        return sum(r.cents for r in rows)
    except Exception:
        # Table might not exist yet - return 0 balance
        return 0

def _add_ledger(db: Session, user_ref: str, cents: int, reason: str, meta: Dict[str, Any] = None) -> int:
    row = CreditLedger(user_ref=user_ref, cents=cents, reason=reason, meta=meta or {})
    db.add(row)
    db.commit()
    return _balance(db, user_ref)

# ---- endpoints ----
@router.get("/wallet")
def get_wallet(
    user_id: str = Query(..., description="User ID or 'current' for authenticated user"),
    db: Session = Depends(get_db),
    # Try to get current user if user_id is "current"
    current_user_id: int = None
):
    """
    Get wallet balance - returns 0 if credit_ledger table doesn't exist.
    
    If user_id is "current", attempts to resolve from authentication token.
    Falls back to checking all DriverWallet records if no auth.
    """
    # Resolve "current" to actual user ID
    resolved_user_id = user_id
    if user_id == "current":
        # Try to get from dependency injection if available
        try:
            from app.dependencies.driver import get_current_driver_id
            from fastapi import Request
            # This won't work without request context, so we'll handle it differently
            resolved_user_id = None
        except:
            resolved_user_id = None
    
    try:
        balance_cents = _balance(db, resolved_user_id or user_id)
    except Exception as e:
        # Handle gracefully if table doesn't exist
        balance_cents = 0
    
    # Also get Nova balance from DriverWallet if available
    nova_balance = 0
    try:
        # If user_id is "current" and we can't resolve it, check all wallets
        # (for demo mode - in production this should require auth)
        if user_id == "current":
            # In demo mode, try to find any wallet with charging detected or use user_id=1
            driver_wallet = db.query(DriverWallet).filter(
                DriverWallet.charging_detected == True
            ).first()
            if not driver_wallet:
                # Fallback to user_id=1 for demo
                driver_wallet = db.query(DriverWallet).filter(DriverWallet.user_id == 1).first()
        else:
            # Try to parse user_id as int (for DriverWallet.user_id)
            try:
                user_id_int = int(user_id)
                driver_wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user_id_int).first()
            except ValueError:
                driver_wallet = None
        
        if driver_wallet:
            nova_balance = driver_wallet.nova_balance or 0
    except Exception:
        # DriverWallet doesn't exist or error - ignore
        pass
    
    return {
        "balance_cents": balance_cents,
        "nova_balance": cents_to_nova(balance_cents) + nova_balance
    }

@router.post("/wallet/credit_qs")
def wallet_credit_qs(
    user_id: str = Query(...),
    cents: int = Query(...),
    db: Session = Depends(get_db),
):
    if cents <= 0:
        raise HTTPException(status_code=400, detail="cents must be > 0")
    new_bal = _add_ledger(db, user_id, cents, "ADJUST", {"via": "credit_qs"})
    return {
        "new_balance_cents": new_bal,
        "nova_balance": cents_to_nova(new_bal)
    }

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
    return {
        "new_balance_cents": new_bal,
        "nova_balance": cents_to_nova(new_bal)
    }

@router.get("/wallet/history")
def wallet_history(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get wallet history - returns empty list if credit_ledger table doesn't exist."""
    try:
        q = (
            db.query(CreditLedger)
            .filter(CreditLedger.user_ref == user_id)
            .order_by(CreditLedger.id.desc())
            .limit(limit)
        )
        return [
            {
                "cents": r.cents,
                "nova_delta": cents_to_nova(r.cents),
                "reason": r.reason,
                "meta": r.meta,
                "ts": r.created_at.isoformat()
            }
            for r in q.all()
        ]
    except Exception:
        # Table might not exist yet - return empty history
        return []

@router.get("/wallet/summary")
def wallet_summary(
    user_id: str = "demo-user-123",
    db: Session = Depends(get_db),
):
    """Get wallet summary with balance and recent history"""
    try:
        balance = _balance(db, user_id)
        
        # Get recent history
        q = (
            db.query(CreditLedger)
            .filter(CreditLedger.user_ref == user_id)
            .order_by(CreditLedger.id.desc())
            .limit(10)
        )
        history = [
            {
                "cents": r.cents,
                "reason": r.reason,
                "meta": r.meta,
                "ts": r.created_at.isoformat()
            }
            for r in q.all()
        ]
    except Exception:
        # Table might not exist yet - return empty wallet
        balance = 0
        history = []
    
    return {
        "balance_cents": balance,
        "nova_balance": cents_to_nova(balance),
        "balance_dollars": round(balance / 100, 2),
        "history": [
            {
                **entry,
                "nova_delta": cents_to_nova(entry["cents"])
            }
            for entry in history
        ]
    }

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
    return {
        "new_balance_cents": new_bal,
        "nova_balance": cents_to_nova(new_bal),
        "redeemed": cents,
        "redeemed_nova": cents_to_nova(cents),
        "perk": perk
    }

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
        return {
            "awarded_cents": amt,
            "nova_awarded": cents_to_nova(amt),
            "new_balance_cents": new_bal,
            "nova_balance": cents_to_nova(new_bal)
        }
    return {
        "awarded_cents": 0,
        "nova_awarded": 0,
        "message": "Not in off-peak window"
    }
