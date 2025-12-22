"""
Tests for wallet activity side-effects:
- Apple PassKit push trigger
- Google Wallet object update trigger
"""
import os

from sqlalchemy.orm import Session

from app.models.domain import DriverWallet
from app.services.wallet_activity import mark_wallet_activity


def test_mark_wallet_activity_triggers_apple_push(monkeypatch, db: Session, test_user):
    """APPLE_PASS_PUSH_ENABLED=true should call send_updates_for_wallet once."""
    wallet = DriverWallet(user_id=test_user.id, nova_balance=0, energy_reputation_score=0)
    db.add(wallet)
    db.commit()

    called = {"count": 0}

    def fake_send_updates_for_wallet(db_arg, wallet_arg):
        called["count"] += 1
        assert wallet_arg.user_id == test_user.id

    monkeypatch.setenv("APPLE_PASS_PUSH_ENABLED", "true")
    monkeypatch.setattr(
        "app.services.wallet_activity.send_updates_for_wallet",
        fake_send_updates_for_wallet,
    )

    mark_wallet_activity(db, test_user.id)

    assert called["count"] == 1


def test_mark_wallet_activity_triggers_google_update(monkeypatch, db: Session, test_user):
    """GOOGLE_WALLET_ENABLED=true should call update_google_wallet_object_on_activity when token present."""
    wallet = DriverWallet(
        user_id=test_user.id,
        nova_balance=0,
        energy_reputation_score=0,
        wallet_pass_token="opaque-token-123",
    )
    db.add(wallet)
    db.commit()

    called = {"count": 0}

    def fake_update_google_wallet_object_on_activity(db_arg, wallet_arg, token_arg):
        called["count"] += 1
        assert wallet_arg.user_id == test_user.id
        assert token_arg == "opaque-token-123"

    monkeypatch.setenv("GOOGLE_WALLET_ENABLED", "true")
    monkeypatch.setattr(
        "app.services.wallet_activity.update_google_wallet_object_on_activity",
        fake_update_google_wallet_object_on_activity,
    )

    mark_wallet_activity(db, test_user.id)

    assert called["count"] == 1



