"""
Unit tests for QR Service - Merchant QR tokens
"""
import pytest
from datetime import datetime
from app.services.qr_service import (
    create_or_get_merchant_qr,
    resolve_qr_token as resolve_merchant_qr_token,
)
from app.models.domain import DomainMerchant


class TestMerchantQrTokens:
    """Test merchant QR token creation and resolution"""
    
    def test_create_merchant_qr_creates_token(self, db):
        """Should create a new QR token if merchant doesn't have one"""
        merchant = DomainMerchant(
            id="merchant_1",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0
        )
        db.add(merchant)
        db.commit()
        
        # Initially no token
        assert merchant.qr_token is None
        
        # Create QR
        result = create_or_get_merchant_qr(db, merchant)
        
        assert "token" in result
        assert "url" in result
        assert result["token"] is not None
        assert len(result["token"]) > 0
        assert merchant.qr_token == result["token"]
        assert merchant.qr_created_at is not None
    
    def test_create_merchant_qr_reuses_existing_token(self, db):
        """Should return existing token if merchant already has one"""
        merchant = DomainMerchant(
            id="merchant_2",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0,
            qr_token="existing_token_123"
        )
        db.add(merchant)
        db.commit()
        
        # Get QR (should return existing)
        result = create_or_get_merchant_qr(db, merchant)
        
        assert result["token"] == "existing_token_123"
        assert merchant.qr_token == "existing_token_123"
    
    def test_resolve_merchant_qr_token_found(self, db):
        """Should resolve QR token to active merchant"""
        merchant = DomainMerchant(
            id="merchant_3",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0,
            qr_token="test_token_456"
        )
        db.add(merchant)
        db.commit()
        
        # Resolve token
        result = resolve_merchant_qr_token(db, "test_token_456")
        
        assert result is not None
        assert result.id == "merchant_3"
        assert result.name == "Test Merchant"
        assert result.qr_last_used_at is not None
    
    def test_resolve_merchant_qr_token_not_found(self, db):
        """Should return None for unknown token"""
        result = resolve_merchant_qr_token(db, "unknown_token")
        assert result is None
    
    def test_resolve_merchant_qr_token_inactive_merchant(self, db):
        """Should return None for inactive merchant"""
        merchant = DomainMerchant(
            id="merchant_4",
            name="Inactive Merchant",
            lat=30.4,
            lng=-97.7,
            status="suspended",  # Not active
            zone_slug="national",
            nova_balance=0,
            qr_token="inactive_token"
        )
        db.add(merchant)
        db.commit()
        
        result = resolve_merchant_qr_token(db, "inactive_token")
        assert result is None

