"""
Merchant Billing Router

Handles subscription management via Stripe Checkout:
- Create checkout session for Pro / Ads subscriptions
- Get subscription status
- Cancel subscription
- Stripe webhook for subscription events
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.dependencies_domain import get_current_user
from app.services.merchant_onboarding_service import create_or_get_merchant_account
from app.services.merchant_subscription_service import (
    create_checkout_session,
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
    get_subscription,
    cancel_subscription,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/merchant/billing", tags=["merchant_billing"])


class SubscribeRequest(BaseModel):
    place_id: str
    plan: str  # "pro" | "ads_flat"


class SubscribeResponse(BaseModel):
    checkout_url: str
    session_id: str


@router.post("/subscribe", response_model=SubscribeResponse, summary="Create subscription checkout")
async def subscribe(
    request: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session for a subscription plan."""
    try:
        merchant_account = create_or_get_merchant_account(db, current_user.id)
        portal_url = settings.MERCHANT_PORTAL_URL

        result = create_checkout_session(
            db=db,
            merchant_account_id=merchant_account.id,
            place_id=request.place_id,
            plan=request.plan,
            success_url=f"{portal_url}/billing?success=true",
            cancel_url=f"{portal_url}/billing?canceled=true",
        )

        return SubscribeResponse(
            checkout_url=result["checkout_url"],
            session_id=result["session_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.get("/subscription", summary="Get subscription status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns current subscription details or null."""
    merchant_account = create_or_get_merchant_account(db, current_user.id)
    sub = get_subscription(db, merchant_account.id)
    return {"subscription": sub}


@router.post("/cancel", summary="Cancel subscription at period end")
async def cancel_subscription_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel the active subscription at end of current billing period."""
    merchant_account = create_or_get_merchant_account(db, current_user.id)
    success = cancel_subscription(db, merchant_account.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription found")
    return {"ok": True, "message": "Subscription will be canceled at end of billing period"}


@router.post("/portal", summary="Create Stripe Billing Portal session")
async def create_billing_portal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Billing Portal session for the merchant to manage subscriptions and payment methods."""
    import stripe as stripe_module

    stripe_module.api_key = settings.STRIPE_SECRET_KEY
    if not stripe_module.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    merchant_account = create_or_get_merchant_account(db, current_user.id)

    # Find the stripe_customer_id from an existing subscription
    from app.models.merchant_subscription import MerchantSubscription

    sub = (
        db.query(MerchantSubscription)
        .filter(
            MerchantSubscription.merchant_account_id == merchant_account.id,
            MerchantSubscription.stripe_customer_id.isnot(None),
        )
        .order_by(MerchantSubscription.created_at.desc())
        .first()
    )
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Stripe customer found. Subscribe to a plan first.",
        )

    try:
        portal_url = settings.MERCHANT_PORTAL_URL
        session = stripe_module.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=f"{portal_url}/billing",
        )
        return {"url": session.url}
    except Exception as e:
        logger.error(f"Error creating billing portal session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create billing portal session")


@router.get("/invoices", summary="Get invoice history")
async def get_invoices(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List Stripe invoices for the merchant's billing account."""
    import stripe as stripe_module

    stripe_module.api_key = settings.STRIPE_SECRET_KEY
    if not stripe_module.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    merchant_account = create_or_get_merchant_account(db, current_user.id)

    from app.models.merchant_subscription import MerchantSubscription

    sub = (
        db.query(MerchantSubscription)
        .filter(
            MerchantSubscription.merchant_account_id == merchant_account.id,
            MerchantSubscription.stripe_customer_id.isnot(None),
        )
        .order_by(MerchantSubscription.created_at.desc())
        .first()
    )
    if not sub or not sub.stripe_customer_id:
        return {"invoices": []}

    try:
        invoices = stripe_module.Invoice.list(
            customer=sub.stripe_customer_id,
            limit=min(limit, 100),
        )
        result = []
        for inv in invoices.data:
            result.append({
                "id": inv.id,
                "amount_due": inv.amount_due,
                "status": inv.status,
                "created": inv.created,
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url,
            })
        return {"invoices": result}
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch invoices")


@router.post("/webhook", summary="Stripe merchant billing webhook")
async def stripe_merchant_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events for merchant subscriptions."""
    import stripe

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    webhook_secret = settings.STRIPE_MERCHANT_WEBHOOK_SECRET
    if not webhook_secret:
        logger.warning("STRIPE_MERCHANT_WEBHOOK_SECRET not configured, skipping verification")
        try:
            event = stripe.Event.construct_from(
                stripe.util.convert_to_stripe_object(
                    stripe.util.json.loads(payload),
                    stripe.api_key,
                ),
                stripe.api_key,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        handle_checkout_completed(db, data_object)
    elif event_type == "customer.subscription.updated":
        handle_subscription_updated(db, data_object)
    elif event_type == "customer.subscription.deleted":
        handle_subscription_deleted(db, data_object)
    else:
        logger.debug(f"Unhandled merchant billing event: {event_type}")

    return {"received": True}
