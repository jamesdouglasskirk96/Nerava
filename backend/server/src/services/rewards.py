import uuid
from sqlalchemy import text
from ..config import Config
from ..models import WalletEvent, MerchantBalance
from ..utils.jsons import to_json

def user_daily_credited_cents(db, user_id: str):
    """Get total credits issued to user today"""
    row = db.execute(text("""
        SELECT COALESCE(SUM(amount_cents), 0) AS s
        FROM wallet_events
        WHERE user_id = :uid 
          AND kind = 'credit'
          AND DATE(created_at) = DATE('now')
    """), {"uid": user_id}).first()
    return int(row.s or 0)

def credit_once_by_payment(db, user_id, amount_cents, payment_id, session_id, pos_event_id, merchant_id):
    """Create wallet event with idempotency via unique index on meta.payment_id"""
    ev = WalletEvent(
        id=str(uuid.uuid4()),
        user_id=user_id,
        kind="credit",
        source="merchant_reward",
        amount_cents=amount_cents,
        meta=to_json({
            "payment_id": payment_id,
            "session_id": session_id,
            "pos_event_id": pos_event_id,
            "merchant_id": merchant_id
        })
    )
    db.add(ev)
    db.commit()
    return ev.id

def issue_reward_atomic(db, cfg: Config, *, user_id, session_id, pos_event_id, merchant_id, pos_amount_cents: int):
    """
    Issue reward atomically with daily cap and idempotency checks.
    Returns dict with ok, reason, wallet_event_id, user_cents
    """
    # Check daily cap
    user_cap_used = user_daily_credited_cents(db, user_id)
    if user_cap_used >= cfg.DAILY_REWARD_CAP_CENTS:
        return {"ok": False, "reason": "daily_cap_reached"}
    
    # Calculate reward (20% of POS amount)
    user_share = max(0, int(round(pos_amount_cents * 0.20)))
    grant = min(user_share, cfg.DAILY_REWARD_CAP_CENTS - user_cap_used)
    
    if grant <= 0:
        return {"ok": False, "reason": "no_remaining_cap"}
    
    try:
        # Credit wallet (idempotent via unique index)
        wallet_event_id = credit_once_by_payment(
            db,
            user_id=user_id,
            amount_cents=grant,
            payment_id=pos_event_id,
            session_id=session_id,
            pos_event_id=pos_event_id,
            merchant_id=merchant_id
        )
        
        # Update merchant balance
        row = db.execute(text("SELECT pending_cents FROM merchant_balances WHERE merchant_id = :m"), 
                         {"m": merchant_id}).first()
        if row is None:
            db.execute(text("INSERT INTO merchant_balances(merchant_id, pending_cents, paid_cents) VALUES (:m, :p, 0)"),
                       {"m": merchant_id, "p": grant})
        else:
            db.execute(text("UPDATE merchant_balances SET pending_cents = pending_cents + :p WHERE merchant_id = :m"),
                       {"m": merchant_id, "p": grant})
        db.commit()
        
        return {"ok": True, "wallet_event_id": wallet_event_id, "user_cents": grant}
    
    except Exception as e:
        db.rollback()
        # Check if it's a duplicate key error (idempotency)
        if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
            return {"ok": False, "reason": "already_credited"}
        return {"ok": False, "reason": f"error: {str(e)}"}
