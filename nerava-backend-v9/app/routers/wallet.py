from datetime import datetime
from typing import Dict, Any, Optional
import os

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models_extra import CreditLedger, IncentiveRule
from app.models.domain import DriverWallet
from app.models import User
from app.dependencies.domain import get_current_user
from app.services.incentives import calc_award_cents
from app.services.nova import cents_to_nova
from app.services.nova_service import NovaService
from app.services.audit import log_wallet_mutation
from app.utils.log import get_logger

logger = get_logger(__name__)

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
    db: Session = Depends(get_db)
):
    """
    Get wallet balance - returns 0 if credit_ledger table doesn't exist.
    
    P0-1 Security: If user_id is "current", authentication is required in non-local environments.
    For backward compatibility, if user_id is a specific ID, the endpoint still works.
    """
    # Resolve user_id
    resolved_user_id = user_id
    
    # P0-1: If user_id is "current", require authentication in non-local
    if user_id == "current":
        import os
        env = os.getenv("ENV", "dev").lower()
        is_local = env in {"local", "dev"}
        
        if not is_local:
            # In non-local, require auth for "current"
            raise HTTPException(
                status_code=401,
                detail="Authentication required when using user_id='current' in non-local environment. Use authenticated endpoint or provide specific user_id."
            )
        else:
            # In local, fallback to demo behavior
            resolved_user_id = "1"  # Demo fallback
    
    try:
        balance_cents = _balance(db, resolved_user_id)
    except Exception as e:
        # Handle gracefully if table doesn't exist
        balance_cents = 0
    
    # Also get Nova balance from DriverWallet if available
    nova_balance = 0
    try:
        # Try to parse user_id as int (for DriverWallet.user_id)
        try:
            user_id_int = int(resolved_user_id)
            driver_wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user_id_int).first()
            if driver_wallet:
                nova_balance = driver_wallet.nova_balance or 0
        except ValueError:
            driver_wallet = None
    except Exception:
        # DriverWallet doesn't exist or error - ignore
        pass
    
    return {
        "balance_cents": balance_cents,
        "nova_balance": cents_to_nova(balance_cents) + nova_balance
    }

