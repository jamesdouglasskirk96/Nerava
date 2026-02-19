"""
Driver Wallet Router - Stripe Express Payouts

Endpoints for driver wallet management, balance checks, and withdrawals.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies.domain import get_current_user
from ..services.payout_service import PayoutService

router = APIRouter(prefix="/v1/wallet", tags=["wallet"])


class WithdrawRequest(BaseModel):
    amount_cents: int


class CreateAccountRequest(BaseModel):
    email: str


class AccountLinkRequest(BaseModel):
    return_url: str
    refresh_url: str


@router.get("/balance")
async def get_balance(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get driver wallet balance"""
    try:
        balance = PayoutService.get_balance(db, current_user.id)
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_wallet_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get wallet transaction history (payouts)"""
    try:
        history = PayoutService.get_payout_history(db, current_user.id, limit)
        return {"payouts": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/withdraw")
async def request_withdrawal(
    request: WithdrawRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Request a withdrawal to Stripe Express account"""
    try:
        result = PayoutService.request_withdrawal(db, current_user.id, request.amount_cents)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stripe/account")
async def create_stripe_account(
    request: CreateAccountRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create or get Stripe Express account for driver"""
    try:
        result = PayoutService.create_express_account(db, current_user.id, request.email)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stripe/account-link")
async def create_stripe_account_link(
    request: AccountLinkRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create Stripe account onboarding link"""
    try:
        result = PayoutService.create_account_link(
            db, current_user.id, request.return_url, request.refresh_url
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stripe/webhook")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events for payouts"""
    try:
        payload = await request.body()
        signature = stripe_signature or ""
        result = PayoutService.handle_webhook(db, payload, signature)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints for testing/debugging
@router.post("/admin/credit")
async def admin_credit_wallet(
    driver_id: int,
    amount_cents: int,
    reference_type: str = "bonus",
    description: str = "Admin credit",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Admin endpoint to credit a driver's wallet"""
    # Check admin role
    if not current_user.admin_role:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        import uuid
        result = PayoutService.credit_wallet(
            db, driver_id, amount_cents, reference_type, str(uuid.uuid4()), description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
