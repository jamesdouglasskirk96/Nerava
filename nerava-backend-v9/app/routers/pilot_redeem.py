"""
Pilot Code Redemption Router

Handles redemption of merchant discount codes and balance deduction.
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db
from app.models import User
from app.dependencies_domain import get_current_user
from app.services.codes import fetch_code, is_code_valid
from app.services.merchant_balance import debit_balance
from app.services.rewards_engine import record_reward_event
from app.models_while_you_charge import MerchantOfferCode
from app.utils.log import get_logger

router = APIRouter(prefix="/v1/pilot", tags=["pilot-redeem"])
logger = get_logger(__name__)


class RedeemCodeRequest(BaseModel):
    """Request model for code redemption"""
    code: str = Field(..., min_length=1, description="Redemption code")
    merchant_id: str = Field(..., description="Merchant ID (must match code)")


class RedeemCodeResponse(BaseModel):
    """Response model for code redemption"""
    success: bool
    redeemed_cents: int
    balance_after: int
    code: str
    merchant_id: str


@router.post("/redeem_code", response_model=RedeemCodeResponse)
def redeem_code(
    request: RedeemCodeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Redeem a discount code and deduct from merchant balance.
    
    Validates:
    - Code exists
    - Code matches merchant_id
    - Code is not expired
    - Code is not already redeemed
    
    Actions:
    - Debits merchant balance
    - Marks code as redeemed
    - Creates RewardEvent for reporting
    
    Auth: Requires authentication (P0-3: security hardening)
    """
    try:
        # Fetch the code with row lock (P0 race condition fix)
        # Use SELECT ... FOR UPDATE to prevent concurrent redemption
        from sqlalchemy import text
        from app.models_while_you_charge import MerchantOfferCode
        
        # Lock the row for update to prevent race conditions
        offer_code = db.query(MerchantOfferCode).filter(
            MerchantOfferCode.code == request.code
        ).with_for_update().first()
        
        if not offer_code:
            raise HTTPException(status_code=404, detail=f"Code {request.code} not found")
        
        # Validate merchant_id matches
        if offer_code.merchant_id != request.merchant_id:
            raise HTTPException(
                status_code=403,
                detail=f"Code {request.code} does not belong to merchant {request.merchant_id}"
            )
        
        # Validate code is not already redeemed (now safe due to row lock)
        if offer_code.is_redeemed:
            raise HTTPException(
                status_code=400,
                detail=f"Code {request.code} has already been redeemed"
            )
        
        # Validate code is not expired
        if not is_code_valid(offer_code):
            if offer_code.expires_at and offer_code.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=400,
                    detail=f"Code {request.code} has expired"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Code {request.code} is not valid"
                )
        
        # Debit merchant balance
        try:
            updated_balance = debit_balance(
                db=db,
                merchant_id=request.merchant_id,
                amount_cents=offer_code.amount_cents,
                reason=f"code_redemption:{offer_code.code}",
                session_id=None  # Could add session_id if available
            )
        except ValueError as e:
            # Insufficient balance or other validation error
            raise HTTPException(status_code=400, detail=str(e))
        
        # Mark code as redeemed (atomic within locked transaction)
        offer_code.is_redeemed = True
        offer_code.redeemed_at = datetime.utcnow()  # Set redemption timestamp if column exists
        db.commit()
        db.refresh(offer_code)
        
        # Create RewardEvent for reporting
        # Using merchant_id as user_id for merchant activity tracking
        try:
            record_reward_event(
                db=db,
                user_id=f"merchant:{request.merchant_id}",  # Prefix to distinguish merchant activities
                source="MERCHANT_CODE_REDEMPTION",
                gross_cents=offer_code.amount_cents,
                meta={
                    "code": offer_code.code,
                    "merchant_id": request.merchant_id,
                    "redemption_type": "discount_code",
                    "code_id": offer_code.id
                }
            )
        except Exception as e:
            # Log error but don't fail the redemption if RewardEvent creation fails
            logger.warning(f"Failed to create RewardEvent for code redemption: {str(e)}")
        
        logger.info(
            f"Code {request.code} redeemed by merchant {request.merchant_id}. "
            f"Amount: {offer_code.amount_cents} cents, New balance: {updated_balance.balance_cents}"
        )
        
        return RedeemCodeResponse(
            success=True,
            redeemed_cents=offer_code.amount_cents,
            balance_after=updated_balance.balance_cents,
            code=offer_code.code,
            merchant_id=request.merchant_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to redeem code {request.code}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to redeem code: {str(e)}")

