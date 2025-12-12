"""
Wallet Pass Router

Endpoints for wallet timeline, pass status, and Apple Wallet pass management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
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
from app.services.apple_wallet_pass import create_pkpass_bundle, refresh_pkpass_bundle
import os
import logging

logger = logging.getLogger(__name__)

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


@router.post("/pass/apple/create")
def create_apple_pass(
    user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Create Apple Wallet pass for driver.
    
    Returns:
    - 200: Signed .pkpass file (if signing enabled)
    - 501: Structured error if signing disabled
    
    Eligibility:
    - Driver must have VehicleAccount (Smartcar connected)
    """
    # Check eligibility
    vehicle_account = db.query(VehicleAccount).filter(
        VehicleAccount.user_id == user.id,
        VehicleAccount.is_active == True
    ).first()
    
    if not vehicle_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "APPLE_WALLET_INELIGIBLE",
                "message": "Connect your EV first"
            }
        )
    
    # Check if signing is enabled
    signing_enabled = os.getenv("APPLE_WALLET_SIGNING_ENABLED", "false").lower() == "true"
    cert_path = os.getenv("APPLE_WALLET_CERT_PATH")
    key_path = os.getenv("APPLE_WALLET_KEY_PATH")
    
    if not signing_enabled or not cert_path or not key_path or not os.path.exists(cert_path) or not os.path.exists(key_path):
        # Return 501 structured error (Approach A)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": "APPLE_WALLET_SIGNING_DISABLED",
                "message": "Apple Wallet pass signing is not enabled on this environment."
            }
        )
    
    # Generate pass bundle
    try:
        bundle_bytes, is_signed = create_pkpass_bundle(db, user.id)
        
        if not is_signed:
            # This shouldn't happen if we checked above, but handle it
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={
                    "error": "APPLE_WALLET_SIGNING_DISABLED",
                    "message": "Apple Wallet pass signing failed."
                }
            )
        
        # Update wallet_pass_last_generated_at
        wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user.id).first()
        if wallet:
            wallet.wallet_pass_last_generated_at = datetime.utcnow()
            db.commit()
        
        # Return .pkpass file
        return Response(
            content=bundle_bytes,
            media_type="application/vnd.apple.pkpass",
            headers={
                "Content-Disposition": 'attachment; filename="nerava-wallet.pkpass"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Apple Wallet pass: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PASS_GENERATION_FAILED",
                "message": "Failed to generate Apple Wallet pass"
            }
        )


@router.post("/pass/apple/refresh")
def refresh_apple_pass(
    user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Refresh Apple Wallet pass for driver.
    
    Same as create, but updates existing pass.
    """
    # Check eligibility
    vehicle_account = db.query(VehicleAccount).filter(
        VehicleAccount.user_id == user.id,
        VehicleAccount.is_active == True
    ).first()
    
    if not vehicle_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "APPLE_WALLET_INELIGIBLE",
                "message": "Connect your EV first"
            }
        )
    
    # Check if signing is enabled
    signing_enabled = os.getenv("APPLE_WALLET_SIGNING_ENABLED", "false").lower() == "true"
    cert_path = os.getenv("APPLE_WALLET_CERT_PATH")
    key_path = os.getenv("APPLE_WALLET_KEY_PATH")
    
    if not signing_enabled or not cert_path or not key_path or not os.path.exists(cert_path) or not os.path.exists(key_path):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": "APPLE_WALLET_SIGNING_DISABLED",
                "message": "Apple Wallet pass signing is not enabled on this environment."
            }
        )
    
    # Generate refreshed pass bundle
    try:
        bundle_bytes, is_signed = refresh_pkpass_bundle(db, user.id)
        
        if not is_signed:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={
                    "error": "APPLE_WALLET_SIGNING_DISABLED",
                    "message": "Apple Wallet pass signing failed."
                }
            )
        
        # Update wallet_pass_last_generated_at
        wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user.id).first()
        if wallet:
            wallet.wallet_pass_last_generated_at = datetime.utcnow()
            db.commit()
        
        # Return .pkpass file
        return Response(
            content=bundle_bytes,
            media_type="application/vnd.apple.pkpass",
            headers={
                "Content-Disposition": 'attachment; filename="nerava-wallet.pkpass"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh Apple Wallet pass: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PASS_GENERATION_FAILED",
                "message": "Failed to refresh Apple Wallet pass"
            }
        )
