"""
Tests for Merchant Offer Code Service and API

Tests cover:
- Code generation
- Code uniqueness
- Expiration handling
- Fetch code
- Code validation
- API endpoint
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models_while_you_charge import Merchant, MerchantOfferCode
from app.services.codes import (
    generate_code,
    store_code,
    fetch_code,
    is_code_valid,
    DEFAULT_EXPIRATION_DAYS
)


# ============================================
# Service Tests
# ============================================

def test_generate_code(db: Session):
    """Test that generate_code creates a valid code format"""
    # Create a test merchant
    merchant = Merchant(
        id="m_code_001",
        name="Starbucks",
        lat=30.4021,
        lng=-97.7266,
        category="coffee"
    )
    db.add(merchant)
    db.commit()
    
    # Generate code
    code = generate_code("m_code_001", db)
    
    # Check format: PREFIX-MERCHANT-####
    assert code is not None
    assert "-" in code
    parts = code.split("-")
    assert len(parts) == 3
    assert parts[0] == "DOM"  # Domain hub prefix
    assert parts[1] == "SB"  # Starbucks abbreviation
    assert len(parts[2]) == 4  # 4-digit number
    assert parts[2].isdigit()


def test_generate_code_merchant_not_found(db: Session):
    """Test that generate_code raises error for non-existent merchant"""
    with pytest.raises(ValueError, match="Merchant.*not found"):
        generate_code("nonexistent_merchant", db)


def test_code_uniqueness(db: Session):
    """Test that generate_code produces unique codes"""
    merchant = Merchant(
        id="m_code_002",
        name="Target",
        lat=30.4021,
        lng=-97.7266,
        category="retail"
    )
    db.add(merchant)
    db.commit()
    
    # Generate multiple codes
    codes = set()
    for _ in range(10):
        code = generate_code("m_code_002", db)
        codes.add(code)
    
    # All codes should be unique
    assert len(codes) == 10


def test_store_code(db: Session):
    """Test that store_code saves a code correctly"""
    merchant = Merchant(
        id="m_code_003",
        name="Whole Foods",
        lat=30.4021,
        lng=-97.7266,
        category="grocery"
    )
    db.add(merchant)
    db.commit()
    
    # Generate and store code
    code = generate_code("m_code_003", db)
    offer_code = store_code(db, code, "m_code_003", 2500)
    
    assert offer_code.code == code
    assert offer_code.merchant_id == "m_code_003"
    assert offer_code.amount_cents == 2500
    assert offer_code.is_redeemed is False
    assert offer_code.expires_at is not None
    
    # Check expiration is roughly 30 days from now
    expected_expiration = datetime.utcnow() + timedelta(days=DEFAULT_EXPIRATION_DAYS)
    time_diff = abs((offer_code.expires_at - expected_expiration).total_seconds())
    assert time_diff < 60  # Within 1 minute


def test_store_code_custom_expiration(db: Session):
    """Test store_code with custom expiration"""
    merchant = Merchant(
        id="m_code_004",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    code = generate_code("m_code_004", db)
    offer_code = store_code(db, code, "m_code_004", 1000, expiration_days=7)
    
    expected_expiration = datetime.utcnow() + timedelta(days=7)
    time_diff = abs((offer_code.expires_at - expected_expiration).total_seconds())
    assert time_diff < 60


def test_store_code_duplicate_raises_error(db: Session):
    """Test that storing duplicate code raises error"""
    merchant = Merchant(
        id="m_code_005",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    code = generate_code("m_code_005", db)
    store_code(db, code, "m_code_005", 1000)
    
    # Try to store same code again
    with pytest.raises(ValueError, match="already exists"):
        store_code(db, code, "m_code_005", 2000)


def test_fetch_code(db: Session):
    """Test that fetch_code retrieves a stored code"""
    merchant = Merchant(
        id="m_code_006",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    # Generate and store code
    code = generate_code("m_code_006", db)
    stored = store_code(db, code, "m_code_006", 1500)
    
    # Fetch code
    fetched = fetch_code(db, code)
    
    assert fetched is not None
    assert fetched.id == stored.id
    assert fetched.code == code
    assert fetched.merchant_id == "m_code_006"
    assert fetched.amount_cents == 1500


def test_fetch_code_not_found(db: Session):
    """Test that fetch_code returns None for non-existent code"""
    fetched = fetch_code(db, "NON-EX-0000")
    assert fetched is None


def test_is_code_valid_not_redeemed(db: Session):
    """Test that is_code_valid returns True for valid unredeemed code"""
    merchant = Merchant(
        id="m_code_007",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    code = generate_code("m_code_007", db)
    offer_code = store_code(db, code, "m_code_007", 1000)
    
    assert is_code_valid(offer_code) is True


def test_is_code_valid_redeemed(db: Session):
    """Test that is_code_valid returns False for redeemed code"""
    merchant = Merchant(
        id="m_code_008",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    code = generate_code("m_code_008", db)
    offer_code = store_code(db, code, "m_code_008", 1000)
    
    # Mark as redeemed
    offer_code.is_redeemed = True
    db.commit()
    db.refresh(offer_code)
    
    assert is_code_valid(offer_code) is False


def test_is_code_valid_expired(db: Session):
    """Test that is_code_valid returns False for expired code"""
    merchant = Merchant(
        id="m_code_009",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    code = generate_code("m_code_009", db)
    
    # Store with past expiration
    offer_code = MerchantOfferCode(
        id="test_id_009",
        merchant_id="m_code_009",
        code=code,
        amount_cents=1000,
        is_redeemed=False,
        expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
    )
    db.add(offer_code)
    db.commit()
    db.refresh(offer_code)
    
    assert is_code_valid(offer_code) is False


def test_code_expiration_future(db: Session):
    """Test that codes with future expiration are valid"""
    merchant = Merchant(
        id="m_code_010",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266
    )
    db.add(merchant)
    db.commit()
    
    code = generate_code("m_code_010", db)
    
    # Store with future expiration
    offer_code = MerchantOfferCode(
        id="test_id_010",
        merchant_id="m_code_010",
        code=code,
        amount_cents=1000,
        is_redeemed=False,
        expires_at=datetime.utcnow() + timedelta(days=5)  # Expires in 5 days
    )
    db.add(offer_code)
    db.commit()
    db.refresh(offer_code)
    
    assert is_code_valid(offer_code) is True


def test_code_format_variations(db: Session):
    """Test code generation with different merchant name formats"""
    # Test with multi-word merchant name
    merchant1 = Merchant(
        id="m_code_011",
        name="Neiman Marcus",
        lat=30.4021,
        lng=-97.7266,
        category="retail"
    )
    db.add(merchant1)
    db.commit()
    
    code1 = generate_code("m_code_011", db)
    assert code1.startswith("DOM-")
    
    # Test with single word merchant name
    merchant2 = Merchant(
        id="m_code_012",
        name="Gap",
        lat=30.4021,
        lng=-97.7266,
        category="retail"
    )
    db.add(merchant2)
    db.commit()
    
    code2 = generate_code("m_code_012", db)
    assert code2.startswith("DOM-")


# ============================================
# API Tests
# ============================================

def test_api_create_merchant_offer(client: TestClient, db: Session):
    """Test POST /v1/pilot/merchant_offer endpoint"""
    # Create merchant
    merchant = Merchant(
        id="m_api_code_001",
        name="Starbucks",
        lat=30.4021,
        lng=-97.7266,
        category="coffee"
    )
    db.add(merchant)
    db.commit()
    
    # Create offer via API
    response = client.post(
        "/v1/pilot/merchant_offer",
        json={
            "merchant_id": "m_api_code_001",
            "amount_cents": 5000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "code" in data
    assert data["amount_cents"] == 5000
    assert data["merchant_id"] == "m_api_code_001"
    assert "expires_at" in data
    
    # Verify code format
    code = data["code"]
    assert "-" in code
    parts = code.split("-")
    assert len(parts) == 3
    assert parts[0] == "DOM"
    assert parts[1] == "SB"


def test_api_create_merchant_offer_merchant_not_found(client: TestClient):
    """Test API returns 400 for non-existent merchant"""
    response = client.post(
        "/v1/pilot/merchant_offer",
        json={
            "merchant_id": "nonexistent",
            "amount_cents": 1000
        }
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_api_create_merchant_offer_creates_unique_codes(client: TestClient, db: Session):
    """Test that API creates unique codes for multiple requests"""
    merchant = Merchant(
        id="m_api_code_002",
        name="Target",
        lat=30.4021,
        lng=-97.7266,
        category="retail"
    )
    db.add(merchant)
    db.commit()
    
    codes = set()
    for _ in range(5):
        response = client.post(
            "/v1/pilot/merchant_offer",
            json={
                "merchant_id": "m_api_code_002",
                "amount_cents": 1000
            }
        )
        assert response.status_code == 200
        codes.add(response.json()["code"])
    
    # All codes should be unique
    assert len(codes) == 5


def test_api_offer_code_expiration(client: TestClient, db: Session):
    """Test that API returns expiration date"""
    merchant = Merchant(
        id="m_api_code_003",
        name="Whole Foods",
        lat=30.4021,
        lng=-97.7266,
        category="grocery"
    )
    db.add(merchant)
    db.commit()
    
    response = client.post(
        "/v1/pilot/merchant_offer",
        json={
            "merchant_id": "m_api_code_003",
            "amount_cents": 2000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify expires_at is a valid ISO datetime string
    expires_at = data["expires_at"]
    assert expires_at is not None
    # Parse to verify it's valid
    parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    assert parsed > datetime.utcnow()  # Should be in the future

