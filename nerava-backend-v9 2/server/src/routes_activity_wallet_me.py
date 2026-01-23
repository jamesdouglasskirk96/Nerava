# server/src/routes_activity_wallet_me.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from .db import get_db
from .models import Reputation, FollowEarning, User, WalletEvent, Setting
from .deps import current_user_id

router = APIRouter(prefix="/v1")

@router.get("/activity")
def activity(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    month = int(datetime.utcnow().strftime("%Y%m"))
    rep = db.get(Reputation, user_id)
    you = db.get(User, user_id)
    q = (db.query(FollowEarning, User)
           .join(User, User.id==FollowEarning.payer_user_id, isouter=True)
           .filter(FollowEarning.month_yyyymm==month, FollowEarning.receiver_user_id==user_id)
           .all())
    earnings = [{"userId":u.id, "handle":u.handle if u else "member", "avatarUrl":u.avatar_url,
                 "tier":"Gold" if (u and u.followers>10) else "Bronze",
                 "amountCents": fe.amount_cents} for fe,u in q]
    total = sum(e["amountCents"] for e in earnings)
    return {
        "reputation":{"score": rep.score if rep else 0, "tier": rep.tier if rep else "Bronze",
                      "followers": you.followers if you else 0, "following": you.following if you else 0},
        "followEarnings": earnings, "totals":{"followCents": total}, "month": month
    }

@router.get("/wallet/debug")
def wallet_debug(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    """Debug wallet data"""
    try:
        from sqlalchemy import text
        
        result = {
            "user_id": user_id,
            "wallet_events": [],
            "payments": [],
            "rewards": []
        }
        
        # Test wallet events
        try:
            wallet_rows = db.query(WalletEvent).filter(WalletEvent.user_id==user_id).all()
            for row in wallet_rows:
                result["wallet_events"].append({
                    "id": row.id,
                    "kind": row.kind,
                    "source": row.source,
                    "amount_cents": row.amount_cents,
                    "meta": row.meta,
                    "created_at": str(row.created_at)
                })
        except Exception as e:
            result["wallet_error"] = str(e)
        
        # Test payments
        try:
            payments_result = db.execute(text("SELECT * FROM payments WHERE user_id = :user_id"), {'user_id': user_id})
            for row in payments_result:
                result["payments"].append({
                    "id": row[0],
                    "merchant_id": row[2],
                    "status": row[5],
                    "amount_cents": row[6],
                    "created_at": str(row[9])
                })
        except Exception as e:
            result["payment_error"] = str(e)
        
        # Test rewards
        try:
            rewards_result = db.execute(text("SELECT * FROM reward_events WHERE user_id = :user_id"), {'user_id': user_id})
            for row in rewards_result:
                result["rewards"].append({
                    "id": row[0],
                    "type": row[2],
                    "amount_cents": row[3],
                    "created_at": str(row[4])
                })
        except Exception as e:
            result["reward_error"] = str(e)
        
        return result
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": str(traceback.format_exc())}

@router.get("/wallet/simple")
def wallet_simple(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    """Simple wallet test"""
    try:
        from sqlalchemy import text
        
        # Just get wallet events first
        wallet_rows = db.query(WalletEvent).filter(WalletEvent.user_id==user_id).all()
        
        balance = sum(r.amount_cents if r.type=="earn" else -r.amount_cents for r in wallet_rows)
        
        breakdown = [{"title": r.title, "amountCents": r.amount_cents, "type": r.type} for r in wallet_rows[:5]]
        
        return {"balanceCents": balance, "breakdown": breakdown, "history": breakdown}
        
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/wallet/summary")
def wallet_summary(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    """Wallet summary using unified ledger"""
    try:
        # Get all wallet events for the user
        wallet_rows = db.query(WalletEvent).filter(WalletEvent.user_id==user_id).order_by(WalletEvent.created_at.desc()).all()
        
        # Calculate balance: credits minus debits
        credits = sum(row.amount_cents for row in wallet_rows if row.kind == 'credit')
        debits = sum(row.amount_cents for row in wallet_rows if row.kind == 'debit')
        balance = credits - debits
        
        # Calculate available credit (all credits)
        available_credit = credits
        
        # Calculate total spent (all debits)
        total_spent = debits
        
        # Build breakdown from wallet events
        breakdown = []
        for row in wallet_rows[:10]:  # Last 10 entries
            title = row.meta.get('title') if row.meta else f"{row.source} ({row.kind})"
            breakdown.append({
                'title': title,
                'amountCents': row.amount_cents if row.kind == 'credit' else -row.amount_cents,
                'type': row.kind,
                'source': row.source,
                'createdAt': row.created_at.isoformat() if row.created_at else None
            })
        
        return {
            "balanceCents": balance, 
            "availableCreditCents": available_credit,
            "totalSpentCents": total_spent,
            "breakdown": breakdown, 
            "history": breakdown
        }
        
    except Exception as e:
        import traceback
        print(f"Wallet summary error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"balanceCents": 0, "breakdown": [], "history": []}

@router.get("/wallet/test")
def wallet_test(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    """Minimal wallet test"""
    try:
        # Test basic query
        count = db.query(WalletEvent).count()
        return {"status": "success", "wallet_events_count": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/profile/me")
def profile_me(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    s = db.get(Setting, user_id)
    return {"handle": u.handle if u else "you", "followers": u.followers if u else 0,
            "following": u.following if u else 0,
            "settings": {"greenAlerts": bool(s.green_alerts) if s else True,
                         "perkAlerts": bool(s.perk_alerts) if s else True,
                         "vehicle": s.vehicle if s else None}
           }

@router.post("/profile/settings")
def profile_settings(payload: dict, user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    s = db.get(Setting, user_id)
    if not s:
        s = Setting(user_id=user_id)
        db.add(s)
    s.green_alerts = bool(payload.get("greenAlerts", True))
    s.perk_alerts = bool(payload.get("perkAlerts", True))
    s.vehicle = payload.get("vehicle")
    db.commit()
    return {"ok":True}
