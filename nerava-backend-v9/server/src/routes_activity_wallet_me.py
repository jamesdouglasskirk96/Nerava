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

@router.get("/wallet/summary")
def wallet_summary(user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    """Simplified wallet summary"""
    try:
        # Get wallet events
        wallet_rows = db.query(WalletEvent).filter(WalletEvent.user_id==user_id).order_by(WalletEvent.created_at.desc()).all()
        
        # Calculate balance from wallet events only
        balance = sum(r.amount_cents if r.type=="earn" else -r.amount_cents for r in wallet_rows)
        
        # Simple breakdown
        breakdown = [ {"title":r.title, "amountCents": r.amount_cents, "type": r.type} for r in wallet_rows[:5] ]
        
        return {"balanceCents": balance, "breakdown": breakdown, "history": breakdown}
        
    except Exception as e:
        print(f"Wallet summary error: {e}")
        import traceback
        traceback.print_exc()
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
