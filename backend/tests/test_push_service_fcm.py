"""
Tests for dual-platform push notification routing (APNs + FCM).
"""
import sys
from unittest.mock import patch, MagicMock
import pytest

# Mock apns2 module if not installed (test environment)
if "apns2" not in sys.modules:
    apns2_mock = MagicMock()
    sys.modules["apns2"] = apns2_mock
    sys.modules["apns2.payload"] = apns2_mock.payload
    sys.modules["apns2.client"] = apns2_mock.client
    sys.modules["apns2.credentials"] = apns2_mock.credentials

from app.services.push_service import send_push_notification, _TokenInvalidError


@pytest.fixture
def mock_device_tokens():
    """Create mock DeviceToken objects for iOS and Android."""
    ios_token = MagicMock()
    ios_token.id = "ios-device-1"
    ios_token.user_id = 1
    ios_token.token = "apns-token-abc"
    ios_token.platform = "ios"
    ios_token.is_active = True

    android_token = MagicMock()
    android_token.id = "android-device-1"
    android_token.user_id = 1
    android_token.token = "fcm-token-xyz"
    android_token.platform = "android"
    android_token.is_active = True

    return ios_token, android_token


@pytest.fixture
def mock_db(mock_device_tokens):
    """Create mock DB session that returns device tokens."""
    ios_token, android_token = mock_device_tokens
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [ios_token, android_token]
    return db


class TestPushServiceRouting:
    """Test that push notifications are routed to the correct platform."""

    @patch("app.services.push_service._send_fcm_notification", return_value=True)
    @patch("app.services.push_service._get_apns_client")
    def test_android_token_routes_to_fcm(self, mock_apns_client, mock_fcm_send, mock_db, mock_device_tokens):
        """Android device tokens should be sent via FCM."""
        ios_token, android_token = mock_device_tokens
        # Only Android token
        mock_db.query.return_value.filter.return_value.all.return_value = [android_token]
        mock_apns_client.return_value = None

        sent = send_push_notification(mock_db, 1, "Test", "Body")

        assert sent == 1
        mock_fcm_send.assert_called_once_with("fcm-token-xyz", "Test", "Body", None)

    @patch("app.services.push_service._send_fcm_notification")
    @patch("app.services.push_service._get_apns_client")
    def test_ios_token_routes_to_apns(self, mock_apns_client, mock_fcm_send, mock_db, mock_device_tokens):
        """iOS device tokens should be sent via APNs."""
        ios_token, android_token = mock_device_tokens
        # Only iOS token
        mock_db.query.return_value.filter.return_value.all.return_value = [ios_token]

        mock_client = MagicMock()
        mock_client.send_notification.return_value = "Success"
        mock_apns_client.return_value = mock_client

        sent = send_push_notification(mock_db, 1, "Test", "Body")

        assert sent == 1
        mock_fcm_send.assert_not_called()
        mock_client.send_notification.assert_called_once()

    @patch("app.services.push_service._send_fcm_notification", return_value=True)
    @patch("app.services.push_service._get_apns_client")
    def test_mixed_platforms_both_sent(self, mock_apns_client, mock_fcm_send, mock_db, mock_device_tokens):
        """Both iOS and Android tokens should be sent to their respective services."""
        mock_client = MagicMock()
        mock_client.send_notification.return_value = "Success"
        mock_apns_client.return_value = mock_client

        sent = send_push_notification(mock_db, 1, "Test", "Body")

        assert sent == 2
        mock_fcm_send.assert_called_once()
        mock_client.send_notification.assert_called_once()

    @patch("app.services.push_service._send_fcm_notification")
    @patch("app.services.push_service._get_apns_client")
    def test_invalid_fcm_token_deactivated(self, mock_apns_client, mock_fcm_send, mock_db, mock_device_tokens):
        """Invalid FCM tokens should be deactivated."""
        ios_token, android_token = mock_device_tokens
        mock_db.query.return_value.filter.return_value.all.return_value = [android_token]
        mock_apns_client.return_value = None
        mock_fcm_send.side_effect = _TokenInvalidError("UNREGISTERED")

        sent = send_push_notification(mock_db, 1, "Test", "Body")

        assert sent == 0
        assert android_token.is_active is False

    def test_no_tokens_returns_zero(self):
        """No device tokens should return 0."""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        sent = send_push_notification(db, 1, "Test", "Body")
        assert sent == 0

    @patch("app.services.push_service._send_fcm_notification", return_value=True)
    @patch("app.services.push_service._get_apns_client")
    def test_fcm_receives_data_payload(self, mock_apns_client, mock_fcm_send, mock_db, mock_device_tokens):
        """FCM should receive the data payload."""
        ios_token, android_token = mock_device_tokens
        mock_db.query.return_value.filter.return_value.all.return_value = [android_token]
        mock_apns_client.return_value = None

        data = {"type": "incentive_earned", "amount_cents": 500}
        send_push_notification(mock_db, 1, "Reward!", "You earned $5.00", data=data)

        mock_fcm_send.assert_called_once_with(
            "fcm-token-xyz", "Reward!", "You earned $5.00", data
        )
