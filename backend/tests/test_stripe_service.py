"""
Tests for StripeService — checkout session creation and webhook handling.

All Stripe API calls are mocked with unittest.mock.patch.
"""
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from app.models.user import User
from app.models.domain import DomainMerchant, StripePayment, NovaTransaction
from app.services.stripe_service import StripeService, NOVA_PACKAGES


def _make_merchant(db, **overrides):
    defaults = dict(
        id=str(uuid.uuid4()),
        name="Test Merchant",
        lat=30.4,
        lng=-97.7,
        zone_slug="test_zone",
        status="active",
        nova_balance=0,
    )
    defaults.update(overrides)
    merchant = DomainMerchant(**defaults)
    db.add(merchant)
    db.flush()
    return merchant


class TestStripeServiceCheckout:
    """Tests for Stripe checkout session creation."""

    @patch("app.services.stripe_service.stripe")
    def test_create_checkout_session_success(self, mock_stripe_module, db):
        """Should create a Stripe checkout session and StripePayment record."""
        mock_stripe_module.api_key = "sk_test_123"

        merchant = _make_merchant(db)

        mock_session = MagicMock()
        mock_session.id = "cs_test_session_id"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe_module.checkout.Session.create.return_value = mock_session

        result = StripeService.create_checkout_session(db, merchant.id, "nova_100")

        assert result["checkout_url"] == "https://checkout.stripe.com/test"
        assert result["session_id"] == "cs_test_session_id"

        # Verify StripePayment record was created
        payment = db.query(StripePayment).filter(
            StripePayment.stripe_session_id == "cs_test_session_id"
        ).first()
        assert payment is not None
        assert payment.merchant_id == merchant.id
        assert payment.status == "pending"
        assert payment.amount_usd == NOVA_PACKAGES["nova_100"]["usd_cents"]

    def test_create_checkout_session_invalid_package(self, db):
        """Should raise ValueError for invalid package ID."""
        merchant = _make_merchant(db)

        with patch("app.services.stripe_service.stripe") as mock_stripe:
            mock_stripe.api_key = "sk_test_123"
            with pytest.raises(ValueError, match="Invalid package_id"):
                StripeService.create_checkout_session(db, merchant.id, "invalid_pkg")

    def test_create_checkout_session_missing_merchant(self, db):
        """Should raise ValueError when merchant does not exist."""
        fake_id = str(uuid.uuid4())
        with patch("app.services.stripe_service.stripe") as mock_stripe:
            mock_stripe.api_key = "sk_test_123"
            with pytest.raises(ValueError, match="not found"):
                StripeService.create_checkout_session(db, fake_id, "nova_100")

    def test_create_checkout_session_no_api_key(self, db):
        """Should raise ValueError when Stripe API key is not configured."""
        merchant = _make_merchant(db)

        with patch("app.services.stripe_service.stripe") as mock_stripe:
            mock_stripe.api_key = None
            with pytest.raises(ValueError, match="Stripe not configured"):
                StripeService.create_checkout_session(db, merchant.id, "nova_100")


