"""
Wallet Pass Router

Endpoints for wallet timeline, pass status, and Apple Wallet pass management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.db import get_db
from app.models import User
from app.models.domain import DriverWallet
from app.models.vehicle import VehicleAccount
from app.dependencies.driver import get_current_driver
from app.services.wallet_timeline import get_wallet_timeline

router = APIRouter(prefix="/v1/wallet", tags=["wallet-pass"])


class TimelineEvent(BaseModel):
    """Timeline event response model"""
    id: str
    type: str  # "EARNED" | "SPENT"
    amount_cents: int
    title: str
    subtitle: str
    created_at: str  # ISO string
    merchant_id: Optional[str] = None
    redemption_id: Optional[str] = None


class PassStatusResponse(BaseModel):
    """Pass status response"""
    wallet_activity_updated_at: Optional[str]  # ISO string or null
    wallet_pass_last_generated_at: Optional[str]  # ISO string or null
    needs_refresh: bool


class EligibilityResponse(BaseModel):
    """Apple Wallet eligibility response"""
    eligible: bool
    reason: Optional[str] = None


@router.get("/timeline", response_model=List[TimelineEvent])
def get_timeline(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Get wallet timeline (earned/spent events).
    
    Returns unified timeline of wallet activity:
    - EARNED events from NovaTransaction (driver_earn)
    - SPENT events from MerchantRedemption (excludes NovaTransaction driver_redeem to avoid duplicates)
    """
    events = get_wallet_timeline(db, driver_user_id=user.id, limit=limit)
    return events


@router.get("/pass/status", response_model=PassStatusResponse)
def get_pass_status(
    user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Get Apple Wallet pass refresh status.
    
    Returns:
    - wallet_activity_updated_at: timestamp of last wallet activity (earn/spend)
    - wallet_pass_last_generated_at: timestamp when pass was last generated
    - needs_refresh: true if activity updated after pass was generated
    
    Logic:
    - If wallet_activity_updated_at is null -> needs_refresh=false
    - If wallet_pass_last_generated_at is null AND wallet_activity_updated_at not null -> needs_refresh=true
    - Else needs_refresh = wallet_activity_updated_at > wallet_pass_last_generated_at
    """
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user.id).first()
    
    if not wallet:
        # Wallet doesn't exist yet - no activity, no pass generated
        return PassStatusResponse(
            wallet_activity_updated_at=None,
            wallet_pass_last_generated_at=None,
            needs_refresh=False
        )
    
    activity_at = wallet.wallet_activity_updated_at.isoformat() if wallet.wallet_activity_updated_at else None
    pass_at = wallet.wallet_pass_last_generated_at.isoformat() if wallet.wallet_pass_last_generated_at else None
    
    # Determine needs_refresh
    if wallet.wallet_activity_updated_at is None:
        needs_refresh = False
    elif wallet.wallet_pass_last_generated_at is None:
        needs_refresh = True
    else:
        needs_refresh = wallet.wallet_activity_updated_at > wallet.wallet_pass_last_generated_at
    
    return PassStatusResponse(
        wallet_activity_updated_at=activity_at,
        wallet_pass_last_generated_at=pass_at,
        needs_refresh=needs_refresh
    )


@router.get("/pass/apple/eligibility", response_model=EligibilityResponse)
def get_apple_wallet_eligibility(
    user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Check if driver is eligible for Apple Wallet pass.
    
    Driver is eligible only if they have VehicleAccount (Smartcar connected).
    """
    vehicle_account = db.query(VehicleAccount).filter(
        VehicleAccount.user_id == user.id,
        VehicleAccount.is_active == True
    ).first()
    
    if vehicle_account:
        return EligibilityResponse(eligible=True)
    else:
        return EligibilityResponse(
            eligible=False,
            reason="Connect your EV first"
        )
