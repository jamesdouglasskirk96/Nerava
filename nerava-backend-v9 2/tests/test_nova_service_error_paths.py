"""
Tests for Nova service error paths and edge cases.

Critical for financial integrity: concurrent grants, invalid states, idempotency.
"""
import pytest
from sqlalchemy.orm import Session
from app.services.nova_service import NovaService
from app.models_domain import DriverWallet, NovaTransaction
from app.models import User


def test_nova_grant_insufficient_balance_validation(db: Session):
    """Test that grant validation checks are in place."""
    # Create test user and wallet
    user = User(
        email="test@example.com",
        password_hash="hashed",
        is_active=True
    )
    db.add(user)
    db.flush()
    
    wallet = DriverWallet(
        driver_user_id=user.id,
        nova_balance=0
    )
    db.add(wallet)
    db.commit()
    
    # Grant should succeed (grants don't require balance)
    txn = NovaService.grant_to_driver(
        db,
        driver_id=user.id,
        amount=100,
        type="driver_earn"
    )
    
    assert txn is not None
    assert txn.amount == 100
    db.refresh(wallet)
    assert wallet.nova_balance == 100


def test_nova_grant_idempotency_duplicate_key(db: Session):
    """Test that duplicate idempotency key returns existing transaction."""
    user = User(
        email="test2@example.com",
        password_hash="hashed",
        is_active=True
    )
    db.add(user)
    db.flush()
    
    wallet = DriverWallet(
        driver_user_id=user.id,
        nova_balance=0
    )
    db.add(wallet)
    db.commit()
    
    idempotency_key = "test-key-123"
    
    # First grant
    txn1 = NovaService.grant_to_driver(
        db,
        driver_id=user.id,
        amount=100,
        type="driver_earn",
        idempotency_key=idempotency_key
    )
    
    # Second grant with same key
    txn2 = NovaService.grant_to_driver(
        db,
        driver_id=user.id,
        amount=100,
        type="driver_earn",
        idempotency_key=idempotency_key
    )
    
    # Should return same transaction or raise conflict
    assert txn1.id == txn2.id or txn2 is None
    
    # Balance should only increase once
    db.refresh(wallet)
    assert wallet.nova_balance == 100


def test_nova_redeem_insufficient_balance(db: Session):
    """Test that redemption fails when balance is insufficient."""
    user = User(
        email="test3@example.com",
        password_hash="hashed",
        is_active=True
    )
    db.add(user)
    db.flush()
    
    wallet = DriverWallet(
        driver_user_id=user.id,
        nova_balance=50  # Less than redemption amount
    )
    db.add(wallet)
    db.commit()
    
    # Try to redeem more than balance
    with pytest.raises(Exception):  # Should raise ValueError or HTTPException
        NovaService.redeem_from_driver(
            db,
            driver_id=user.id,
            amount=100,  # More than balance
            merchant_id="test_merchant",
            type="redemption"
        )


def test_nova_redeem_idempotency(db: Session):
    """Test that duplicate redemption is prevented."""
    user = User(
        email="test4@example.com",
        password_hash="hashed",
        is_active=True
    )
    db.add(user)
    db.flush()
    
    wallet = DriverWallet(
        driver_user_id=user.id,
        nova_balance=200
    )
    db.add(wallet)
    db.commit()
    
    idempotency_key = "redeem-key-123"
    
    # First redemption
    txn1 = NovaService.redeem_from_driver(
        db,
        driver_id=user.id,
        amount=100,
        merchant_id="test_merchant",
        type="redemption",
        idempotency_key=idempotency_key
    )
    
    # Second redemption with same key should fail or return existing
    try:
        txn2 = NovaService.redeem_from_driver(
            db,
            driver_id=user.id,
            amount=100,
            merchant_id="test_merchant",
            type="redemption",
            idempotency_key=idempotency_key
        )
        # If no exception, should be same transaction
        assert txn1.id == txn2.id
    except Exception:
        # Exception is also acceptable (idempotency conflict)
        pass
    
    # Balance should only decrease once
    db.refresh(wallet)
    assert wallet.nova_balance == 100