class TestStripeServiceWebhook:
    """Tests for Stripe webhook handling."""

    @patch("app.services.stripe_service.NovaService.grant_to_merchant")
    @patch("app.services.stripe_service.stripe")
    def test_handle_checkout_completed_webhook(self, mock_stripe_module, mock_nova_grant, db):
        """Should process checkout.session.completed and grant Nova."""
        mock_stripe_module.api_key = "sk_test_123"

        merchant = _make_merchant(db)
        payment_id = str(uuid.uuid4())

        # Create a pending payment
        payment = StripePayment(
            id=payment_id,
            stripe_session_id="cs_test_abc",
            merchant_id=merchant.id,
            amount_usd=10000,
            nova_issued=1000,
            status="pending",
        )
        db.add(payment)
        db.flush()

        # Simulate Stripe webhook event
        mock_event = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_abc",
                    "payment_intent": "pi_test_xyz",
                    "metadata": {
                        "merchant_id": merchant.id,
                        "nova_amount": "1000",
                        "package_id": "nova_100",
                        "payment_id": payment_id,
                    },
                }
            },
        }
        mock_stripe_module.Webhook.construct_event.return_value = mock_event

        result = StripeService.handle_webhook(
            db, b"raw_payload", "sig_header", "webhook_secret"
        )

        assert result["status"] == "success"
        assert result["nova_granted"] == 1000

        # Verify payment status was updated
        db.refresh(payment)
        assert payment.status == "paid"
        assert payment.stripe_payment_intent_id == "pi_test_xyz"
        assert payment.stripe_event_id == "evt_test_123"

    @patch("app.services.stripe_service.stripe")
    def test_handle_webhook_idempotent(self, mock_stripe_module, db):
        """Processing the same webhook event twice should be idempotent."""
        mock_stripe_module.api_key = "sk_test_123"

        merchant = _make_merchant(db)
        payment_id = str(uuid.uuid4())

        # Create a payment that was already processed (has event_id)
        payment = StripePayment(
            id=payment_id,
            stripe_session_id="cs_test_dup",
            stripe_event_id="evt_test_dup",
            merchant_id=merchant.id,
            amount_usd=10000,
            nova_issued=1000,
            status="paid",
        )
        db.add(payment)
        db.flush()

        mock_event = {
            "id": "evt_test_dup",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_dup",
                    "metadata": {
                        "merchant_id": merchant.id,
                        "nova_amount": "1000",
                        "package_id": "nova_100",
                        "payment_id": payment_id,
                    },
                }
            },
        }
        mock_stripe_module.Webhook.construct_event.return_value = mock_event

        result = StripeService.handle_webhook(
            db, b"raw_payload", "sig_header", "webhook_secret"
        )

        assert result["status"] == "already_processed"

    @patch("app.services.stripe_service.stripe")
    def test_handle_webhook_invalid_signature(self, mock_stripe_module, db):
        """Should raise ValueError on invalid webhook signature."""
        mock_stripe_module.api_key = "sk_test_123"

        # Import the actual stripe errors for the mock
        import stripe as stripe_lib
        mock_stripe_module.error = stripe_lib.error
        mock_stripe_module.Webhook.construct_event.side_effect = (
            stripe_lib.error.SignatureVerificationError("bad sig", "sig_header")
        )

        with pytest.raises(ValueError, match="Invalid signature"):
            StripeService.handle_webhook(
                db, b"raw_payload", "bad_sig", "webhook_secret"
            )

    @patch("app.services.stripe_service.stripe")
    def test_handle_webhook_unhandled_event_type(self, mock_stripe_module, db):
        """Unhandled event types should be ignored gracefully."""
        mock_stripe_module.api_key = "sk_test_123"
        mock_event = {
            "id": "evt_other",
            "type": "payment_intent.succeeded",
            "data": {"object": {}},
        }
        mock_stripe_module.Webhook.construct_event.return_value = mock_event

        result = StripeService.handle_webhook(
            db, b"payload", "sig", "secret"
        )
        assert result["status"] == "ignored"


class TestNovaPackages:
    """Verify NOVA_PACKAGES configuration."""

    def test_packages_have_required_keys(self):
        """Each package should define usd_cents and nova_amount."""
        for pkg_id, pkg in NOVA_PACKAGES.items():
            assert "usd_cents" in pkg, f"Package {pkg_id} missing usd_cents"
            assert "nova_amount" in pkg, f"Package {pkg_id} missing nova_amount"
            assert pkg["usd_cents"] > 0
            assert pkg["nova_amount"] > 0

    def test_volume_discounts(self):
        """Larger packages should have better per-Nova pricing."""
        price_100 = NOVA_PACKAGES["nova_100"]["usd_cents"] / NOVA_PACKAGES["nova_100"]["nova_amount"]
        price_500 = NOVA_PACKAGES["nova_500"]["usd_cents"] / NOVA_PACKAGES["nova_500"]["nova_amount"]
        price_1000 = NOVA_PACKAGES["nova_1000"]["usd_cents"] / NOVA_PACKAGES["nova_1000"]["nova_amount"]

        assert price_500 < price_100, "500 pack should be cheaper per Nova than 100"
        assert price_1000 < price_500, "1000 pack should be cheaper per Nova than 500"
