"""
Tests for Merchant Balance Service and API

Tests cover:
- Initial balance fetch
- Credit operations
- Debit operations
- Ledger logging
- Insufficient balance errors
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.models_while_you_charge import Merchant, MerchantBalance, MerchantBalanceLedger
from app.services.merchant_balance import get_balance, credit_balance, debit_balance


def test_get_balance_creates_if_missing(db: Session):
    """Test that get_balance creates a zero-balance record if missing"""
    # Create a test merchant
    merchant = Merchant(
        id="m_test_001",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266,
        category="coffee"
    )
    db.add(merchant)
    db.commit()
    
    # Get balance (should create zero balance)
    balance = get_balance(db, "m_test_001")
    
    assert balance is not None
    assert balance.merchant_id == "m_test_001"
    assert balance.balance_cents == 0
    assert balance.id is not None
    
    # Verify it was persisted
    db.refresh(balance)
    stored = db.query(MerchantBalance).filter(MerchantBalance.merchant_id == "m_test_001").first()
    assert stored is not None
    assert stored.balance_cents == 0


def test_get_balance_returns_existing(db: Session):
    """Test that get_balance returns existing balance"""
    # Create merchant and balance
    merchant = Merchant(
        id="m_test_002",
        name="Test Merchant 2",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    
    balance = MerchantBalance(
        id="bal_test_002",
        merchant_id="m_test_002",
        balance_cents=5000
    )
    db.add(balance)
    db.commit()
    
    # Get balance
    result = get_balance(db, "m_test_002")
    
    assert result is not None
    assert result.merchant_id == "m_test_002"
    assert result.balance_cents == 5000


def test_credit_balance_increases_balance(db: Session):
    """Test that credit_balance increases balance correctly"""
    # Create merchant
    merchant = Merchant(
        id="m_test_003",
        name="Test Merchant 3",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Initial balance is 0
    balance = get_balance(db, "m_test_003")
    assert balance.balance_cents == 0
    
    # Credit 1000 cents
    updated = credit_balance(db, "m_test_003", 1000, "initial_deposit")
    
    assert updated.balance_cents == 1000
    
    # Verify ledger entry
    ledger = db.query(MerchantBalanceLedger).filter(
        MerchantBalanceLedger.merchant_id == "m_test_003"
    ).first()
    
    assert ledger is not None
    assert ledger.delta_cents == 1000
    assert ledger.reason == "initial_deposit"


def test_credit_balance_with_session_id(db: Session):
    """Test credit with session_id reference"""
    merchant = Merchant(
        id="m_test_004",
        name="Test Merchant 4",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    credit_balance(db, "m_test_004", 500, "session_reward", session_id="session_123")
    
    ledger = db.query(MerchantBalanceLedger).filter(
        MerchantBalanceLedger.merchant_id == "m_test_004"
    ).first()
    
    assert ledger.session_id == "session_123"


def test_debit_balance_decreases_balance(db: Session):
    """Test that debit_balance decreases balance correctly"""
    merchant = Merchant(
        id="m_test_005",
        name="Test Merchant 5",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Set initial balance
    credit_balance(db, "m_test_005", 5000, "initial_deposit")
    
    # Debit 2000 cents
    updated = debit_balance(db, "m_test_005", 2000, "discount_issued")
    
    assert updated.balance_cents == 3000
    
    # Verify ledger entry (negative delta)
    ledger = db.query(MerchantBalanceLedger).filter(
        MerchantBalanceLedger.merchant_id == "m_test_005",
        MerchantBalanceLedger.delta_cents < 0
    ).first()
    
    assert ledger is not None
    assert ledger.delta_cents == -2000
    assert ledger.reason == "discount_issued"


def test_debit_insufficient_balance(db: Session):
    """Test that debit fails with insufficient balance"""
    merchant = Merchant(
        id="m_test_006",
        name="Test Merchant 6",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Set balance to 1000
    credit_balance(db, "m_test_006", 1000, "initial_deposit")
    
    # Try to debit more than available
    with pytest.raises(ValueError, match="Insufficient balance"):
        debit_balance(db, "m_test_006", 2000, "discount_issued")


def test_credit_negative_amount_raises_error(db: Session):
    """Test that credit with negative amount raises error"""
    merchant = Merchant(
        id="m_test_007",
        name="Test Merchant 7",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    with pytest.raises(ValueError, match="amount_cents must be >= 0"):
        credit_balance(db, "m_test_007", -100, "invalid")


def test_debit_negative_amount_raises_error(db: Session):
    """Test that debit with negative amount raises error"""
    merchant = Merchant(
        id="m_test_008",
        name="Test Merchant 8",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    credit_balance(db, "m_test_008", 1000, "initial")
    
    with pytest.raises(ValueError, match="amount_cents must be >= 0"):
        debit_balance(db, "m_test_008", -100, "invalid")


def test_ledger_tracks_all_transactions(db: Session):
    """Test that all transactions are logged in ledger"""
    merchant = Merchant(
        id="m_test_009",
        name="Test Merchant 9",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Perform multiple operations
    credit_balance(db, "m_test_009", 5000, "deposit_1")
    credit_balance(db, "m_test_009", 2000, "deposit_2")
    debit_balance(db, "m_test_009", 1500, "payout_1")
    debit_balance(db, "m_test_009", 500, "payout_2")
    
    # Get all ledger entries
    entries = db.query(MerchantBalanceLedger).filter(
        MerchantBalanceLedger.merchant_id == "m_test_009"
    ).order_by(MerchantBalanceLedger.created_at).all()
    
    assert len(entries) == 4
    
    # Verify credits
    assert entries[0].delta_cents == 5000
    assert entries[0].reason == "deposit_1"
    assert entries[1].delta_cents == 2000
    assert entries[1].reason == "deposit_2"
    
    # Verify debits (negative)
    assert entries[2].delta_cents == -1500
    assert entries[2].reason == "payout_1"
    assert entries[3].delta_cents == -500
    assert entries[3].reason == "payout_2"
    
    # Final balance should be 5000
    balance = get_balance(db, "m_test_009")
    assert balance.balance_cents == 5000


# ============================================
# API Tests
# ============================================

def test_api_get_balance(client: TestClient, db: Session):
    """Test GET /v1/merchants/{id}/balance endpoint"""
    # Create merchant
    merchant = Merchant(
        id="m_api_001",
        name="API Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Set balance
    from app.services.merchant_balance import credit_balance
    credit_balance(db, "m_api_001", 3000, "test_setup")
    db.commit()
    
    # Call API
    response = client.get("/v1/merchants/m_api_001/balance")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["merchant_id"] == "m_api_001"
    assert data["balance_cents"] == 3000
    assert "created_at" in data
    assert "updated_at" in data


def test_api_get_balance_creates_if_missing(client: TestClient, db: Session):
    """Test that API creates zero balance if missing"""
    merchant = Merchant(
        id="m_api_002",
        name="API Test Merchant 2",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Call API (no balance exists yet)
    response = client.get("/v1/merchants/m_api_002/balance")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["merchant_id"] == "m_api_002"
    assert data["balance_cents"] == 0


def test_api_credit_balance(client: TestClient, db: Session):
    """Test POST /v1/merchants/{id}/credit endpoint"""
    merchant = Merchant(
        id="m_api_003",
        name="API Test Merchant 3",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Credit via API
    response = client.post(
        "/v1/merchants/m_api_003/credit",
        json={
            "amount_cents": 2500,
            "reason": "api_test_credit",
            "session_id": "session_test_123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["merchant_id"] == "m_api_003"
    assert data["balance_cents"] == 2500
    assert data["amount_credited"] == 2500
    assert data["reason"] == "api_test_credit"


def test_api_debit_balance(client: TestClient, db: Session):
    """Test POST /v1/merchants/{id}/debit endpoint"""
    merchant = Merchant(
        id="m_api_004",
        name="API Test Merchant 4",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Set initial balance
    from app.services.merchant_balance import credit_balance
    credit_balance(db, "m_api_004", 5000, "setup")
    db.commit()
    
    # Debit via API
    response = client.post(
        "/v1/merchants/m_api_004/debit",
        json={
            "amount_cents": 1800,
            "reason": "api_test_debit"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["merchant_id"] == "m_api_004"
    assert data["balance_cents"] == 3200  # 5000 - 1800
    assert data["amount_debited"] == 1800
    assert data["reason"] == "api_test_debit"


def test_api_debit_insufficient_balance(client: TestClient, db: Session):
    """Test that API returns 400 for insufficient balance"""
    merchant = Merchant(
        id="m_api_005",
        name="API Test Merchant 5",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Set balance to 500
    from app.services.merchant_balance import credit_balance
    credit_balance(db, "m_api_005", 500, "setup")
    db.commit()
    
    # Try to debit more
    response = client.post(
        "/v1/merchants/m_api_005/debit",
        json={
            "amount_cents": 1000,
            "reason": "insufficient_test"
        }
    )
    
    assert response.status_code == 400
    assert "Insufficient balance" in response.json()["detail"]


def test_api_credit_negative_amount(client: TestClient, db: Session):
    """Test that API rejects negative credit amounts"""
    merchant = Merchant(
        id="m_api_006",
        name="API Test Merchant 6",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    response = client.post(
        "/v1/merchants/m_api_006/credit",
        json={
            "amount_cents": -100,
            "reason": "invalid"
        }
    )
    
    # Should fail validation
    assert response.status_code == 422  # Validation error


def test_api_merchant_not_found(client: TestClient):
    """Test that API returns 404 for non-existent merchant"""
    response = client.get("/v1/merchants/nonexistent/balance")
    
    assert response.status_code == 404

