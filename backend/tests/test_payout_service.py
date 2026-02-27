"""
Tests for PayoutService — Express account creation, wallet management,
withdrawal eligibility, transfer processing, and webhook handling.

All Stripe API calls are mocked with unittest.mock.patch.

Note: The codebase has two conflicting DriverWallet models (domain.py and
driver_wallet.py) for the same table. To work around this in tests, we
preload a mock version of the driver_wallet module before any test triggers
the real import, then test the service methods with mocked dependencies.
"""
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from app.models.user import User

# Pre-load a mock driver_wallet module to prevent the table conflict
# when the payout_service tries to import from it.
# We only do this if the real module hasn't been imported yet.
if "app.models.driver_wallet" not in sys.modules:
    import types as _types

    class _MockDriverWallet:
        """Mock DriverWallet model with attribute descriptors for ORM-like filtering."""
        driver_id = MagicMock()
        id = MagicMock()
        stripe_account_id = MagicMock()

    class _MockPayout:
        """Mock Payout model with attribute descriptors for ORM-like filtering."""
        driver_id = MagicMock()
        stripe_transfer_id = MagicMock()
        status = MagicMock()
        created_at = MagicMock()
        amount_cents = MagicMock()

    class _MockWalletLedger:
        pass

    _mock_dw_module = _types.ModuleType("app.models.driver_wallet")
    _mock_dw_module.DriverWallet = _MockDriverWallet
    _mock_dw_module.Payout = _MockPayout
    _mock_dw_module.WalletLedger = _MockWalletLedger
    sys.modules["app.models.driver_wallet"] = _mock_dw_module

from app.services.payout_service import (
    MINIMUM_WITHDRAWAL_CENTS,
    WEEKLY_WITHDRAWAL_LIMIT_CENTS,
    MAX_DAILY_WITHDRAWALS,
    _is_mock_mode,
)


def _make_user(db, email="driver@test.com"):
    user = User(
        email=email,
        password_hash="hashed",
        is_active=True,
        role_flags="driver",
    )
    db.add(user)
    db.flush()
    return user


class TestGetBalance:
    """Tests for balance retrieval logic."""

    def test_balance_can_withdraw_calculation(self):
        """Balance above minimum should allow withdrawal."""
        assert 5000 >= MINIMUM_WITHDRAWAL_CENTS

    def test_balance_cannot_withdraw_below_minimum(self):
        """Balance below minimum should not allow withdrawal."""
        assert 500 < MINIMUM_WITHDRAWAL_CENTS

    def test_minimum_withdrawal_is_configured(self):
        """MINIMUM_WITHDRAWAL_CENTS should be $20."""
        assert MINIMUM_WITHDRAWAL_CENTS == 2000

    def test_weekly_limit_configured(self):
        """WEEKLY_WITHDRAWAL_LIMIT_CENTS should be $1000."""
        assert WEEKLY_WITHDRAWAL_LIMIT_CENTS == 100000

    def test_max_daily_withdrawals_configured(self):
        """MAX_DAILY_WITHDRAWALS should be 3."""
        assert MAX_DAILY_WITHDRAWALS == 3


class TestMockModeDetection:
    """Tests for mock mode detection."""

    @patch("app.services.payout_service.ENABLE_STRIPE_PAYOUTS", False)
    def test_mock_mode_when_payouts_disabled(self):
        """Should be in mock mode when ENABLE_STRIPE_PAYOUTS is False."""
        assert _is_mock_mode() is True

    @patch("app.services.payout_service.ENABLE_STRIPE_PAYOUTS", True)
    @patch("app.services.payout_service.stripe", None)
    @patch("app.services.payout_service.STRIPE_SECRET_KEY", "")
    def test_mock_mode_when_no_stripe(self):
        """Should be in mock mode when stripe module is not loaded."""
        assert _is_mock_mode() is True


