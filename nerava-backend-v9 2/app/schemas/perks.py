"""
Schemas for Perk Unlock API
"""
from pydantic import BaseModel
from typing import Optional


class PerkUnlockRequest(BaseModel):
    """Request to unlock a perk"""
    perk_id: int
    unlock_method: str  # "dwell_time" or "user_confirmation"
    intent_session_id: Optional[str] = None
    merchant_id: Optional[str] = None
    dwell_time_seconds: Optional[int] = None


class PerkUnlockResponse(BaseModel):
    """Response for unlocking a perk"""
    unlock_id: str
    perk_id: int
    unlocked_at: str  # ISO string
    message: str