@router.post("/wallet/credit_qs")
def wallet_credit_qs(
    user_id: Optional[str] = Query(None, description="[DEPRECATED] User ID - ignored, uses authenticated user"),
    cents: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Credit (add) amount to authenticated user's wallet.
    
    P0-A Security: Requires authentication. user_id parameter is accepted for backward
    compatibility but ignored - uses authenticated user's ID instead.
    """
    # P0-A: Use authenticated user ID, ignore user_id parameter for security
    authenticated_user_id = str(current_user.id)
    
    # Log warning in non-prod if user_id was provided and mismatched
    if user_id is not None:
        env = os.getenv("ENV", "dev").lower()
        is_local = env in {"local", "dev"}
        if user_id != authenticated_user_id and not is_local:
            logger.warning(
                f"[P0-A] wallet_credit_qs: user_id param '{user_id}' ignored, using authenticated user {authenticated_user_id}",
                extra={
                    "endpoint": "wallet_credit_qs",
                    "provided_user_id": user_id,
                    "authenticated_user_id": authenticated_user_id,
                    "actor_user_id": authenticated_user_id
                }
            )
    
    if cents <= 0:
        raise HTTPException(status_code=400, detail="cents must be > 0")
    
    # Get balance before mutation
    before_balance = _balance(db, authenticated_user_id)
    
    new_bal = _add_ledger(db, authenticated_user_id, cents, "ADJUST", {"via": "credit_qs"})
    
    # P1-1: Admin audit log
    log_wallet_mutation(
        db=db,
        actor_id=current_user.id,
        action="wallet_credit",
        user_id=authenticated_user_id,
        before_balance=before_balance,
        after_balance=new_bal,
        amount=cents,
        metadata={"via": "credit_qs", "endpoint": "wallet_credit_qs"}
    )
    
    # Audit log
    logger.info(
        f"[AUDIT] wallet_credit_qs: user {authenticated_user_id} credited {cents} cents",
        extra={
            "endpoint": "wallet_credit_qs",
            "actor_user_id": authenticated_user_id,
            "amount_cents": cents,
            "new_balance_cents": new_bal,
            "result": "success"
        }
    )
    
    return {
        "new_balance_cents": new_bal,
        "nova_balance": cents_to_nova(new_bal)
    }

@router.post("/wallet/debit_qs")
def wallet_debit_qs(
    user_id: Optional[str] = Query(None, description="[DEPRECATED] User ID - ignored, uses authenticated user"),
    cents: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Debit (subtract) amount from authenticated user's wallet.
    
    P0-A Security: Requires authentication. user_id parameter is accepted for backward
    compatibility but ignored - uses authenticated user's ID instead.
    """
    # P0-A: Use authenticated user ID, ignore user_id parameter for security
    authenticated_user_id = str(current_user.id)
    
    # Log warning in non-prod if user_id was provided and mismatched
    if user_id is not None:
        env = os.getenv("ENV", "dev").lower()
        is_local = env in {"local", "dev"}
        if user_id != authenticated_user_id and not is_local:
            logger.warning(
                f"[P0-A] wallet_debit_qs: user_id param '{user_id}' ignored, using authenticated user {authenticated_user_id}",
                extra={
                    "endpoint": "wallet_debit_qs",
                    "provided_user_id": user_id,
                    "authenticated_user_id": authenticated_user_id,
                    "actor_user_id": authenticated_user_id
                }
            )
    
    if cents <= 0:
        raise HTTPException(status_code=400, detail="cents must be > 0")
    
    bal = _balance(db, authenticated_user_id)
    if bal < cents:
        # Audit log for failed debit
        logger.warning(
            f"[AUDIT] wallet_debit_qs: user {authenticated_user_id} insufficient funds (has {bal}, needs {cents})",
            extra={
                "endpoint": "wallet_debit_qs",
                "actor_user_id": authenticated_user_id,
                "amount_cents": cents,
                "balance_cents": bal,
                "result": "insufficient_funds"
            }
        )
        raise HTTPException(status_code=400, detail="insufficient_funds")
    
    # Get balance before mutation
    before_balance = bal
    
    new_bal = _add_ledger(db, authenticated_user_id, -cents, "ADJUST", {"via": "debit_qs"})
    
    # P1-1: Admin audit log
    log_wallet_mutation(
        db=db,
        actor_id=current_user.id,
        action="wallet_debit",
        user_id=authenticated_user_id,
        before_balance=before_balance,
        after_balance=new_bal,
        amount=-cents,
        metadata={"via": "debit_qs", "endpoint": "wallet_debit_qs"}
    )
    
    # Audit log
    logger.info(
        f"[AUDIT] wallet_debit_qs: user {authenticated_user_id} debited {cents} cents",
        extra={
            "endpoint": "wallet_debit_qs",
            "actor_user_id": authenticated_user_id,
            "amount_cents": cents,
            "new_balance_cents": new_bal,
            "result": "success"
        }
    )
    
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
    user_id: Optional[str] = None  # [DEPRECATED] - ignored, uses authenticated user
    cents: int
    perk: str

@router.post("/wallet/redeem")
def wallet_redeem(
    req: RedeemReq,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Redeem perk from authenticated user's wallet.
    
    P0-A Security: Requires authentication. user_id field in request body is accepted
    for backward compatibility but ignored - uses authenticated user's ID instead.
    """
    # P0-A: Use authenticated user ID, ignore user_id in request body for security
    authenticated_user_id = str(current_user.id)
    
    # Log warning in non-prod if user_id was provided and mismatched
    if req.user_id is not None:
        env = os.getenv("ENV", "dev").lower()
        is_local = env in {"local", "dev"}
        if req.user_id != authenticated_user_id and not is_local:
            logger.warning(
                f"[P0-A] wallet_redeem: user_id field '{req.user_id}' ignored, using authenticated user {authenticated_user_id}",
                extra={
                    "endpoint": "wallet_redeem",
                    "provided_user_id": req.user_id,
                    "authenticated_user_id": authenticated_user_id,
                    "actor_user_id": authenticated_user_id
                }
            )
    
    cents = int(req.cents)
    perk = req.perk
    if cents <= 0:
        raise HTTPException(status_code=400, detail="invalid_request")
    
    bal = _balance(db, authenticated_user_id)
    if bal < cents:
        # Audit log for failed redeem
        logger.warning(
            f"[AUDIT] wallet_redeem: user {authenticated_user_id} insufficient funds (has {bal}, needs {cents}) for perk '{perk}'",
            extra={
                "endpoint": "wallet_redeem",
                "actor_user_id": authenticated_user_id,
                "amount_cents": cents,
                "balance_cents": bal,
                "perk": perk,
                "result": "insufficient_funds"
            }
        )
        raise HTTPException(status_code=400, detail="insufficient_funds")
    
    # Get balance before mutation
    before_balance = bal
    
    new_bal = _add_ledger(db, authenticated_user_id, -cents, "REDEEM", {"perk": perk})
    
    # P1-1: Admin audit log
    log_wallet_mutation(
        db=db,
        actor_id=current_user.id,
        action="wallet_redeem",
        user_id=authenticated_user_id,
        before_balance=before_balance,
        after_balance=new_bal,
        amount=-cents,
        metadata={"perk": perk, "endpoint": "wallet_redeem"}
    )
    
    # Audit log
    logger.info(
        f"[AUDIT] wallet_redeem: user {authenticated_user_id} redeemed {cents} cents for perk '{perk}'",
        extra={
            "endpoint": "wallet_redeem",
            "actor_user_id": authenticated_user_id,
            "amount_cents": cents,
            "new_balance_cents": new_bal,
            "perk": perk,
            "result": "success"
        }
    )
    
    return {
        "new_balance_cents": new_bal,
        "nova_balance": cents_to_nova(new_bal),
        "redeemed": cents,
        "redeemed_nova": cents_to_nova(cents),
        "perk": perk
    }

@router.post("/incentives/award_off_peak")
def award_off_peak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Award off-peak incentive to authenticated user's wallet.
    
    P0-1 Security: Requires authentication. Uses authenticated user's ID.
    """
    # P0-1: Use authenticated user ID
    authenticated_user_id = str(current_user.id)
    
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
        # Get balance before mutation
        before_balance = _balance(db, authenticated_user_id)
        
        new_bal = _add_ledger(db, authenticated_user_id, amt, "OFF_PEAK_AWARD", {"rule": "OFF_PEAK_BASE"})
        
        # P1-1: Admin audit log
        log_wallet_mutation(
            db=db,
            actor_id=current_user.id,
            action="wallet_credit",
            user_id=authenticated_user_id,
            before_balance=before_balance,
            after_balance=new_bal,
            amount=amt,
            metadata={"rule": "OFF_PEAK_BASE", "endpoint": "award_off_peak"}
        )
        db.commit()  # Commit audit log
        
        # Audit log
        logger.info(
            f"[AUDIT] award_off_peak: user {authenticated_user_id} awarded {amt} cents",
            extra={
                "endpoint": "award_off_peak",
                "actor_user_id": authenticated_user_id,
                "amount_cents": amt,
                "new_balance_cents": new_bal,
                "result": "success"
            }
        )
        
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
