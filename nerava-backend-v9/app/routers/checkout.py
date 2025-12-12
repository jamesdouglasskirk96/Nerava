"""
Checkout Router - QR-based and discovery-based Nova redemption
Handles driver checkout flow at merchants.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime
import logging

from ..db import get_db
from ..models import User
from ..models.domain import DomainMerchant, DriverWallet, MerchantRedemption
from ..services.qr_service import resolve_qr_token as resolve_merchant_qr_token
from ..services.nova_service import NovaService
from ..services.wallet_activity import mark_wallet_activity
from ..dependencies_driver import get_current_driver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/checkout", tags=["checkout"])


class CheckoutQrResponse(BaseModel):
    """Response for QR checkout lookup"""
    merchant: dict
    driver: dict


class RedeemRequest(BaseModel):
    """Request to redeem Nova at checkout"""
    qr_token: str
    order_total_cents: int


class RedeemResponse(BaseModel):
    """Response from Nova redemption"""
    success: bool
    merchant_id: str
    discount_cents: int
    order_total_cents: int
    nova_spent_cents: int
    remaining_nova_cents: int
    message: str


@router.get("/qr/{token}", response_model=CheckoutQrResponse)
async def checkout_qr(
    token: str,
    user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Look up merchant info and driver balance via QR token.
    
    This endpoint is called when a driver scans a merchant QR code.
    It returns merchant info (name, perk) and driver Nova balance.
    
    Args:
        token: QR token from merchant sign
        user: Authenticated driver (from get_current_driver)
        
    Returns:
        CheckoutQrResponse with merchant and driver info
    """
    # Resolve QR token to merchant
    merchant = resolve_merchant_qr_token(db, token)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "INVALID_QR_TOKEN",
                "message": "QR token not found or merchant not active"
            }
        )
    
    # Get driver wallet balance
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user.id).first()
    nova_balance = wallet.nova_balance if wallet else 0
    
    # Determine perk amount (use custom if set, otherwise recommended)
    perk_cents = merchant.custom_perk_cents or merchant.recommended_perk_cents or 0
    
    return CheckoutQrResponse(
        merchant={
            "id": merchant.id,
            "name": merchant.name,
            "perk_label": merchant.perk_label or f"${perk_cents / 100:.2f} off any order",
            "recommended_perk_cents": perk_cents
        },
        driver={
            "connected": True,
            "nova_balance_cents": nova_balance
        }
    )


@router.post("/redeem", response_model=RedeemResponse)
async def redeem_nova(
    request: RedeemRequest,
    user: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Redeem Nova at merchant checkout.
    
    This endpoint:
    1. Resolves merchant via QR token
    2. Calculates discount amount
    3. Validates driver has sufficient Nova
    4. Debits Nova from driver wallet
    5. Creates MerchantRedemption record
    
    Note: The merchant applies the discount manually in Square POS.
    This endpoint just handles the Nova redemption side.
    
    Args:
        request: RedeemRequest with qr_token and order_total_cents
        user: Authenticated driver
        
    Returns:
        RedeemResponse with redemption details
    """
    # Validate order_total_cents
    if request.order_total_cents <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_ORDER_TOTAL",
                "message": "Order total must be greater than zero"
            }
        )
    
    # Resolve merchant
    merchant = resolve_merchant_qr_token(db, request.qr_token)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "INVALID_QR_TOKEN",
                "message": "QR token not found or merchant not active"
            }
        )
    
    # Determine discount amount
    perk_cents = merchant.custom_perk_cents or merchant.recommended_perk_cents or 0
    discount_cents = min(perk_cents, request.order_total_cents)
    
    if discount_cents <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "NO_DISCOUNT_AVAILABLE",
                "message": "No discount available for this merchant"
            }
        )
    
    # Check driver Nova balance
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user.id).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "WALLET_NOT_FOUND",
                "message": "Driver wallet not found"
            }
        )
    
    if wallet.nova_balance < discount_cents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INSUFFICIENT_NOVA",
                "message": f"Insufficient Nova balance. Has {wallet.nova_balance}, needs {discount_cents}"
            }
        )
    
    # Redeem Nova via NovaService
    try:
        result = NovaService.redeem_from_driver(
            db=db,
            driver_id=user.id,
            merchant_id=merchant.id,
            amount=discount_cents,
            metadata={
                "qr_token": request.qr_token,
                "order_total_cents": request.order_total_cents,
                "checkout_type": "qr"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "REDEMPTION_FAILED",
                "message": str(e)
            }
        )
    
    # Create MerchantRedemption record
    redemption_id = str(uuid.uuid4())
    redemption = MerchantRedemption(
        id=redemption_id,
        merchant_id=merchant.id,
        driver_user_id=user.id,
        qr_token=request.qr_token,
        order_total_cents=request.order_total_cents,
        discount_cents=discount_cents,
        nova_spent_cents=discount_cents
    )
    db.add(redemption)
    db.commit()
    db.refresh(redemption)
    
    # Mark wallet activity for pass refresh
    mark_wallet_activity(db, user.id)
    db.commit()
    
    logger.info(
        f"Redemption: driver {user.id} redeemed {discount_cents} Nova at merchant {merchant.id}, "
        f"order total: ${request.order_total_cents / 100:.2f}"
    )
    
    return RedeemResponse(
        success=True,
        merchant_id=merchant.id,
        discount_cents=discount_cents,
        order_total_cents=request.order_total_cents,
        nova_spent_cents=discount_cents,
        remaining_nova_cents=result["driver_balance"],
        message="Nova applied. Show this screen to the merchant so they can add the discount in Square."
    )

