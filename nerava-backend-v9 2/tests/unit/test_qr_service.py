"""
Unit tests for QR Service - QR/code resolution
"""
import pytest
from datetime import datetime, timedelta
from app.services.qr_service import (
    resolve_qr_token,
    check_code_status,
)
from app.models.while_you_charge import Merchant, MerchantOfferCode


class TestResolveQrToken:
    """Test QR token resolution"""
    
    def test_resolves_valid_token_to_merchant(self, db):
        """Valid QR token should resolve to merchant and campaign"""
        # Create test merchant
        merchant = Merchant(
            id="m1",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7
        )
        db.add(merchant)
        db.commit()
        
        # Create offer code
        offer_code = MerchantOfferCode(
            id="code1",
            merchant_id="m1",
            code="DOM-TEST-1234",
            amount_cents=500,
            is_redeemed=False,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(offer_code)
        db.commit()
        
        # Resolve token
        result = resolve_qr_token(db, "DOM-TEST-1234")
        
        assert result is not None
        assert result["merchant_id"] == "m1"
        assert result["merchant_name"] == "Test Merchant"
        assert result["code"] == "DOM-TEST-1234"
        assert result["amount_cents"] == 500
        assert result["is_redeemed"] is False
    
    def test_invalid_token_returns_none(self, db):
        """Invalid QR token should return None"""
        result = resolve_qr_token(db, "INVALID-CODE")
        assert result is None


class TestCheckCodeStatus:
    """Test code status checking"""
    
    def test_valid_code_status(self, db):
        """Valid, unredeemed code should return valid status"""
        merchant = Merchant(id="m1", name="Test", lat=30.4, lng=-97.7)
        db.add(merchant)
        db.commit()
        
        offer_code = MerchantOfferCode(
            id="code1",
            merchant_id="m1",
            code="VALID-CODE-123",
            amount_cents=500,
            is_redeemed=False,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(offer_code)
        db.commit()
        
        result = check_code_status(db, "VALID-CODE-123")
        
        assert result["status"] == "valid"
        assert result["valid"] is True
        assert result["merchant_id"] == "m1"
        assert result["amount_cents"] == 500
    
    def test_redeemed_code_status(self, db):
        """Redeemed code should return redeemed status"""
        merchant = Merchant(id="m2", name="Test", lat=30.4, lng=-97.7)
        db.add(merchant)
        db.commit()
        
        offer_code = MerchantOfferCode(
            id="code2",
            merchant_id="m2",
            code="REDEEMED-CODE",
            amount_cents=500,
            is_redeemed=True,  # Already redeemed
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(offer_code)
        db.commit()
        
        result = check_code_status(db, "REDEEMED-CODE")
        
        assert result["status"] == "redeemed"
        assert result["valid"] is False
        assert "error" in result
    
    def test_expired_code_status(self, db):
        """Expired code should return expired status"""
        merchant = Merchant(id="m3", name="Test", lat=30.4, lng=-97.7)
        db.add(merchant)
        db.commit()
        
        offer_code = MerchantOfferCode(
            id="code3",
            merchant_id="m3",
            code="EXPIRED-CODE",
            amount_cents=500,
            is_redeemed=False,
            expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
        )
        db.add(offer_code)
        db.commit()
        
        result = check_code_status(db, "EXPIRED-CODE")
        
        assert result["status"] == "expired"
        assert result["valid"] is False
        assert "error" in result
    
    def test_not_found_code_status(self, db):
        """Non-existent code should return not_found status"""
        result = check_code_status(db, "NONEXISTENT-CODE")
        
        assert result["status"] == "not_found"
        assert result["valid"] is False
        assert "error" in result


