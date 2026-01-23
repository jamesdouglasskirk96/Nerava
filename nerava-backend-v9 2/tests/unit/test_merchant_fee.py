"""
Unit tests for Merchant Fee service
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch
from app.services.merchant_fee import record_merchant_fee
from app.models.domain import MerchantFeeLedger


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = Mock()
    
    # Mock query result (no existing ledger)
    db.query.return_value.filter.return_value.first.return_value = None
    
    # Mock add and commit
    db.add = Mock()
    db.flush = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    
    return db


class TestRecordMerchantFee:
    """Tests for record_merchant_fee"""
    
    def test_create_new_ledger(self, mock_db):
        """Test creating a new ledger row"""
        ts = datetime(2025, 1, 15, 10, 30, 0)
        
        fee = record_merchant_fee(mock_db, "merchant-1", 300, ts)
        
        # Should calculate 15% of 300 = 45
        assert fee == 45
        
        # Should create new ledger
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Check the ledger object
        ledger = mock_db.add.call_args[0][0]
        assert ledger.merchant_id == "merchant-1"
        assert ledger.period_start == date(2025, 1, 1)
        assert ledger.nova_redeemed_cents == 300
        assert ledger.fee_cents == 45
        assert ledger.status == "accruing"
    
    def test_update_existing_ledger(self, mock_db):
        """Test updating an existing ledger row"""
        # Create existing ledger
        existing_ledger = MerchantFeeLedger(
            id="ledger-1",
            merchant_id="merchant-1",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            nova_redeemed_cents=200,
            fee_cents=30,
            status="accruing"
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_ledger
        
        ts = datetime(2025, 1, 15, 10, 30, 0)
        
        fee = record_merchant_fee(mock_db, "merchant-1", 300, ts)
        
        # Should calculate incremental fee: 15% of 300 = 45
        assert fee == 45
        
        # Should update existing ledger
        assert existing_ledger.nova_redeemed_cents == 500  # 200 + 300
        assert existing_ledger.fee_cents == 75  # 15% of 500
        assert existing_ledger.status == "accruing"
        
        mock_db.commit.assert_called_once()
    
    def test_preserve_invoiced_status(self, mock_db):
        """Test that invoiced status is preserved"""
        # Create existing ledger with invoiced status
        existing_ledger = MerchantFeeLedger(
            id="ledger-1",
            merchant_id="merchant-1",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            nova_redeemed_cents=200,
            fee_cents=30,
            status="invoiced"
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_ledger
        
        ts = datetime(2025, 1, 15, 10, 30, 0)
        
        fee = record_merchant_fee(mock_db, "merchant-1", 300, ts)
        
        # Status should remain "invoiced"
        assert existing_ledger.status == "invoiced"
        assert fee == 45  # Incremental fee still calculated
    
    def test_preserve_paid_status(self, mock_db):
        """Test that paid status is preserved"""
        # Create existing ledger with paid status
        existing_ledger = MerchantFeeLedger(
            id="ledger-1",
            merchant_id="merchant-1",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            nova_redeemed_cents=200,
            fee_cents=30,
            status="paid"
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_ledger
        
        ts = datetime(2025, 1, 15, 10, 30, 0)
        
        fee = record_merchant_fee(mock_db, "merchant-1", 300, ts)
        
        # Status should remain "paid"
        assert existing_ledger.status == "paid"
        assert fee == 45  # Incremental fee still calculated
    
    def test_fee_calculation_rounding(self, mock_db):
        """Test that fee calculation rounds correctly"""
        ts = datetime(2025, 1, 15, 10, 30, 0)
        
        # 333 cents * 0.15 = 49.95, should round to 50
        fee = record_merchant_fee(mock_db, "merchant-1", 333, ts)
        
        assert fee == 50
        
        ledger = mock_db.add.call_args[0][0]
        assert ledger.fee_cents == 50

