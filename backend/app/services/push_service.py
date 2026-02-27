"""
Push Notification Service — Sends APNs push notifications to iOS devices.

Uses PyAPNs2 to send notifications via Apple Push Notification service.
Handles token invalidation when APNs returns 410 Gone.
"""
import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.device_token import DeviceToken
from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded APNs client (only initialized when needed)
_apns_client = None


def _get_apns_client():
    """Get or create the APNs client. Returns None if not configured."""
    global _apns_client
    if _apns_client is not None:
        return _apns_client

    key_path = getattr(settings, "APNS_KEY_PATH", None)
    key_id = getattr(settings, "APNS_KEY_ID", None)
    team_id = getattr(settings, "APNS_TEAM_ID", None)

    if not all([key_path, key_id, team_id]):
        logger.debug("APNs not configured (APNS_KEY_PATH, APNS_KEY_ID, APNS_TEAM_ID required)")
        return None

    try:
        from apns2.client import APNsClient
        from apns2.credentials import TokenCredentials

        token_credentials = TokenCredentials(
            auth_key_path=key_path,
            auth_key_id=key_id,
            team_id=team_id,
        )
        _apns_client = APNsClient(
            credentials=token_credentials,
            use_sandbox=getattr(settings, "APNS_USE_SANDBOX", False),
        )
        logger.info("APNs client initialized (key_id=%s)", key_id)
        return _apns_client
    except Exception as e:
        logger.warning("Failed to initialize APNs client: %s", e)
        return None


def send_push_notification(
    db: Session,
    user_id: int,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Send a push notification to all active devices for a user.

    Returns the number of notifications successfully sent.
    """
    bundle_id = getattr(settings, "APNS_BUNDLE_ID", "com.nerava.app")

    tokens = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.user_id == user_id,
            DeviceToken.is_active.is_(True),
        )
        .all()
    )

    if not tokens:
        logger.debug("No active device tokens for user %s", user_id)
        return 0

    client = _get_apns_client()
    if client is None:
        logger.info(
            "APNs not configured — skipping push for user %s (%s: %s)",
            user_id, title, body,
        )
        return 0

    try:
        from apns2.payload import Payload
    except ImportError:
        logger.warning("PyAPNs2 not installed — cannot send push notifications")
        return 0

    payload = Payload(
        alert={"title": title, "body": body},
        sound="default",
        custom=data or {},
    )

    sent = 0
    for device in tokens:
        try:
            response = client.send_notification(
                device.token, payload, topic=bundle_id
            )

            if response == "Success" or (hasattr(response, 'is_successful') and response.is_successful):
                sent += 1
                logger.debug("Push sent to device %s for user %s", device.id, user_id)
            else:
                reason = getattr(response, 'description', str(response))
                logger.warning(
                    "Push failed for device %s: %s", device.id, reason
                )
                # Deactivate invalid tokens
                if "Unregistered" in str(reason) or "BadDeviceToken" in str(reason):
                    device.is_active = False
                    logger.info("Deactivated invalid token %s", device.id)
        except Exception as e:
            error_str = str(e)
            logger.warning("Push error for device %s: %s", device.id, error_str)
            # Handle 410 Gone — token is permanently invalid
            if "410" in error_str or "Unregistered" in error_str:
                device.is_active = False
                logger.info("Deactivated expired token %s (410 Gone)", device.id)

    if sent > 0 or any(not d.is_active for d in tokens):
        db.commit()

    logger.info(
        "Push notification sent to %d/%d devices for user %s: %s",
        sent, len(tokens), user_id, title,
    )
    return sent


def send_incentive_earned_push(
    db: Session,
    user_id: int,
    amount_cents: int,
) -> int:
    """Send push notification when driver earns a charging incentive."""
    amount_str = f"${amount_cents / 100:.2f}"
    return send_push_notification(
        db,
        user_id,
        title="You earned a reward!",
        body=f"You earned {amount_str} from your charging session.",
        data={"type": "incentive_earned", "amount_cents": amount_cents},
    )


def send_exclusive_confirmed_push(
    db: Session,
    user_id: int,
    merchant_name: str,
) -> int:
    """Send push notification when exclusive spot is confirmed."""
    return send_push_notification(
        db,
        user_id,
        title="Spot confirmed!",
        body=f"Your spot at {merchant_name} is confirmed. Head over now!",
        data={"type": "exclusive_confirmed", "merchant_name": merchant_name},
    )


def send_payout_complete_push(
    db: Session,
    user_id: int,
    amount_cents: int,
) -> int:
    """Send push notification when a payout is completed."""
    amount_str = f"${amount_cents / 100:.2f}"
    return send_push_notification(
        db,
        user_id,
        title="Payout sent!",
        body=f"Your payout of {amount_str} has been sent to your bank.",
        data={"type": "payout_complete", "amount_cents": amount_cents},
    )
