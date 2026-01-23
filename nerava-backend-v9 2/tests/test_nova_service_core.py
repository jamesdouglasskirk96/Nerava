"""
Comprehensive tests for Nova Service

Tests grant_to_driver, redeem_from_driver, idempotency, and error paths.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.nova_service import NovaService, compute_payload_hash
from app.models_domain import DriverWallet, DomainMerchant, NovaTransaction
from app.models import User
import uuid


class TestComputePayloadHash:
    """Test compute_payload_hash function"""
    
    def test_compute_payload_hash_deterministic(self):
        """Test compute_payload_hash is deterministic"""
        payload = {"driver_id": 1, "amount": 100, "type": "driver_earn"}
        hash1 = compute_payload_hash(payload)
        hash2 = compute_payload_hash(payload)
        assert hash1 == hash2
        assert len(hash1) == 16
    
    def test_compute_payload_hash_different_payloads(self):
        """Test compute_payload_hash produces different hashes for different payloads"""
        payload1 = {"driver_id": 1, "amount": 100}
        payload2 = {"driver_id": 1, "amount": 200}
        hash1 = compute_payload_hash(payload1)
        hash2 = compute_payload_hash(payload2)
        assert hash1 != hash2
    
    def test_compute_payload_hash_sorted_keys(self):
        """Test compute_payload_hash uses sorted keys"""
        payload1 = {"a": 1, "b": 2}
        payload2 = {"b": 2, "a": 1}
        hash1 = compute_payload_hash(payload1)
        hash2 = compute_payload_hash(payload2)
        assert hash1 == hash2


class TestNovaServiceGrantToDriver:
    """Test NovaService.grant_to_driver"""
    
    def test_grant_to_driver_happy_path(self, db: Session):
        """Test successful Nova grant"""
        # Create user and wallet
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        wallet = DriverWallet(user_id=user.id, nova_balance=0, energy_reputation_score=0)
        db.add(wallet)
        db.commit()
        
        # Grant Nova
        transaction = NovaService.grant_to_driver(
            db=db,
            driver_id=user.id,
            amount=100,
            type="driver_earn",
            session_id="session1"
        )
        
        assert transaction is not None
        assert transaction.amount == 100
        assert transaction.type == "driver_earn"
        
        # Check wallet updated
        db.refresh(wallet)
        assert wallet.nova_balance == 100
        assert wallet.energy_reputation_score == 100  # driver_earn increments reputation
    
    def test_grant_to_driver_creates_wallet(self, db: Session):
        """Test grant_to_driver creates wallet if not exists"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        # Grant Nova (no wallet exists)
        transaction = NovaService.grant_to_driver(
            db=db,
            driver_id=user.id,
            amount=50,
            type="driver_earn"
        )
        
        assert transaction is not None
        wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user.id).first()
        assert wallet is not None
        assert wallet.nova_balance == 50
    
    def test_grant_to_driver_idempotent(self, db: Session):
        """Test grant_to_driver is idempotent with same key"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        idempotency_key = str(uuid.uuid4())
        
        # First grant
        txn1 = NovaService.grant_to_driver(
            db=db,
            driver_id=user.id,
            amount=100,
            idempotency_key=idempotency_key
        )
        
        # Second grant with same key
        txn2 = NovaService.grant_to_driver(
            db=db,
            driver_id=user.id,
            amount=100,
            idempotency_key=idempotency_key
        )
        
        # Should return same transaction
        assert txn1.id == txn2.id
        
        # Wallet should only be incremented once
        wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user.id).first()
        assert wallet.nova_balance == 100
    
    def test_grant_to_driver_idempotency_conflict(self, db: Session):
        """Test grant_to_driver raises error on idempotency conflict"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        idempotency_key = str(uuid.uuid4())
        
        # First grant
        NovaService.grant_to_driver(
            db=db,
            driver_id=user.id,
            amount=100,
            idempotency_key=idempotency_key
        )
        
        # Second grant with same key but different amount (should conflict)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            NovaService.grant_to_driver(
                db=db,
                driver_id=user.id,
                amount=200,  # Different amount
                idempotency_key=idempotency_key
            )
        assert exc_info.value.status_code == 409
    
    def test_grant_to_driver_admin_grant_no_reputation(self, db: Session):
        """Test admin_grant type does not increment reputation"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        transaction = NovaService.grant_to_driver(
            db=db,
            driver_id=user.id,
            amount=100,
            type="admin_grant"  # Not driver_earn
        )
        
        wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user.id).first()
        assert wallet.nova_balance == 100
        assert wallet.energy_reputation_score == 0  # No reputation for admin_grant


class TestNovaServiceRedeemFromDriver:
    """Test NovaService.redeem_from_driver"""
    
    def test_redeem_from_driver_happy_path(self, db: Session):
        """Test successful Nova redemption"""
        # Create user, wallet, and merchant
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        wallet = DriverWallet(user_id=user.id, nova_balance=200, energy_reputation_score=0)
        db.add(wallet)
        
        merchant = DomainMerchant(
            id=str(uuid.uuid4()),
            name="Test Merchant",
            status="active",
            nova_balance=0,
            zone_slug="test_zone",
            lat=30.0,
            lng=-97.0
        )
        db.add(merchant)
        db.commit()
        
        # Redeem Nova
        result = NovaService.redeem_from_driver(
            db=db,
            driver_id=user.id,
            merchant_id=merchant.id,
            amount=100
        )
        
        assert result["amount"] == 100
        assert result["driver_balance"] == 100  # 200 - 100
        assert result["merchant_balance"] == 100  # 0 + 100
        
        # Check transactions created
        transactions = db.query(NovaTransaction).filter(
            NovaTransaction.driver_user_id == user.id
        ).all()
        assert len(transactions) >= 1
    
    def test_redeem_from_driver_insufficient_balance(self, db: Session):
        """Test redeem_from_driver raises error for insufficient balance"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        wallet = DriverWallet(user_id=user.id, nova_balance=50, energy_reputation_score=0)
        db.add(wallet)
        
        merchant = DomainMerchant(
            id=str(uuid.uuid4()),
            name="Test Merchant",
            status="active",
            nova_balance=0,
            zone_slug="test_zone",
            lat=30.0,
            lng=-97.0
        )
        db.add(merchant)
        db.commit()
        
        # Try to redeem more than balance
        with pytest.raises(ValueError, match="Insufficient"):
            NovaService.redeem_from_driver(
                db=db,
                driver_id=user.id,
                merchant_id=merchant.id,
                amount=100  # More than 50
            )
    
    def test_redeem_from_driver_no_wallet(self, db: Session):
        """Test redeem_from_driver raises error when wallet doesn't exist"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        
        merchant = DomainMerchant(
            id=str(uuid.uuid4()),
            name="Test Merchant",
            status="active",
            nova_balance=0,
            zone_slug="test_zone",
            lat=30.0,
            lng=-97.0
        )
        db.add(merchant)
        db.commit()
        
        with pytest.raises(ValueError, match="wallet not found"):
            NovaService.redeem_from_driver(
                db=db,
                driver_id=user.id,
                merchant_id=merchant.id,
                amount=100
            )
    
    def test_redeem_from_driver_inactive_merchant(self, db: Session):
        """Test redeem_from_driver raises error for inactive merchant"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        wallet = DriverWallet(user_id=user.id, nova_balance=200, energy_reputation_score=0)
        db.add(wallet)
        
        merchant = DomainMerchant(
            id=str(uuid.uuid4()),
            name="Test Merchant",
            status="suspended",  # Not active
            nova_balance=0,
            zone_slug="test_zone",
            lat=30.0,
            lng=-97.0
        )
        db.add(merchant)
        db.commit()
        
        with pytest.raises(ValueError, match="not found or not active"):
            NovaService.redeem_from_driver(
                db=db,
                driver_id=user.id,
                merchant_id=merchant.id,
                amount=100
            )
    
    def test_redeem_from_driver_idempotent(self, db: Session):
        """Test redeem_from_driver is idempotent"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        wallet = DriverWallet(user_id=user.id, nova_balance=200, energy_reputation_score=0)
        db.add(wallet)
        
        merchant = DomainMerchant(
            id=str(uuid.uuid4()),
            name="Test Merchant",
            status="active",
            nova_balance=0,
            zone_slug="test_zone",
            lat=30.0,
            lng=-97.0
        )
        db.add(merchant)
        db.commit()
        
        idempotency_key = str(uuid.uuid4())
        
        # First redemption
        result1 = NovaService.redeem_from_driver(
            db=db,
            driver_id=user.id,
            merchant_id=merchant.id,
            amount=100,
            idempotency_key=idempotency_key
        )
        
        # Second redemption with same key
        result2 = NovaService.redeem_from_driver(
            db=db,
            driver_id=user.id,
            merchant_id=merchant.id,
            amount=100,
            idempotency_key=idempotency_key
        )
        
        assert result1["transaction_id"] == result2["transaction_id"]
        assert result2["idempotent"] is True
        assert result2["driver_balance"] == 100  # Should still be 100, not 0
    
    def test_redeem_from_driver_atomic_update(self, db: Session):
        """Test redeem_from_driver uses atomic balance update"""
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        wallet = DriverWallet(user_id=user.id, nova_balance=200, energy_reputation_score=0)
        db.add(wallet)
        
        merchant = DomainMerchant(
            id=str(uuid.uuid4()),
            name="Test Merchant",
            status="active",
            nova_balance=0,
            zone_slug="test_zone",
            lat=30.0,
            lng=-97.0
        )
        db.add(merchant)
        db.commit()
        
        # Redeem
        result = NovaService.redeem_from_driver(
            db=db,
            driver_id=user.id,
            merchant_id=merchant.id,
            amount=100
        )
        
        # Verify balances updated correctly
        db.refresh(wallet)
        db.refresh(merchant)
        assert wallet.nova_balance == 100
        assert merchant.nova_balance == 100







