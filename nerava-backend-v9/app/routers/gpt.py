from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/v1/gpt", tags=["gpt"])

@router.get("/find_charger")
def find_charger(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_m: Optional[int] = Query(500, ge=0, le=10000)
):
    """Find nearby chargers (stub - returns empty array for now)"""
    return []

@router.get("/find_merchants")
def find_merchants(
    lat: float = Query(...),
    lng: float = Query(...),
    category: Optional[str] = Query(None),
    radius_m: Optional[int] = Query(1200, ge=0, le=10000)
):
    """Find nearby merchants (stub - returns empty array for now)"""
    return []

@router.post("/create_session_link")
def create_session_link():
    """Create a session link (stub)"""
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    return {
        "session_id": session_id,
        "url": f"https://nerava.app/session/{session_id}",
        "expires_at": expires_at.isoformat()
    }

@router.get("/me")
def get_me():
    """Get current user summary (stub)"""
    return {
        "id": 1,
        "handle": "james",
        "email": "james@example.com",
        "balance_cents": 0,
        "followers_count": 0,
        "following_count": 0
    }

@router.post("/follow")
def follow(user_id: int):
    """Follow a user (stub)"""
    return {"ok": True}

@router.post("/unfollow")
def unfollow(user_id: int):
    """Unfollow a user (stub)"""
    return {"ok": True}

@router.post("/redeem")
def redeem(intent_id: str):
    """Redeem an intent (log only)"""
    # Log the redemption attempt
    print(f"[LOG] Redeem attempt for intent_id={intent_id}")
    return {"ok": True, "message": "Redemption logged"}

