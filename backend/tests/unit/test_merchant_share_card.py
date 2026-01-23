"""
Unit tests for merchant share card service
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.domain import DomainMerchant, MerchantRedemption
from app.services.merchant_share_card import generate_share_card
import uuid


def test_share_card_png_header(db: Session, test_merchant):
    """Test that share card returns PNG bytes with correct header"""
    png_bytes = generate_share_card(db, test_merchant.id, days=7)
    
    # PNG files start with PNG signature
    assert png_bytes.startswith(b'\x89PNG\r\n\x1a\n')
    assert len(png_bytes) > 0


def test_share_card_deterministic_size(db: Session, test_merchant):
    """Test that share card has deterministic output size (not exact bytes)"""
    png_bytes1 = generate_share_card(db, test_merchant.id, days=7)
    png_bytes2 = generate_share_card(db, test_merchant.id, days=7)
    
    # Size should be similar (not exact due to compression, but close)
    assert abs(len(png_bytes1) - len(png_bytes2)) < 100  # Allow small variance


def test_share_card_zero_redemptions(db: Session, test_merchant):
    """Test that share card works when merchant has 0 redemptions"""
    png_bytes = generate_share_card(db, test_merchant.id, days=7)
    
    assert png_bytes.startswith(b'\x89PNG\r\n\x1a\n')
    assert len(png_bytes) > 0


def test_share_card_with_redemptions(db: Session, test_merchant, test_user):
    """Test share card with actual redemptions"""
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
    
    png_bytes = generate_share_card(db, test_merchant.id, days=7)
    
    assert png_bytes.startswith(b'\x89PNG\r\n\x1a\n')
    assert len(png_bytes) > 0


def test_share_card_merchant_not_found(db: Session):
    """Test that share card raises ValueError for non-existent merchant"""
    with pytest.raises(ValueError, match="not found"):
        generate_share_card(db, "nonexistent_merchant_id", days=7)
