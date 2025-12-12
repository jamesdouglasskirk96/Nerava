"""
Unit tests for wallet timeline service
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.domain import DriverWallet, NovaTransaction, MerchantRedemption, DomainMerchant
from app.services.wallet_timeline import get_wallet_timeline
import uuid


def test_empty_timeline(db: Session):
    """Test that empty timeline returns []"""
    timeline = get_wallet_timeline(db, driver_user_id=999, limit=20)
    assert timeline == []


def test_earned_events_only(db: Session, test_user):
    """Test that earned events appear in timeline"""
    # Create wallet
    wallet = DriverWallet(user_id=test_user.id, nova_balance=1000, energy_reputation_score=0)
    db.add(wallet)
    db.flush()
    
    # Create earned transaction
    txn = NovaTransaction(
        id=str(uuid.uuid4()),
        type="driver_earn",
        driver_user_id=test_user.id,
        amount=500,
        created_at=datetime.utcnow()
    )
    db.add(txn)
    db.commit()
    
    timeline = get_wallet_timeline(db, driver_user_id=test_user.id, limit=20)
    assert len(timeline) == 1
    assert timeline[0]["type"] == "EARNED"
    assert timeline[0]["amount_cents"] == 500
    assert timeline[0]["title"] == "Off-Peak Charging"
    assert timeline[0]["redemption_id"] is None


def test_spent_events_only(db: Session, test_user, test_merchant):
    """Test that spent events appear in timeline"""
    # Create wallet
    wallet = DriverWallet(user_id=test_user.id, nova_balance=0, energy_reputation_score=0)
    db.add(wallet)
    db.flush()
    
    # Create redemption
    redemption = MerchantRedemption(
        id=str(uuid.uuid4()),
        merchant_id=test_merchant.id,
        driver_user_id=test_user.id,
        order_total_cents=1000,
        discount_cents=200,
        nova_spent_cents=200,
        created_at=datetime.utcnow()
    )
    db.add(redemption)
    db.commit()
    
    timeline = get_wallet_timeline(db, driver_user_id=test_user.id, limit=20)
    assert len(timeline) == 1
    assert timeline[0]["type"] == "SPENT"
    assert timeline[0]["amount_cents"] == 200
    assert timeline[0]["title"] == test_merchant.name
    assert timeline[0]["redemption_id"] == redemption.id


def test_no_duplicate_spent_events(db: Session, test_user, test_merchant):
    """
    Test that when BOTH MerchantRedemption exists AND NovaTransaction driver_redeem exists
    for same action, timeline shows ONE SPENT event only (from MerchantRedemption)
    and no duplicates.
    """
    # Create wallet
    wallet = DriverWallet(user_id=test_user.id, nova_balance=0, energy_reputation_score=0)
    db.add(wallet)
    db.flush()
    
    now = datetime.utcnow()
    
    # Create redemption (this is the source of truth for SPENT)
    redemption = MerchantRedemption(
        id=str(uuid.uuid4()),
        merchant_id=test_merchant.id,
        driver_user_id=test_user.id,
        order_total_cents=1000,
        discount_cents=200,
        nova_spent_cents=200,
        created_at=now
    )
    db.add(redemption)
    
    # Create driver_redeem transaction (this should be EXCLUDED to avoid duplicate)
    txn_redeem = NovaTransaction(
        id=str(uuid.uuid4()),
        type="driver_redeem",
        driver_user_id=test_user.id,
        merchant_id=test_merchant.id,
        amount=200,
        created_at=now
    )
    db.add(txn_redeem)
    
    # Also create an earned transaction to ensure it still shows
    txn_earn = NovaTransaction(
        id=str(uuid.uuid4()),
        type="driver_earn",
        driver_user_id=test_user.id,
        amount=500,
        created_at=now - timedelta(seconds=1)  # Slightly earlier
    )
    db.add(txn_earn)
    db.commit()
    
    timeline = get_wallet_timeline(db, driver_user_id=test_user.id, limit=20)
    
    # Should have exactly 2 events: 1 SPENT (from redemption) and 1 EARNED
    assert len(timeline) == 2
    
    # First should be SPENT (newer)
    assert timeline[0]["type"] == "SPENT"
    assert timeline[0]["redemption_id"] == redemption.id
    assert timeline[0]["amount_cents"] == 200
    
    # Second should be EARNED
    assert timeline[1]["type"] == "EARNED"
    assert timeline[1]["amount_cents"] == 500
    
    # Verify no driver_redeem transaction appears
    spent_ids = [e["id"] for e in timeline if e["type"] == "SPENT"]
    assert len(spent_ids) == 1
    assert spent_ids[0] == f"spent_{redemption.id}"


def test_timeline_ordering(db: Session, test_user, test_merchant):
    """Test that timeline is ordered newest first"""
    wallet = DriverWallet(user_id=test_user.id, nova_balance=0, energy_reputation_score=0)
    db.add(wallet)
    db.flush()
    
    base_time = datetime.utcnow()
    
    # Create events in reverse chronological order
    txn1 = NovaTransaction(
        id=str(uuid.uuid4()),
        type="driver_earn",
        driver_user_id=test_user.id,
        amount=100,
        created_at=base_time - timedelta(hours=2)
    )
    db.add(txn1)
    
    redemption1 = MerchantRedemption(
        id=str(uuid.uuid4()),
        merchant_id=test_merchant.id,
        driver_user_id=test_user.id,
        order_total_cents=500,
        discount_cents=50,
        nova_spent_cents=50,
        created_at=base_time - timedelta(hours=1)
    )
    db.add(redemption1)
    
    txn2 = NovaTransaction(
        id=str(uuid.uuid4()),
        type="driver_earn",
        driver_user_id=test_user.id,
        amount=200,
        created_at=base_time
    )
    db.add(txn2)
    db.commit()
    
    timeline = get_wallet_timeline(db, driver_user_id=test_user.id, limit=20)
    
    # Should be ordered: newest first
    assert len(timeline) == 3
    assert timeline[0]["type"] == "EARNED"  # Most recent
    assert timeline[0]["amount_cents"] == 200
    assert timeline[1]["type"] == "SPENT"
    assert timeline[1]["amount_cents"] == 50
    assert timeline[2]["type"] == "EARNED"  # Oldest
    assert timeline[2]["amount_cents"] == 100


def test_timeline_limit(db: Session, test_user):
    """Test that limit parameter works"""
    wallet = DriverWallet(user_id=test_user.id, nova_balance=0, energy_reputation_score=0)
    db.add(wallet)
    db.flush()
    
    # Create 10 earned transactions
    for i in range(10):
        txn = NovaTransaction(
            id=str(uuid.uuid4()),
            type="driver_earn",
            driver_user_id=test_user.id,
            amount=100,
            created_at=datetime.utcnow() - timedelta(minutes=i)
        )
        db.add(txn)
    db.commit()
    
    timeline = get_wallet_timeline(db, driver_user_id=test_user.id, limit=5)
    assert len(timeline) == 5
