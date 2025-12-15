"""
Unit tests for Merchant Billing Summary
"""
import pytest
from datetime import datetime
from calendar import monthrange
from app.services.merchant_analytics import merchant_billing_summary
from app.models.domain import DomainMerchant, MerchantRedemption
from app.models import User


class TestMerchantBilling:
    """Test merchant billing summary functions"""
    
    def test_billing_summary_no_redemptions(self, db):
        """Should return zeros for merchant with no redemptions"""
        merchant = DomainMerchant(
            id="merchant_billing_1",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0
        )
        db.add(merchant)
        db.commit()
        
        summary = merchant_billing_summary(db, "merchant_billing_1")
        
        assert summary["nova_redeemed_cents"] == 0
        assert summary["platform_fee_cents"] == 0
        assert summary["platform_fee_bps"] == 1500  # 15%
        assert summary["status"] == "pending"
        assert summary["settlement_method"] == "invoice"
        assert "period_start" in summary
        assert "period_end" in summary
    
    def test_billing_summary_with_redemptions(self, db):
        """Should calculate platform fee correctly (15% of redeemed Nova)"""
        # Create merchant
        merchant = DomainMerchant(
            id="merchant_billing_2",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0
        )
        db.add(merchant)
        
        # Create user/driver
        user = User(id=10, email="driver@test.com", display_name="Driver")
        db.add(user)
        db.commit()
        
        # Create redemption with nova_spent_cents=100 (should result in $0.15 platform fee)
        redemption = MerchantRedemption(
            id="redemption_billing_1",
            merchant_id="merchant_billing_2",
            driver_user_id=10,
            qr_token="token1",
            order_total_cents=2000,
            discount_cents=100,
            nova_spent_cents=100,  # $1.00 of Nova redeemed
            created_at=datetime.utcnow()
        )
        db.add(redemption)
        db.commit()
        
        summary = merchant_billing_summary(db, "merchant_billing_2")
        
        # Should have $1.00 redeemed
        assert summary["nova_redeemed_cents"] == 100
        
        # Platform fee should be 15% = $0.15
        assert summary["platform_fee_cents"] == 15
        
        # Platform fee BPS should be 1500 (15%)
        assert summary["platform_fee_bps"] == 1500
        
        assert summary["status"] == "pending"
        assert summary["settlement_method"] == "invoice"
    
    def test_billing_summary_multiple_redemptions(self, db):
        """Should aggregate multiple redemptions correctly"""
        merchant = DomainMerchant(
            id="merchant_billing_3",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0
        )
        db.add(merchant)
        
        user = User(id=11, email="driver@test.com", display_name="Driver")
        db.add(user)
        db.commit()
        
        # Create multiple redemptions
        redemption1 = MerchantRedemption(
            id="redemption_billing_2",
            merchant_id="merchant_billing_3",
            driver_user_id=11,
            qr_token="token1",
            order_total_cents=2000,
            discount_cents=100,
            nova_spent_cents=100,  # $1.00
            created_at=datetime.utcnow()
        )
        redemption2 = MerchantRedemption(
            id="redemption_billing_3",
            merchant_id="merchant_billing_3",
            driver_user_id=11,
            qr_token="token2",
            order_total_cents=3000,
            discount_cents=100,
            nova_spent_cents=100,  # $1.00
            created_at=datetime.utcnow()
        )
        db.add(redemption1)
        db.add(redemption2)
        db.commit()
        
        summary = merchant_billing_summary(db, "merchant_billing_3")
        
        # Total should be $2.00
        assert summary["nova_redeemed_cents"] == 200
        
        # Platform fee should be 15% of $2.00 = $0.30
        assert summary["platform_fee_cents"] == 30
    
    def test_billing_summary_period_defaults_to_current_month(self, db):
        """Should default to current calendar month"""
        merchant = DomainMerchant(
            id="merchant_billing_4",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0
        )
        db.add(merchant)
        db.commit()
        
        summary = merchant_billing_summary(db, "merchant_billing_4")
        
        # Check that period is current month
        now = datetime.utcnow()
        expected_start = datetime(now.year, now.month, 1).strftime("%Y-%m-%d")
        last_day = monthrange(now.year, now.month)[1]
        expected_end = datetime(now.year, now.month, last_day).strftime("%Y-%m-%d")
        
        assert summary["period_start"] == expected_start
        assert summary["period_end"] == expected_end

