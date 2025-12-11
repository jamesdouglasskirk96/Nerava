"""
Unit tests for Merchant Reporting Service
"""
import pytest
from datetime import datetime, timedelta
from app.services.merchant_reporting import get_merchant_summary, get_shareable_stats
from app.models.domain import DomainMerchant, MerchantRedemption, DriverWallet
from app.models import User


class TestMerchantReporting:
    """Test merchant reporting functions"""
    
    def test_get_merchant_summary_no_redemptions(self, db):
        """Should return zeros for merchant with no redemptions"""
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
        
        summary = get_merchant_summary(db, "merchant_1")
        
        assert summary["total_redemptions"] == 0
        assert summary["total_discount_cents"] == 0
        assert summary["unique_driver_count"] == 0
        assert summary["last_7d_redemptions"] == 0
        assert summary["last_30d_redemptions"] == 0
        assert summary["avg_discount_cents"] == 0
    
    def test_get_merchant_summary_with_redemptions(self, db):
        """Should calculate correct summary stats"""
        # Create merchant
        merchant = DomainMerchant(
            id="merchant_2",
            name="Test Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0
        )
        db.add(merchant)
        
        # Create users/drivers
        user1 = User(id=1, email="driver1@test.com", display_name="Driver 1")
        user2 = User(id=2, email="driver2@test.com", display_name="Driver 2")
        db.add(user1)
        db.add(user2)
        db.commit()
        
        # Create redemptions
        redemption1 = MerchantRedemption(
            id="redemption_1",
            merchant_id="merchant_2",
            driver_user_id=1,
            qr_token="token1",
            order_total_cents=2000,
            discount_cents=300,
            nova_spent_cents=300,
            created_at=datetime.utcnow() - timedelta(days=5)  # 5 days ago
        )
        redemption2 = MerchantRedemption(
            id="redemption_2",
            merchant_id="merchant_2",
            driver_user_id=2,
            qr_token="token2",
            order_total_cents=1500,
            discount_cents=300,
            nova_spent_cents=300,
            created_at=datetime.utcnow() - timedelta(days=3)  # 3 days ago
        )
        redemption3 = MerchantRedemption(
            id="redemption_3",
            merchant_id="merchant_2",
            driver_user_id=1,  # Same driver as redemption1
            qr_token="token3",
            order_total_cents=1800,
            discount_cents=250,
            nova_spent_cents=250,
            created_at=datetime.utcnow() - timedelta(days=35)  # 35 days ago (outside 30d window)
        )
        db.add(redemption1)
        db.add(redemption2)
        db.add(redemption3)
        db.commit()
        
        summary = get_merchant_summary(db, "merchant_2")
        
        assert summary["total_redemptions"] == 3
        assert summary["total_discount_cents"] == 850  # 300 + 300 + 250
        assert summary["unique_driver_count"] == 2  # Two unique drivers
        assert summary["last_7d_redemptions"] == 2  # redemption1 and redemption2
        assert summary["last_30d_redemptions"] == 2  # redemption1 and redemption2
        assert summary["avg_discount_cents"] == pytest.approx(283.33, abs=0.01)
    
    def test_get_shareable_stats_with_redemptions(self, db):
        """Should generate shareable stat lines"""
        merchant = DomainMerchant(
            id="merchant_3",
            name="Eggman",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0
        )
        db.add(merchant)
        
        user = User(id=3, email="driver@test.com", display_name="Driver")
        db.add(user)
        db.commit()
        
        # Create recent redemptions
        for i in range(3):
            redemption = MerchantRedemption(
                id=f"redemption_{i}",
                merchant_id="merchant_3",
                driver_user_id=3,
                qr_token=f"token_{i}",
                order_total_cents=2000,
                discount_cents=300,
                nova_spent_cents=300,
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            db.add(redemption)
        db.commit()
        
        lines = get_shareable_stats(db, "merchant_3")
        
        assert len(lines) > 0
        assert any("EV driver" in line for line in lines)
        assert any("Eggman" in line for line in lines)
    
    def test_get_shareable_stats_no_redemptions(self, db):
        """Should return welcome message if no redemptions"""
        merchant = DomainMerchant(
            id="merchant_4",
            name="New Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0
        )
        db.add(merchant)
        db.commit()
        
        lines = get_shareable_stats(db, "merchant_4")
        
        assert len(lines) > 0
        assert any("Welcome" in line or "Nerava" in line for line in lines)

