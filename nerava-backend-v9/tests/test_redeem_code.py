"""
Tests for Code Redemption API

Tests cover:
- Happy path redemption
- Double redemption error
- Expired code error
- Wrong merchant error
- Code not found error
- Insufficient balance error
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models_while_you_charge import Merchant, MerchantOfferCode
from app.services.codes import generate_code, store_code
from app.services.merchant_balance import credit_balance, get_balance


# ============================================
# API Tests
# ============================================

def test_redeem_code_happy_path(client: TestClient, db: Session):
    """Test successful code redemption - happy path"""
    # Create merchant
    merchant = Merchant(
        id="m_redeem_001",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266,
        category="coffee"
    )
    db.add(merchant)
    db.commit()
    
    # Set merchant balance to 10000 cents
    credit_balance(db, "m_redeem_001", 10000, "initial_deposit")
    db.commit()
    
    # Generate and store a code worth 2500 cents
    code = generate_code("m_redeem_001", db)
    store_code(db, code, "m_redeem_001", 2500)
    db.commit()
    
    # Redeem the code via API
    response = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": code,
            "merchant_id": "m_redeem_001"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["redeemed_cents"] == 2500
    assert data["balance_after"] == 7500  # 10000 - 2500
    assert data["code"] == code
    assert data["merchant_id"] == "m_redeem_001"
    
    # Verify code is marked as redeemed
    from app.services.codes import fetch_code
    redeemed_code = fetch_code(db, code)
    assert redeemed_code.is_redeemed is True
    
    # Verify balance was debited
    balance = get_balance(db, "m_redeem_001")
    assert balance.balance_cents == 7500


def test_redeem_code_twice_error(client: TestClient, db: Session):
    """Test that redeeming the same code twice returns an error"""
    # Create merchant
    merchant = Merchant(
        id="m_redeem_002",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Set balance and create code
    credit_balance(db, "m_redeem_002", 10000, "initial")
    code = generate_code("m_redeem_002", db)
    store_code(db, code, "m_redeem_002", 2000)
    db.commit()
    
    # First redemption should succeed
    response1 = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": code,
            "merchant_id": "m_redeem_002"
        }
    )
    assert response1.status_code == 200
    
    # Second redemption should fail
    response2 = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": code,
            "merchant_id": "m_redeem_002"
        }
    )
    
    assert response2.status_code == 400
    assert "already been redeemed" in response2.json()["detail"]


def test_redeem_code_expired_error(client: TestClient, db: Session):
    """Test that redeeming an expired code returns an error"""
    # Create merchant
    merchant = Merchant(
        id="m_redeem_003",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    credit_balance(db, "m_redeem_003", 10000, "initial")
    
    # Create a code with past expiration
    code = generate_code("m_redeem_003", db)
    import uuid
    expired_code = MerchantOfferCode(
        id=str(uuid.uuid4()),
        merchant_id="m_redeem_003",
        code=code,
        amount_cents=1500,
        is_redeemed=False,
        expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
    )
    db.add(expired_code)
    db.commit()
    
    # Try to redeem expired code
    response = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": code,
            "merchant_id": "m_redeem_003"
        }
    )
    
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


def test_redeem_code_wrong_merchant_error(client: TestClient, db: Session):
    """Test that redeeming a code with wrong merchant_id returns an error"""
    # Create two merchants
    merchant1 = Merchant(
        id="m_redeem_004",
        name="Merchant 1",
        lat=30.4021,
        lng=-97.7266
    )
    merchant2 = Merchant(
        id="m_redeem_005",
        name="Merchant 2",
        lat=30.4030,
        lng=-97.7260
    )
    db.add(merchant1)
    db.add(merchant2)
    db.commit()
    
    credit_balance(db, "m_redeem_004", 10000, "initial")
    credit_balance(db, "m_redeem_005", 10000, "initial")
    
    # Create code for merchant1
    code = generate_code("m_redeem_004", db)
    store_code(db, code, "m_redeem_004", 1000)
    db.commit()
    
    # Try to redeem with merchant2's ID
    response = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": code,
            "merchant_id": "m_redeem_005"  # Wrong merchant
        }
    )
    
    assert response.status_code == 403
    assert "does not belong to merchant" in response.json()["detail"]


def test_redeem_code_not_found_error(client: TestClient):
    """Test that redeeming a non-existent code returns 404"""
    response = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": "NON-EX-0000",
            "merchant_id": "m_redeem_006"
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_redeem_code_insufficient_balance(client: TestClient, db: Session):
    """Test that redeeming with insufficient balance returns an error"""
    # Create merchant with low balance
    merchant = Merchant(
        id="m_redeem_007",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Set balance to only 500 cents
    credit_balance(db, "m_redeem_007", 500, "initial")
    
    # Create code worth 2000 cents (more than balance)
    code = generate_code("m_redeem_007", db)
    store_code(db, code, "m_redeem_007", 2000)
    db.commit()
    
    # Try to redeem
    response = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": code,
            "merchant_id": "m_redeem_007"
        }
    )
    
    assert response.status_code == 400
    assert "Insufficient balance" in response.json()["detail"]


def test_redeem_code_creates_reward_event(client: TestClient, db: Session):
    """Test that redemption creates a RewardEvent for reporting"""
    from app.models_extra import RewardEvent
    
    # Create merchant
    merchant = Merchant(
        id="m_redeem_008",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    credit_balance(db, "m_redeem_008", 10000, "initial")
    
    # Generate and store code
    code = generate_code("m_redeem_008", db)
    store_code(db, code, "m_redeem_008", 3000)
    db.commit()
    
    # Count RewardEvents before redemption
    events_before = db.query(RewardEvent).filter(
        RewardEvent.source == "MERCHANT_CODE_REDEMPTION"
    ).count()
    
    # Redeem code
    response = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": code,
            "merchant_id": "m_redeem_008"
        }
    )
    
    assert response.status_code == 200
    
    # Count RewardEvents after redemption
    events_after = db.query(RewardEvent).filter(
        RewardEvent.source == "MERCHANT_CODE_REDEMPTION"
    ).count()
    
    # Should have created one new RewardEvent
    assert events_after == events_before + 1
    
    # Verify the RewardEvent details
    reward_event = db.query(RewardEvent).filter(
        RewardEvent.source == "MERCHANT_CODE_REDEMPTION",
        RewardEvent.meta.contains({"code": code})
    ).first()
    
    assert reward_event is not None
    assert reward_event.gross_cents == 3000
    assert reward_event.user_id == f"merchant:m_redeem_008"
    assert reward_event.meta["code"] == code
    assert reward_event.meta["merchant_id"] == "m_redeem_008"


def test_redeem_code_validates_all_conditions(client: TestClient, db: Session):
    """Test that all validation checks work together"""
    # Create merchant with sufficient balance
    merchant = Merchant(
        id="m_redeem_009",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    credit_balance(db, "m_redeem_009", 10000, "initial")
    
    # Create valid, unredeemed code
    code = generate_code("m_redeem_009", db)
    store_code(db, code, "m_redeem_009", 2000)
    db.commit()
    
    # Verify code is valid before redemption
    from app.services.codes import fetch_code, is_code_valid
    offer_code = fetch_code(db, code)
    assert is_code_valid(offer_code) is True
    assert offer_code.is_redeemed is False
    
    # Redeem code
    response = client.post(
        "/v1/pilot/redeem_code",
        json={
            "code": code,
            "merchant_id": "m_redeem_009"
        }
    )
    
    assert response.status_code == 200
    
    # Verify code is now invalid after redemption
    db.refresh(offer_code)
    assert offer_code.is_redeemed is True
    assert is_code_valid(offer_code) is False

