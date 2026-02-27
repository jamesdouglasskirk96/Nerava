"""
Driver Wallet Router - Stripe Express Payouts

Endpoints for driver wallet management, balance checks, and withdrawals.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies.domain import get_current_user
from ..services.payout_service import PayoutService
from ..models.driver_wallet import WalletLedger, DriverWallet
from ..models.session_event import IncentiveGrant
from ..models.campaign import Campaign

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/wallet", tags=["wallet"])


class WithdrawRequest(BaseModel):
    amount_cents: int = Field(gt=0, le=10000000)


class CreateAccountRequest(BaseModel):
    email: str = ""


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
        logger.exception("Failed to get wallet balance for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to retrieve wallet balance")


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
        logger.exception("Failed to get payout history for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to retrieve payout history")


@router.get("/ledger")
async def get_wallet_ledger(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get wallet ledger entries with campaign attribution."""
    entries = (
        db.query(WalletLedger)
        .filter(WalletLedger.driver_id == current_user.id)
        .order_by(WalletLedger.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for e in entries:
        campaign_name = None
        sponsor_name = None
        if e.reference_type == "campaign_grant" and e.reference_id:
            grant = db.query(IncentiveGrant).filter(IncentiveGrant.id == e.reference_id).first()
            if grant and grant.campaign_id:
                campaign = db.query(Campaign).filter(Campaign.id == grant.campaign_id).first()
                if campaign:
                    campaign_name = campaign.name
                    sponsor_name = campaign.sponsor_name

        results.append({
            "id": e.id,
            "amount_cents": e.amount_cents,
            "balance_after_cents": e.balance_after_cents,
            "transaction_type": e.transaction_type,
            "description": e.description,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "campaign_name": campaign_name,
            "sponsor_name": sponsor_name,
        })

    return {"entries": results, "count": len(results)}


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
        logger.exception("Withdrawal failed for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Withdrawal request failed")


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
        logger.exception("Stripe account creation failed for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to create payout account")


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
        logger.exception("Stripe account link creation failed for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to create onboarding link")


@router.post("/stripe/webhook")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events for payouts"""
    import os
    if os.getenv("ENV", "dev") == "prod" and not stripe_signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
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

    # Item 37: Max single-credit limit of $500 (50000 cents)
    if amount_cents > 50000:
        raise HTTPException(
            status_code=400,
            detail="Single credit cannot exceed $500 (50000 cents)"
        )

    try:
        import uuid
        result = PayoutService.credit_wallet(
            db, driver_id, amount_cents, reference_type, str(uuid.uuid4()), description
        )
        # Item 37: Structured audit log for admin wallet credits
        logger.info(
            "admin_wallet_credit",
            extra={
                "admin_user_id": current_user.id,
                "driver_id": driver_id,
                "amount_cents": amount_cents,
                "reference_type": reference_type,
            },
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