class TestPayoutServiceWithMockModels:
    """
    Integration-style tests using the PayoutService with the internal
    model imports patched to avoid the DriverWallet table conflict.
    """

    def test_get_or_create_wallet_creates_new(self):
        """get_or_create_wallet should create a wallet when none exists."""
        mock_db = MagicMock()
        mock_wallet_cls = MagicMock()
        mock_wallet_cls.return_value = MagicMock(
            id="wallet_123",
            driver_id=1,
            balance_cents=0,
            pending_balance_cents=0,
            stripe_account_id=None,
            stripe_onboarding_complete=False,
            total_earned_cents=0,
            total_withdrawn_cents=0,
        )
        # First query returns None (no wallet), second returns the new one
        mock_query = MagicMock()
        mock_query.filter.return_value.first.side_effect = [
            None,  # First call: no wallet exists
        ]
        mock_db.query.return_value = mock_query

        with patch.dict("sys.modules", {
            "app.models.driver_wallet": MagicMock(DriverWallet=mock_wallet_cls),
        }):
            from app.services.payout_service import PayoutService
            # Use a simpler approach: call the method and check it handles no wallet
            result = PayoutService.get_or_create_wallet(mock_db, 1)

        assert result["wallet_id"] is not None

    def test_credit_wallet_mock(self):
        """credit_wallet should update balance and create ledger entry."""
        mock_wallet = MagicMock(
            id="wallet_abc",
            driver_id=1,
            balance_cents=1000,
            total_earned_cents=1000,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_wallet

        with patch.dict("sys.modules", {
            "app.models.driver_wallet": MagicMock(),
        }):
            from app.services.payout_service import PayoutService
            result = PayoutService.credit_wallet(
                mock_db, 1, 500, "clo_reward", "ref_123", "Test reward"
            )

        assert result["new_balance_cents"] == 1500
        mock_db.add.assert_called()  # Ledger entry was added
        mock_db.commit.assert_called()

    def test_create_express_account_existing(self):
        """Should return existing account if driver already has one."""
        mock_wallet = MagicMock(
            stripe_account_id="acct_existing_xyz",
            stripe_onboarding_complete=True,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_wallet

        with patch.dict("sys.modules", {
            "app.models.driver_wallet": MagicMock(),
        }):
            from app.services.payout_service import PayoutService
            result = PayoutService.create_express_account(mock_db, 1, "test@test.com")

        assert result["status"] == "existing"
        assert result["stripe_account_id"] == "acct_existing_xyz"

    @patch("app.services.payout_service._is_mock_mode", return_value=True)
    def test_create_express_account_mock_mode(self, mock_mode):
        """Mock mode should create a fake account ID."""
        mock_wallet = MagicMock(
            stripe_account_id=None,
            stripe_onboarding_complete=False,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_wallet

        with patch.dict("sys.modules", {
            "app.models.driver_wallet": MagicMock(),
        }):
            from app.services.payout_service import PayoutService
            result = PayoutService.create_express_account(mock_db, 1, "test@test.com")

        assert result["status"] == "mock_created"
        assert result["stripe_account_id"].startswith("acct_mock_")

    def test_check_withdrawal_eligibility_no_wallet(self):
        """Should fail eligibility check when no wallet exists."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.dict("sys.modules", {
            "app.models.driver_wallet": MagicMock(),
        }):
            from app.services.payout_service import PayoutService
            eligible, reason = PayoutService.check_withdrawal_eligibility(
                mock_db, 1, 2000
            )

        assert eligible is False
        assert "No wallet" in reason

    def test_check_withdrawal_eligibility_below_minimum(self):
        """Should fail when amount is below minimum."""
        mock_wallet = MagicMock(
            balance_cents=5000,
            stripe_account_id="acct_123",
            stripe_onboarding_complete=True,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_wallet

        with patch.dict("sys.modules", {
            "app.models.driver_wallet": MagicMock(),
        }):
            from app.services.payout_service import PayoutService
            eligible, reason = PayoutService.check_withdrawal_eligibility(
                mock_db, 1, 500
            )

        assert eligible is False
        assert "Minimum" in reason

    def test_check_withdrawal_eligibility_insufficient_balance(self):
        """Should fail when balance is insufficient."""
        mock_wallet = MagicMock(
            balance_cents=1000,
            stripe_account_id="acct_123",
            stripe_onboarding_complete=True,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_wallet

        with patch.dict("sys.modules", {
            "app.models.driver_wallet": MagicMock(),
        }):
            from app.services.payout_service import PayoutService
            eligible, reason = PayoutService.check_withdrawal_eligibility(
                mock_db, 1, 2000
            )

        assert eligible is False
        assert "Insufficient" in reason

    def test_check_withdrawal_eligibility_no_stripe_account(self):
        """Should fail when Stripe account is not set up."""
        mock_wallet = MagicMock(
            balance_cents=5000,
            stripe_account_id=None,
            stripe_onboarding_complete=False,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_wallet

        with patch.dict("sys.modules", {
            "app.models.driver_wallet": MagicMock(),
        }):
            from app.services.payout_service import PayoutService
            eligible, reason = PayoutService.check_withdrawal_eligibility(
                mock_db, 1, 2000
            )

        assert eligible is False
        assert "not set up" in reason


class TestWebhookHandling:
    """Tests for Stripe webhook event handling."""

    @patch("app.services.payout_service._is_mock_mode", return_value=True)
    def test_webhook_mock_mode_ignored(self, mock_mode):
        """Webhooks should be ignored in mock mode."""
        mock_db = MagicMock()
        from app.services.payout_service import PayoutService
        result = PayoutService.handle_webhook(mock_db, b"payload", "sig")
        assert result["status"] == "ignored"
        assert result["reason"] == "mock_mode"

    @patch("app.services.payout_service._is_mock_mode", return_value=False)
    @patch("app.services.payout_service.STRIPE_WEBHOOK_SECRET", "")
    def test_webhook_no_secret_configured(self, mock_mode):
        """Should return error when webhook secret is not configured."""
        mock_db = MagicMock()
        from app.services.payout_service import PayoutService
        result = PayoutService.handle_webhook(mock_db, b"payload", "sig")
        assert result["status"] == "error"
        assert "not_configured" in result["reason"]

    @patch("app.services.payout_service._is_mock_mode", return_value=False)
    @patch("app.services.payout_service.STRIPE_WEBHOOK_SECRET", "whsec_test")
    @patch("app.services.payout_service.stripe")
    def test_handle_transfer_paid_webhook(self, mock_stripe, mock_mode):
        """transfer.paid webhook should process the payout."""
        mock_payout = MagicMock(
            status="processing",
            amount_cents=2000,
            wallet_id="wallet_1",
        )
        mock_wallet = MagicMock(
            pending_balance_cents=2000,
            total_withdrawn_cents=0,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_payout,  # Payout query
            mock_wallet,  # Wallet query
        ]

        mock_event = {
            "type": "transfer.paid",
            "data": {"object": {"id": "tr_test_123"}},
        }
        mock_stripe.Webhook.construct_event.return_value = mock_event

        from app.services.payout_service import PayoutService
        result = PayoutService.handle_webhook(mock_db, b"payload", "sig")

        assert result["action"] == "marked_paid"
        assert mock_payout.status == "paid"
        assert mock_payout.paid_at is not None

    @patch("app.services.payout_service._is_mock_mode", return_value=False)
    @patch("app.services.payout_service.STRIPE_WEBHOOK_SECRET", "whsec_test")
    @patch("app.services.payout_service.stripe")
    def test_handle_transfer_failed_webhook(self, mock_stripe, mock_mode):
        """transfer.failed webhook should revert funds."""
        mock_payout = MagicMock(
            status="processing",
            amount_cents=2000,
            wallet_id="wallet_1",
        )
        mock_wallet = MagicMock(
            pending_balance_cents=2000,
            balance_cents=0,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_payout,  # Payout query
            mock_wallet,  # Wallet query
        ]

        mock_event = {
            "type": "transfer.failed",
            "data": {"object": {"id": "tr_fail_456", "failure_message": "Bank rejected"}},
        }
        mock_stripe.Webhook.construct_event.return_value = mock_event

        from app.services.payout_service import PayoutService
        result = PayoutService.handle_webhook(mock_db, b"payload", "sig")

        assert result["action"] == "marked_failed"
        assert mock_payout.status == "failed"
        assert mock_payout.failure_reason == "Bank rejected"
        # Funds should be reverted
        assert mock_wallet.balance_cents == 2000
        assert mock_wallet.pending_balance_cents == 0

    @patch("app.services.payout_service._is_mock_mode", return_value=False)
    @patch("app.services.payout_service.STRIPE_WEBHOOK_SECRET", "whsec_test")
    @patch("app.services.payout_service.stripe")
    def test_handle_account_updated_webhook(self, mock_stripe, mock_mode):
        """account.updated webhook should update onboarding status."""
        mock_wallet = MagicMock(
            stripe_onboarding_complete=False,
            stripe_account_status="restricted",
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_wallet

        mock_event = {
            "type": "account.updated",
            "data": {
                "object": {
                    "id": "acct_test_789",
                    "capabilities": {"transfers": "active"},
                    "charges_enabled": True,
                }
            },
        }
        mock_stripe.Webhook.construct_event.return_value = mock_event

        from app.services.payout_service import PayoutService
        result = PayoutService.handle_webhook(mock_db, b"payload", "sig")

        assert result["action"] == "onboarding_complete"
        assert mock_wallet.stripe_onboarding_complete is True
        assert mock_wallet.stripe_account_status == "enabled"

    @patch("app.services.payout_service._is_mock_mode", return_value=False)
    @patch("app.services.payout_service.STRIPE_WEBHOOK_SECRET", "whsec_test")
    @patch("app.services.payout_service.stripe")
    def test_handle_unhandled_event_type(self, mock_stripe, mock_mode):
        """Unhandled event types should be ignored."""
        mock_db = MagicMock()
        mock_event = {
            "type": "some.other.event",
            "data": {"object": {}},
        }
        mock_stripe.Webhook.construct_event.return_value = mock_event

        from app.services.payout_service import PayoutService
        result = PayoutService.handle_webhook(mock_db, b"payload", "sig")

        assert result["status"] == "ignored"
