"""
Merchant Onboarding Service

Business logic for merchant onboarding, location claims, and placement rules.
"""
import logging
import uuid
import secrets
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from app.models import (
    MerchantAccount,
    MerchantLocationClaim,
    MerchantPlacementRule,
    MerchantPaymentMethod,
    User,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory state for OAuth (TODO: Use Redis or database in production)
_oauth_states: Dict[str, Dict] = {}


def create_or_get_merchant_account(db: Session, user_id: int) -> MerchantAccount:
    """
    Create or get merchant account for a user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        MerchantAccount instance
    """
    account = (
        db.query(MerchantAccount)
        .filter(MerchantAccount.owner_user_id == user_id)
        .first()
    )
    
    if not account:
        account = MerchantAccount(
            id=str(uuid.uuid4()),
            owner_user_id=user_id,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        logger.info(f"Created merchant account {account.id} for user {user_id}")
    
    return account


def store_oauth_state(state: str, user_id: int) -> None:
    """
    Store OAuth state for CSRF protection.
    
    TODO: Use Redis or database in production instead of in-memory dict.
    """
    _oauth_states[state] = {
        "user_id": user_id,
        "created_at": datetime.utcnow(),
    }


def validate_oauth_state(state: str) -> Optional[int]:
    """
    Validate OAuth state and return associated user_id.
    
    Returns:
        user_id if valid, None otherwise
    """
    state_data = _oauth_states.get(state)
    if not state_data:
        return None
    
    # Clean up old states (older than 10 minutes)
    if (datetime.utcnow() - state_data["created_at"]).total_seconds() > 600:
        del _oauth_states[state]
        return None
    
    return state_data["user_id"]


def claim_location(
    db: Session,
    merchant_account_id: str,
    place_id: str,
) -> MerchantLocationClaim:
    """
    Claim a Google Place location for a merchant account.
    
    Args:
        db: Database session
        merchant_account_id: Merchant account ID
        place_id: Google Places place_id
    
    Returns:
        Created MerchantLocationClaim
    
    Raises:
        ValueError: If location already claimed by another merchant
    """
    # Check if already claimed by this merchant
    existing = (
        db.query(MerchantLocationClaim)
        .filter(
            MerchantLocationClaim.merchant_account_id == merchant_account_id,
            MerchantLocationClaim.place_id == place_id,
        )
        .first()
    )
    
    if existing:
        return existing
    
    # Check if claimed by another merchant (optional - can allow multiple claims)
    # For now, we'll allow multiple merchants to claim the same place_id
    # In production, you might want to enforce uniqueness
    
    claim = MerchantLocationClaim(
        id=str(uuid.uuid4()),
        merchant_account_id=merchant_account_id,
        place_id=place_id,
        status="CLAIMED",
    )
    
    db.add(claim)
    db.commit()
    db.refresh(claim)
    
    logger.info(f"Claimed location {place_id} for merchant account {merchant_account_id}")
    
    return claim


def create_setup_intent(
    db: Session,
    merchant_account_id: str,
) -> Dict[str, str]:
    """
    Create Stripe SetupIntent for card-on-file collection.
    
    Args:
        db: Database session
        merchant_account_id: Merchant account ID
    
    Returns:
        Dict with client_secret and setup_intent_id
    
    Raises:
        ValueError: If Stripe not configured
    """
    # Check if Stripe is configured
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("Stripe not configured (STRIPE_SECRET_KEY missing)")
    
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
    except ImportError:
        raise ValueError("Stripe package not installed")
    
    # Get or create merchant account
    merchant_account = (
        db.query(MerchantAccount)
        .filter(MerchantAccount.id == merchant_account_id)
        .first()
    )
    
    if not merchant_account:
        raise ValueError(f"Merchant account {merchant_account_id} not found")
    
    # Check for existing active payment method
    existing_payment = (
        db.query(MerchantPaymentMethod)
        .filter(
            MerchantPaymentMethod.merchant_account_id == merchant_account_id,
            MerchantPaymentMethod.status == "ACTIVE",
        )
        .first()
    )
    
    if existing_payment:
        # Return existing payment method info (or create new SetupIntent for updating)
        # For now, create a new SetupIntent
        pass
    
    # Create Stripe Customer if needed
    stripe_customer_id = None
    if existing_payment:
        stripe_customer_id = existing_payment.stripe_customer_id
    else:
        # Create new Stripe Customer
        customer = stripe.Customer.create(
            metadata={
                "merchant_account_id": merchant_account_id,
                "user_id": str(merchant_account.owner_user_id),
            }
        )
        stripe_customer_id = customer.id
    
    # Create SetupIntent
    setup_intent = stripe.SetupIntent.create(
        customer=stripe_customer_id,
        payment_method_types=["card"],
        usage="off_session",  # Card-on-file for future charges
        metadata={
            "merchant_account_id": merchant_account_id,
        }
    )
    
    return {
        "client_secret": setup_intent.client_secret,
        "setup_intent_id": setup_intent.id,
        "stripe_customer_id": stripe_customer_id,
    }


def update_placement_rule(
    db: Session,
    merchant_account_id: str,
    place_id: str,
    daily_cap_cents: Optional[int] = None,
    boost_weight: Optional[float] = None,
    perks_enabled: Optional[bool] = None,
) -> MerchantPlacementRule:
    """
    Update placement rule for a location.
    
    Requires:
    - Location must be claimed by merchant
    - Active payment method must exist
    
    Args:
        db: Database session
        merchant_account_id: Merchant account ID
        place_id: Google Places place_id
        daily_cap_cents: Optional daily spending cap
        boost_weight: Optional boost weight (additive)
        perks_enabled: Optional perks enabled flag
    
    Returns:
        Updated MerchantPlacementRule
    
    Raises:
        ValueError: If location not claimed or payment method missing
    """
    # Verify location is claimed by this merchant
    claim = (
        db.query(MerchantLocationClaim)
        .filter(
            MerchantLocationClaim.merchant_account_id == merchant_account_id,
            MerchantLocationClaim.place_id == place_id,
            MerchantLocationClaim.status == "CLAIMED",
        )
        .first()
    )
    
    if not claim:
        raise ValueError(f"Location {place_id} not claimed by merchant account {merchant_account_id}")
    
    # Verify active payment method exists
    payment_method = (
        db.query(MerchantPaymentMethod)
        .filter(
            MerchantPaymentMethod.merchant_account_id == merchant_account_id,
            MerchantPaymentMethod.status == "ACTIVE",
        )
        .first()
    )
    
    if not payment_method:
        raise ValueError(f"Active payment method required for placement rules")
    
    # Get or create placement rule
    rule = (
        db.query(MerchantPlacementRule)
        .filter(MerchantPlacementRule.place_id == place_id)
        .first()
    )
    
    if not rule:
        rule = MerchantPlacementRule(
            id=str(uuid.uuid4()),
            place_id=place_id,
            status="ACTIVE",
            daily_cap_cents=daily_cap_cents or 0,
            boost_weight=boost_weight or 0.0,
            perks_enabled=perks_enabled or False,
        )
        db.add(rule)
    else:
        # Update existing rule
        if daily_cap_cents is not None:
            rule.daily_cap_cents = daily_cap_cents
        if boost_weight is not None:
            rule.boost_weight = boost_weight
        if perks_enabled is not None:
            rule.perks_enabled = perks_enabled
        rule.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(rule)
    
    logger.info(
        f"Updated placement rule for {place_id}: "
        f"cap={rule.daily_cap_cents}, boost={rule.boost_weight}, perks={rule.perks_enabled}"
    )
    
    return rule



