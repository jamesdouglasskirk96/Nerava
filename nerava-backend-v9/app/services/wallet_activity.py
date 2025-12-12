"""
Wallet Activity Service

Helper functions to mark wallet activity for pass refresh tracking.
"""
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.domain import DriverWallet


def mark_wallet_activity(db: Session, driver_user_id: int) -> None:
    """
    Mark wallet activity by updating wallet_activity_updated_at timestamp.
    
    This should be called whenever:
    - Nova is earned (grant_to_driver)
    - Nova is spent (redeem_from_driver or MerchantRedemption created)
    
    Args:
        db: Database session
        driver_user_id: Driver user ID
        
    Note:
        Does not commit - caller should commit in their transaction pattern.
    """
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == driver_user_id).first()
    
    if not wallet:
        # Create wallet if it doesn't exist
        wallet = DriverWallet(
            user_id=driver_user_id,
            nova_balance=0,
            energy_reputation_score=0
        )
        db.add(wallet)
        db.flush()
    
    wallet.wallet_activity_updated_at = datetime.utcnow()
    # Note: updated_at is handled by SQLAlchemy onupdate
