"""
Tests for Nova facade layer in wallet and reward endpoints.

Verifies that Nova conversion is properly applied to wallet balances,
transaction history, and reward amounts without modifying underlying DB schema.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main_simple import app
from app.db import get_db, SessionLocal, Base, engine
from app.models_extra import CreditLedger, RewardEvent, IncentiveRule, Follow, FollowerShare, CommunityPeriod
from app.services.nova import cents_to_nova
import uuid

# Import all models to ensure they're registered with Base
from app import models, models_extra, models_while_you_charge, models_demo

client = TestClient(app)


@pytest.fixture
def db():
    """Create a test database session."""
    # Import all models to ensure they're registered with Base
    from app import models, models_extra, models_while_you_charge, models_demo
    
    # Ensure tables exist (they should be created by conftest, but make sure)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def seeded_wallet(db: Session):
    """
    Fixture that seeds wallet with ledger entries: +100, -40.
    
    Returns the user_id and expected balance.
    """
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    # Add ledger entries: +100, -40
    entry1 = CreditLedger(
        user_ref=user_id,
        cents=100,
        reason="TEST_CREDIT",
        meta={"test": True}
    )
    entry2 = CreditLedger(
        user_ref=user_id,
        cents=-40,
        reason="TEST_DEBIT",
        meta={"test": True}
    )
    
    db.add(entry1)
    db.add(entry2)
    db.commit()
    
    # Expected balance: 100 - 40 = 60 cents
    expected_balance_cents = 60
    
    return {
        "user_id": user_id,
        "expected_balance_cents": expected_balance_cents,
        "expected_nova_balance": cents_to_nova(expected_balance_cents)
    }


def test_wallet_returns_nova_balance(seeded_wallet, db: Session):
    """Test 1: /v1/wallet returns nova_balance == balance_cents"""
    user_id = seeded_wallet["user_id"]
    expected_balance_cents = seeded_wallet["expected_balance_cents"]
    expected_nova_balance = seeded_wallet["expected_nova_balance"]
    
    response = client.get("/v1/wallet", params={"user_id": user_id})
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify both fields are present
    assert "balance_cents" in data
    assert "nova_balance" in data
    
    # Verify values match expected
    assert data["balance_cents"] == expected_balance_cents
    assert data["nova_balance"] == expected_nova_balance
    
    # Verify Nova balance equals cents balance (1:1 conversion currently)
    assert data["nova_balance"] == data["balance_cents"]


def test_wallet_history_returns_nova_delta(seeded_wallet, db: Session):
    """Test 2: /v1/wallet/history entries have nova_delta == cents_delta"""
    user_id = seeded_wallet["user_id"]
    
    response = client.get("/v1/wallet/history", params={"user_id": user_id})
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 2 entries
    assert len(data) == 2
    
    # Verify each entry has both cents and nova_delta
    for entry in data:
        assert "cents" in entry
        assert "nova_delta" in entry
        assert "reason" in entry
        assert "ts" in entry
        
        # Verify nova_delta matches cents (1:1 conversion currently)
        assert entry["nova_delta"] == entry["cents"]
    
    # Verify entries are in descending order (most recent first)
    assert data[0]["cents"] == -40  # Most recent: debit
    assert data[1]["cents"] == 100  # Older: credit
    
    # Verify Nova deltas match
    assert data[0]["nova_delta"] == -40
    assert data[1]["nova_delta"] == 100


def test_reward_endpoint_returns_nova_awarded():
    """Test 3: Reward endpoint contains nova_awarded"""
    # Test the /v1/incentives/award endpoint
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    reward_cents = 150
    
    response = client.post(
        "/v1/incentives/award",
        params={
            "user_id": user_id,
            "cents": reward_cents,
            "source": "TEST"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify reward fields are present
    assert "gross_cents" in data
    assert "net_cents" in data
    assert "nova_awarded" in data
    assert "user_id" in data
    assert "source" in data
    
    # Verify nova_awarded matches net_cents (1:1 conversion currently)
    # Note: net_cents is gross minus community pool (10%)
    expected_nova = cents_to_nova(data["net_cents"])
    assert data["nova_awarded"] == expected_nova
    
    # Verify user_id matches
    assert data["user_id"] == user_id
    assert data["source"] == "TEST"


def test_wallet_summary_includes_nova(seeded_wallet, db: Session):
    """Test that /v1/wallet/summary includes Nova fields"""
    user_id = seeded_wallet["user_id"]
    
    response = client.get("/v1/wallet/summary", params={"user_id": user_id})
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify balance fields
    assert "balance_cents" in data
    assert "nova_balance" in data
    assert data["nova_balance"] == cents_to_nova(data["balance_cents"])
    
    # Verify history entries have nova_delta
    assert "history" in data
    assert isinstance(data["history"], list)
    
    for entry in data["history"]:
        assert "cents" in entry
        assert "nova_delta" in entry
        assert entry["nova_delta"] == cents_to_nova(entry["cents"])


def test_wallet_credit_returns_nova_balance():
    """Test that wallet credit endpoint returns nova_balance"""
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    credit_cents = 250
    
    response = client.post(
        "/v1/wallet/credit_qs",
        params={
            "user_id": user_id,
            "cents": credit_cents
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify both fields are present
    assert "new_balance_cents" in data
    assert "nova_balance" in data
    
    # Verify values match
    assert data["new_balance_cents"] == credit_cents
    assert data["nova_balance"] == cents_to_nova(credit_cents)
    assert data["nova_balance"] == data["new_balance_cents"]


def test_incentive_award_off_peak_returns_nova():
    """Test that /v1/incentives/award_off_peak returns nova fields"""
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    response = client.post(
        "/v1/incentives/award_off_peak",
        params={
            "user_id": user_id,
            "cents": 100
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify Nova fields are present
    assert "awarded_cents" in data
    assert "nova_awarded" in data
    
    # Verify Nova values match cents (1:1 conversion)
    assert data["nova_awarded"] == cents_to_nova(data["awarded_cents"])
    
    # If awarded, verify balance fields are present
    if data.get("awarded_cents", 0) > 0:
        assert "balance_cents" in data
        assert "nova_balance" in data
        assert data["nova_balance"] == cents_to_nova(data["balance_cents"])

