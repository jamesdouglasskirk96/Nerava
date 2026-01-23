"""
Test helpers for financial flow tests.

Provides utilities for creating test users, merchants, wallets, and
performing financial operations in tests.
"""
import uuid
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.domain import DriverWallet, DomainMerchant, NovaTransaction, MerchantRedemption
from app.services.nova_service import NovaService


def create_test_user_with_wallet(db: Session, email: str = "test@example.com", initial_balance: int = 0) -> Tuple[User, DriverWallet]:
    """Create a test user with a driver wallet."""
    user = User(
        email=email,
        password_hash="hashed",
        is_active=True,
        role_flags="driver"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create wallet
    wallet = DriverWallet(
        user_id=user.id,
        nova_balance=initial_balance
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    
    return user, wallet


def create_test_merchant(db: Session, name: str = "Test Merchant", zone_slug: str = "test_zone", initial_balance: int = 0) -> DomainMerchant:
    """Create a test merchant."""
    merchant = DomainMerchant(
        id=str(uuid.uuid4()),
        name=name,
        lat=30.4,
        lng=-97.7,
        zone_slug=zone_slug,
        status="active",
        nova_balance=initial_balance
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    
    return merchant


def post_nova_grant(
    db: Session,
    driver_id: int,
    amount: int,
    session_id: Optional[str] = None,
    event_id: Optional[str] = None,
    idempotency_key: Optional[str] = None
) -> NovaTransaction:
    """Helper to grant Nova to a driver."""
    return NovaService.grant_to_driver(
        db=db,
        driver_id=driver_id,
        amount=amount,
        type="driver_earn",
        session_id=session_id,
        event_id=event_id,
        idempotency_key=idempotency_key
    )


def post_redemption(
    db: Session,
    driver_id: int,
    merchant_id: str,
    amount: int,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    """Helper to redeem Nova from a driver."""
    return NovaService.redeem_from_driver(
        db=db,
        driver_id=driver_id,
        merchant_id=merchant_id,
        amount=amount,
        idempotency_key=idempotency_key
    )


def verify_ledger_balance(db: Session, user_id: int) -> int:
    """
    Verify wallet balance matches sum of all Nova transactions.
    
    Returns the calculated balance from ledger.
    
    Note: merchant_earn transactions are excluded from driver balance calculation
    even though they have driver_user_id set (they're for merchant tracking only).
    """
    # Refresh session to get latest data
    db.expire_all()
    
    # Get all credit transactions for this user (exclude merchant_earn)
    credits = db.query(NovaTransaction).filter(
        NovaTransaction.driver_user_id == user_id,
        NovaTransaction.type.in_(["driver_earn", "admin_grant"])
    ).all()
    
    # Get all debit transactions for this user (driver_redeem only)
    debits = db.query(NovaTransaction).filter(
        NovaTransaction.driver_user_id == user_id,
        NovaTransaction.type == "driver_redeem"
    ).all()
    
    total_credits = sum(txn.amount for txn in credits)
    total_debits = sum(txn.amount for txn in debits)
    
    return total_credits - total_debits


def get_wallet_balance(db: Session, user_id: int) -> int:
    """Get current wallet balance from DriverWallet table."""
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user_id).first()
    return wallet.nova_balance if wallet else 0

