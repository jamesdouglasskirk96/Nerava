"""Tests for the loyalty punch card service."""
import pytest
from sqlalchemy.orm import Session

from app.models.loyalty import LoyaltyCard, LoyaltyProgress
from app.services import loyalty_service


def _create_user(db, user_id=1, phone="5551234567"):
    from app.models import User
    user = User(id=user_id, phone=phone, role_flags="driver")
    db.add(user)
    db.commit()
    return user


MERCHANT_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

def _create_merchant(db, merchant_id=MERCHANT_UUID):
    from app.models.domain import DomainMerchant
    m = DomainMerchant(
        id=merchant_id,
        name="Test Cafe",
        lat=30.0, lng=-97.0,
        zone_slug="test_zone",
    )
    db.add(m)
    db.commit()
    return m


# ---------------------------------------------------------------------------
# Card CRUD
# ---------------------------------------------------------------------------

def test_create_loyalty_card(db: Session):
    _create_merchant(db)
    card = loyalty_service.create_loyalty_card(
        db, merchant_id=MERCHANT_UUID, program_name="Coffee Card",
        visits_required=5, reward_cents=500, reward_description="Free coffee",
    )
    assert card.id is not None
    assert card.program_name == "Coffee Card"
    assert card.visits_required == 5
    assert card.reward_cents == 500
    assert card.is_active is True


def test_list_loyalty_cards(db: Session):
    _create_merchant(db)
    loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card A", 3, 300)
    loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card B", 10, 1000)
    cards = loyalty_service.get_loyalty_cards(db, MERCHANT_UUID)
    assert len(cards) == 2


def test_update_loyalty_card(db: Session):
    _create_merchant(db)
    card = loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Old Name", 5, 500)
    updated = loyalty_service.update_loyalty_card(db, card.id, MERCHANT_UUID, program_name="New Name", is_active=False)
    assert updated.program_name == "New Name"
    assert updated.is_active is False


def test_update_card_wrong_merchant(db: Session):
    _create_merchant(db)
    card = loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 5, 500)
    result = loyalty_service.update_loyalty_card(db, card.id, "11111111-2222-3333-4444-555555555555", program_name="X")
    assert result is None


# ---------------------------------------------------------------------------
# Visit increment & auto-unlock
# ---------------------------------------------------------------------------

def test_increment_visit(db: Session):
    _create_merchant(db)
    _create_user(db)
    loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 3, 300)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    progress = loyalty_service.get_driver_progress(db, 1, MERCHANT_UUID)
    assert len(progress) == 1
    assert progress[0]["visit_count"] == 1
    assert progress[0]["reward_unlocked"] is False


def test_auto_unlock_at_milestone(db: Session):
    _create_merchant(db)
    _create_user(db)
    loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 3, 300)
    for _ in range(3):
        loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    progress = loyalty_service.get_driver_progress(db, 1, MERCHANT_UUID)
    assert progress[0]["visit_count"] == 3
    assert progress[0]["reward_unlocked"] is True
    assert progress[0]["reward_claimed"] is False


def test_no_increment_after_claimed(db: Session):
    _create_merchant(db)
    _create_user(db)
    card = loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 2, 200)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    loyalty_service.claim_reward(db, 1, card.id)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    progress = loyalty_service.get_driver_progress(db, 1, MERCHANT_UUID)
    assert progress[0]["visit_count"] == 2  # didn't increment past claim


# ---------------------------------------------------------------------------
# Claim reward
# ---------------------------------------------------------------------------

def test_claim_reward(db: Session):
    _create_merchant(db)
    _create_user(db)
    card = loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 2, 200)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    result = loyalty_service.claim_reward(db, 1, card.id)
    assert result is not None
    assert result.reward_claimed is True
    assert result.reward_claimed_at is not None


def test_claim_reward_not_unlocked(db: Session):
    _create_merchant(db)
    _create_user(db)
    card = loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 5, 500)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    result = loyalty_service.claim_reward(db, 1, card.id)
    assert result is None


def test_claim_reward_double_claim(db: Session):
    _create_merchant(db)
    _create_user(db)
    card = loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 1, 100)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    loyalty_service.claim_reward(db, 1, card.id)
    result = loyalty_service.claim_reward(db, 1, card.id)
    assert result is None


# ---------------------------------------------------------------------------
# Merchant analytics
# ---------------------------------------------------------------------------

def test_merchant_loyalty_stats(db: Session):
    _create_merchant(db)
    _create_user(db, 1, "5551111111")
    _create_user(db, 2, "5552222222")
    card = loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 3, 300)

    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    loyalty_service.increment_visit(db, 2, MERCHANT_UUID)

    stats = loyalty_service.get_merchant_loyalty_stats(db, MERCHANT_UUID)
    assert stats["enrolled_drivers"] == 2
    assert stats["total_visits"] == 3
    assert stats["rewards_unlocked"] == 0
    assert stats["rewards_claimed"] == 0


def test_merchant_loyalty_customers(db: Session):
    _create_merchant(db)
    _create_user(db)
    loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card", 5, 500)
    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)

    result = loyalty_service.get_merchant_loyalty_customers(db, MERCHANT_UUID)
    assert result["total"] == 1
    assert len(result["customers"]) == 1
    assert result["customers"][0]["visit_count"] == 1


# ---------------------------------------------------------------------------
# Multiple cards per merchant
# ---------------------------------------------------------------------------

def test_multiple_cards_all_punched(db: Session):
    _create_merchant(db)
    _create_user(db)
    loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card A", 2, 200)
    loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Card B", 5, 500)

    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    progress = loyalty_service.get_driver_progress(db, 1, MERCHANT_UUID)
    assert len(progress) == 2
    assert all(p["visit_count"] == 1 for p in progress)


def test_inactive_card_not_in_progress(db: Session):
    _create_merchant(db)
    _create_user(db)
    loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Active", 3, 300)
    inactive = loyalty_service.create_loyalty_card(db, MERCHANT_UUID, "Inactive", 3, 300)
    loyalty_service.update_loyalty_card(db, inactive.id, MERCHANT_UUID, is_active=False)

    loyalty_service.increment_visit(db, 1, MERCHANT_UUID)
    progress = loyalty_service.get_driver_progress(db, 1, MERCHANT_UUID)
    assert len(progress) == 1
    assert progress[0]["program_name"] == "Active"
