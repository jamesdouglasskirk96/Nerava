"""Tests for Merchant Rewards: Request-to-Join, Reward Claims, Receipt Submissions."""
import pytest
from datetime import datetime, timedelta
from app.models.merchant_reward import (
    MerchantJoinRequest,
    RewardClaim,
    RewardClaimStatus,
    ReceiptSubmission,
    ReceiptStatus,
)
from app.services.merchant_reward_service import (
    create_join_request,
    get_join_request_count,
    user_has_requested,
    create_reward_claim,
    get_active_claims,
    get_claim_by_id,
    create_receipt_submission,
    get_merchant_reward_state,
)


# ---------------------------------------------------------------------------
# Request-to-Join Tests
# ---------------------------------------------------------------------------

def test_create_join_request(db, test_user):
    """Should create a join request."""
    req = create_join_request(
        db=db,
        driver_user_id=test_user.id,
        place_id="ChIJ_test_place",
        merchant_name="Test Coffee Shop",
        interest_tags=["coffee", "food"],
    )
    assert req.id is not None
    assert req.merchant_name == "Test Coffee Shop"
    assert req.interest_tags == ["coffee", "food"]
    assert req.status == "pending"


def test_join_request_idempotent(db, test_user):
    """Same driver + place_id should return existing request."""
    req1 = create_join_request(
        db=db,
        driver_user_id=test_user.id,
        place_id="ChIJ_idem_place",
        merchant_name="Idem Shop",
    )
    req2 = create_join_request(
        db=db,
        driver_user_id=test_user.id,
        place_id="ChIJ_idem_place",
        merchant_name="Idem Shop",
    )
    assert req1.id == req2.id


def test_join_request_count(db, test_user):
    """Should count requests per place_id."""
    create_join_request(db=db, driver_user_id=test_user.id, place_id="ChIJ_count", merchant_name="Count Shop")
    assert get_join_request_count(db, "ChIJ_count") == 1
    assert get_join_request_count(db, "ChIJ_other") == 0


def test_user_has_requested(db, test_user):
    """Should check if a user has requested a merchant."""
    create_join_request(db=db, driver_user_id=test_user.id, place_id="ChIJ_has", merchant_name="Has Shop")
    assert user_has_requested(db, test_user.id, "ChIJ_has") is True
    assert user_has_requested(db, test_user.id, "ChIJ_nope") is False


# ---------------------------------------------------------------------------
# Reward Claim Tests
# ---------------------------------------------------------------------------

def test_create_reward_claim(db, test_user):
    """Should create a reward claim with 2-hour expiry."""
    claim = create_reward_claim(
        db=db,
        driver_user_id=test_user.id,
        merchant_name="Asadas Grill",
        place_id="ChIJ_asadas",
        reward_description="Free Margarita",
    )
    assert claim.id is not None
    assert claim.status == RewardClaimStatus.CLAIMED
    assert claim.reward_description == "Free Margarita"
    assert claim.expires_at > datetime.utcnow()
    assert (claim.expires_at - datetime.utcnow()).total_seconds() > 7000  # ~2 hours


def test_claim_idempotent(db, test_user):
    """Same driver + place_id should return existing active claim."""
    c1 = create_reward_claim(db=db, driver_user_id=test_user.id, merchant_name="Idem", place_id="ChIJ_idem_claim")
    c2 = create_reward_claim(db=db, driver_user_id=test_user.id, merchant_name="Idem", place_id="ChIJ_idem_claim")
    assert c1.id == c2.id


def test_get_active_claims(db, test_user):
    """Should return only active (non-expired) claims."""
    create_reward_claim(db=db, driver_user_id=test_user.id, merchant_name="Active", place_id="ChIJ_active")
    claims = get_active_claims(db, test_user.id)
    assert len(claims) >= 1
    assert any(c.merchant_name == "Active" for c in claims)


def test_get_claim_by_id(db, test_user):
    """Should fetch a claim by ID for the requesting driver."""
    claim = create_reward_claim(db=db, driver_user_id=test_user.id, merchant_name="ById", place_id="ChIJ_byid")
    found = get_claim_by_id(db, claim.id, test_user.id)
    assert found is not None
    assert found.id == claim.id
    # Wrong user should not find it
    assert get_claim_by_id(db, claim.id, 99999) is None


# ---------------------------------------------------------------------------
# Receipt Submission Tests
# ---------------------------------------------------------------------------

def test_create_receipt_submission(db, test_user):
    """Should create a receipt submission and update claim status."""
    claim = create_reward_claim(db=db, driver_user_id=test_user.id, merchant_name="Receipt", place_id="ChIJ_receipt")
    submission = create_receipt_submission(
        db=db,
        driver_user_id=test_user.id,
        reward_claim_id=claim.id,
        image_url="https://example.com/receipt.jpg",
    )
    assert submission.id is not None
    assert submission.status == ReceiptStatus.PENDING

    # Claim should now be RECEIPT_UPLOADED
    db.refresh(claim)
    assert claim.status == RewardClaimStatus.RECEIPT_UPLOADED


def test_receipt_submission_wrong_user(db, test_user):
    """Should reject receipt from wrong driver."""
    claim = create_reward_claim(db=db, driver_user_id=test_user.id, merchant_name="Wrong", place_id="ChIJ_wrong")
    with pytest.raises(ValueError, match="not found"):
        create_receipt_submission(db=db, driver_user_id=99999, reward_claim_id=claim.id, image_url="https://x.com/r.jpg")


# ---------------------------------------------------------------------------
# Merchant Reward State Tests
# ---------------------------------------------------------------------------

def test_merchant_reward_state_with_request(db, test_user):
    """Should return join request state."""
    create_join_request(db=db, driver_user_id=test_user.id, place_id="ChIJ_state", merchant_name="State Shop")
    state = get_merchant_reward_state(db, place_id="ChIJ_state", merchant_id=None, driver_user_id=test_user.id)
    assert state["join_request_count"] == 1
    assert state["user_has_requested"] is True


def test_merchant_reward_state_with_claim(db, test_user):
    """Should return active claim state."""
    create_reward_claim(db=db, driver_user_id=test_user.id, merchant_name="Claimed", place_id="ChIJ_claimed_state")
    state = get_merchant_reward_state(db, place_id="ChIJ_claimed_state", merchant_id=None, driver_user_id=test_user.id)
    assert state["active_claim_id"] is not None
    assert state["active_claim_status"] == "claimed"
