"""
Nova Service - Nova balance management and transactions
for Domain Charge Party MVP
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
from datetime import datetime
import logging

from app.models_domain import (
    DriverWallet,
    DomainMerchant,
    NovaTransaction,
    DomainChargingSession,
    StripePayment
)
from app.services.wallet_activity import mark_wallet_activity

logger = logging.getLogger(__name__)


class NovaService:
    """Service for Nova balance and transaction management"""
    
    @staticmethod
    def grant_to_driver(
        db: Session,
        driver_id: int,
        amount: int,
        *,
        type: str = "driver_earn",
        session_id: Optional[str] = None,
        event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NovaTransaction:
        """
        Grant Nova to a driver.
        
        Args:
            driver_id: User ID of the driver
            amount: Nova amount (always positive)
            type: Transaction type (driver_earn, admin_grant, etc.)
            session_id: Optional charging session ID
            metadata: Optional metadata dict
        """
        # Get or create driver wallet
        wallet = db.query(DriverWallet).filter(DriverWallet.user_id == driver_id).first()
        if not wallet:
            wallet = DriverWallet(user_id=driver_id, nova_balance=0, energy_reputation_score=0)
            db.add(wallet)
            db.flush()
        
        # Update balance
        wallet.nova_balance += amount
        wallet.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = NovaTransaction(
            id=str(uuid.uuid4()),
            type=type,
            driver_user_id=driver_id,
            amount=amount,
            session_id=session_id,
            event_id=event_id,
            transaction_meta=metadata or {}
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Mark wallet activity for pass refresh
        mark_wallet_activity(db, driver_id)
        db.commit()
        
        logger.info(f"Granted {amount} Nova to driver {driver_id} (type: {type}, session: {session_id})")
        return transaction
    
    @staticmethod
    def redeem_from_driver(
        db: Session,
        driver_id: int,
        merchant_id: str,
        amount: int,
        *,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Redeem Nova from driver to merchant.
        
        This performs two operations:
        1. Decreases driver wallet balance
        2. Increases merchant Nova balance
        3. Creates transaction records
        
        Args:
            driver_id: User ID of the driver
            merchant_id: Merchant ID
            amount: Nova amount to redeem (always positive)
            session_id: Optional charging session ID
            metadata: Optional metadata dict
        
        Returns:
            Dict with transaction info and new balances
        """
        # Validate driver has enough Nova
        wallet = db.query(DriverWallet).filter(DriverWallet.user_id == driver_id).first()
        if not wallet:
            raise ValueError(f"Driver wallet not found for user {driver_id}")
        
        if wallet.nova_balance < amount:
            raise ValueError(f"Insufficient Nova balance. Has {wallet.nova_balance}, needs {amount}")
        
        # Validate merchant exists and is active
        merchant = db.query(DomainMerchant).filter(
            and_(
                DomainMerchant.id == merchant_id,
                DomainMerchant.status == "active"
            )
        ).first()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found or not active")
        
        # Update driver wallet
        wallet.nova_balance -= amount
        wallet.updated_at = datetime.utcnow()
        
        # Update merchant balance
        merchant.nova_balance += amount
        merchant.updated_at = datetime.utcnow()
        
        # Create driver redemption transaction
        driver_txn = NovaTransaction(
            id=str(uuid.uuid4()),
            type="driver_redeem",
            driver_user_id=driver_id,
            merchant_id=merchant_id,
            amount=amount,
            session_id=session_id,
            transaction_meta=metadata or {}
        )
        db.add(driver_txn)
        
        # Create merchant earn transaction
        merchant_txn = NovaTransaction(
            id=str(uuid.uuid4()),
            type="merchant_earn",
            driver_user_id=driver_id,
            merchant_id=merchant_id,
            amount=amount,
            session_id=session_id,
            transaction_meta={**(metadata or {}), "source": "driver_redeem"}
        )
        db.add(merchant_txn)
        
        db.commit()
        db.refresh(wallet)
        db.refresh(merchant)
        
        # Mark wallet activity for pass refresh
        mark_wallet_activity(db, driver_id)
        db.commit()
        
        logger.info(f"Redeemed {amount} Nova from driver {driver_id} to merchant {merchant_id}")
        
        return {
            "transaction_id": driver_txn.id,
            "driver_balance": wallet.nova_balance,
            "merchant_balance": merchant.nova_balance,
            "amount": amount
        }
    
    @staticmethod
    def grant_to_merchant(
        db: Session,
        merchant_id: str,
        amount: int,
        *,
        type: str = "merchant_topup",
        stripe_payment_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NovaTransaction:
        """
        Grant Nova to a merchant (e.g., from Stripe purchase).
        
        Args:
            merchant_id: Merchant ID
            amount: Nova amount (always positive)
            type: Transaction type (merchant_topup, admin_grant, etc.)
            stripe_payment_id: Optional Stripe payment ID
            metadata: Optional metadata dict
        """
        # Validate merchant exists
        merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")
        
        # Update merchant balance
        merchant.nova_balance += amount
        merchant.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = NovaTransaction(
            id=str(uuid.uuid4()),
            type=type,
            merchant_id=merchant_id,
            amount=amount,
            stripe_payment_id=stripe_payment_id,
            transaction_meta=metadata or {}
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        db.refresh(merchant)
        
        logger.info(f"Granted {amount} Nova to merchant {merchant_id} (type: {type}, stripe: {stripe_payment_id})")
        return transaction
    
    @staticmethod
    def get_driver_wallet(db: Session, driver_id: int) -> DriverWallet:
        """Get or create driver wallet"""
        wallet = db.query(DriverWallet).filter(DriverWallet.user_id == driver_id).first()
        if not wallet:
            wallet = DriverWallet(user_id=driver_id, nova_balance=0, energy_reputation_score=0)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        return wallet
    
    @staticmethod
    def get_driver_transactions(
        db: Session,
        driver_id: int,
        limit: int = 50
    ) -> list[NovaTransaction]:
        """Get recent transactions for a driver"""
        return db.query(NovaTransaction).filter(
            NovaTransaction.driver_user_id == driver_id
        ).order_by(NovaTransaction.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_merchant_transactions(
        db: Session,
        merchant_id: str,
        limit: int = 50
    ) -> list[NovaTransaction]:
        """Get recent transactions for a merchant"""
        return db.query(NovaTransaction).filter(
            NovaTransaction.merchant_id == merchant_id
        ).order_by(NovaTransaction.created_at.desc()).limit(limit).all()

