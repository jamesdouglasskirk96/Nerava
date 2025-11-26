"""
Stripe Service - Nova purchase via Stripe Checkout
for Domain Charge Party MVP
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
import logging
import stripe

from app.models_domain import StripePayment, DomainMerchant
from app.services.nova_service import NovaService
from app.core.config import settings

logger = logging.getLogger(__name__)

# Stripe packages: package_id -> (usd_cents, nova_amount)
NOVA_PACKAGES = {
    "nova_100": {"usd_cents": 10000, "nova_amount": 1000},  # $100 for 1000 Nova
    "nova_500": {"usd_cents": 45000, "nova_amount": 5000},  # $450 for 5000 Nova (10% discount)
    "nova_1000": {"usd_cents": 80000, "nova_amount": 10000},  # $800 for 10000 Nova (20% discount)
}

# Initialize Stripe (will use env var STRIPE_SECRET_KEY)
stripe.api_key = settings.STRIPE_SECRET_KEY if settings.STRIPE_SECRET_KEY else None


class StripeService:
    """Service for Stripe Checkout and webhook handling"""
    
    @staticmethod
    def create_checkout_session(
        db: Session,
        merchant_id: str,
        package_id: str
    ) -> Dict[str, Any]:
        """
        Create Stripe Checkout session for Nova purchase.
        
        Args:
            merchant_id: Merchant ID
            package_id: Package ID (e.g., "nova_100")
        
        Returns:
            Dict with checkout_url
        """
        if not stripe.api_key:
            raise ValueError("Stripe not configured. Set STRIPE_SECRET_KEY environment variable.")
        
        # Validate package
        if package_id not in NOVA_PACKAGES:
            raise ValueError(f"Invalid package_id: {package_id}")
        
        package = NOVA_PACKAGES[package_id]
        
        # Validate merchant exists
        merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")
        
        # Create Stripe Checkout session
        payment_id = str(uuid.uuid4())
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{package['nova_amount']} Nova",
                            "description": f"Purchase {package['nova_amount']} Nova for Domain Charge Party"
                        },
                        "unit_amount": package["usd_cents"]
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=f"{settings.FRONTEND_URL}/merchant/dashboard?success=true",
                cancel_url=f"{settings.FRONTEND_URL}/merchant/buy-nova?cancelled=true",
                metadata={
                    "merchant_id": merchant_id,
                    "nova_amount": package["nova_amount"],
                    "package_id": package_id,
                    "payment_id": payment_id
                },
                client_reference_id=payment_id
            )
            
            # Create payment record
            stripe_payment = StripePayment(
                id=payment_id,
                stripe_session_id=checkout_session.id,
                merchant_id=merchant_id,
                amount_usd=package["usd_cents"],
                nova_issued=package["nova_amount"],
                status="pending"
            )
            db.add(stripe_payment)
            db.commit()
            db.refresh(stripe_payment)
            
            logger.info(f"Created Stripe checkout session for merchant {merchant_id}: {checkout_session.id}")
            
            return {
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise ValueError(f"Stripe error: {str(e)}")
    
    @staticmethod
    def handle_webhook(
        db: Session,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook event.
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            webhook_secret: Stripe webhook secret
        
        Returns:
            Dict with status and message
        """
        if not stripe.api_key:
            raise ValueError("Stripe not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload in Stripe webhook: {e}")
            raise ValueError(f"Invalid payload: {e}")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in Stripe webhook: {e}")
            raise ValueError(f"Invalid signature: {e}")
        
        # Handle the event
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            return StripeService._handle_checkout_completed(db, session, event["id"])
        else:
            logger.info(f"Unhandled Stripe event type: {event['type']}")
            return {"status": "ignored", "message": f"Event type {event['type']} not handled"}
    
    @staticmethod
    def _handle_checkout_completed(
        db: Session,
        session: Dict[str, Any],
        event_id: str
    ) -> Dict[str, Any]:
        """Handle checkout.session.completed event"""
        stripe_session_id = session["id"]
        payment_intent_id = session.get("payment_intent")
        metadata = session.get("metadata", {})
        
        merchant_id = metadata.get("merchant_id")
        nova_amount = int(metadata.get("nova_amount", 0))
        package_id = metadata.get("package_id")
        payment_id = metadata.get("payment_id")
        
        # Check for idempotency
        existing_payment = db.query(StripePayment).filter(
            StripePayment.stripe_event_id == event_id
        ).first()
        
        if existing_payment:
            logger.info(f"Webhook event {event_id} already processed (idempotent)")
            return {"status": "already_processed", "payment_id": existing_payment.id}
        
        # Find payment record by session_id or payment_id
        stripe_payment = db.query(StripePayment).filter(
            StripePayment.stripe_session_id == stripe_session_id
        ).first()
        
        if not stripe_payment and payment_id:
            stripe_payment = db.query(StripePayment).filter(
                StripePayment.id == payment_id
            ).first()
        
        if not stripe_payment:
            logger.error(f"Stripe payment not found for session {stripe_session_id}")
            return {"status": "error", "message": "Payment record not found"}
        
        # Update payment status
        stripe_payment.status = "paid"
        stripe_payment.stripe_payment_intent_id = payment_intent_id
        stripe_payment.stripe_event_id = event_id
        db.flush()
        
        # Grant Nova to merchant
        try:
            NovaService.grant_to_merchant(
                db=db,
                merchant_id=merchant_id,
                amount=nova_amount,
                type="merchant_topup",
                stripe_payment_id=stripe_payment.id,
                metadata={
                    "package_id": package_id,
                    "stripe_session_id": stripe_session_id
                }
            )
            
            db.commit()
            logger.info(f"Granted {nova_amount} Nova to merchant {merchant_id} via Stripe payment {stripe_payment.id}")
            
            return {
                "status": "success",
                "payment_id": stripe_payment.id,
                "nova_granted": nova_amount
            }
        except Exception as e:
            db.rollback()
            stripe_payment.status = "failed"
            db.commit()
            logger.error(f"Failed to grant Nova after Stripe payment: {e}")
            return {"status": "error", "message": str(e)}

