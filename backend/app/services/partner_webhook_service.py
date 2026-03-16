"""
Partner Webhook Delivery Service

Delivers webhook events to partners with HMAC-SHA256 signature verification,
retry logic with exponential backoff, and structured logging.
"""
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional

import httpx

from app.models.partner import Partner

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]  # Exponential backoff per attempt
REQUEST_TIMEOUT_SECONDS = 10


def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for a payload."""
    mac = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256)
    return mac.hexdigest()


def deliver_webhook(
    partner: Partner,
    event_type: str,
    payload: Dict[str, Any],
) -> bool:
    """
    Deliver a webhook event to a partner's configured endpoint.

    Signs the JSON payload with HMAC-SHA256 using the partner's webhook_secret,
    then POSTs to the partner's webhook_url with appropriate headers.

    Retries up to 3 times with exponential backoff (1s, 2s, 4s) on failure.
    Times out after 10 seconds per attempt.

    Args:
        partner: The partner to deliver the webhook to.
        event_type: The event type string (e.g., "grant.created").
        payload: The event payload dict.

    Returns:
        True if delivery succeeded (2xx response), False otherwise.
    """
    if not partner.webhook_url:
        logger.warning(f"Partner {partner.slug} has no webhook_url configured, skipping delivery")
        return False

    if not partner.webhook_secret:
        logger.warning(f"Partner {partner.slug} has no webhook_secret configured, skipping delivery")
        return False

    payload_bytes = json.dumps(payload, default=str, sort_keys=True).encode("utf-8")
    signature = _sign_payload(payload_bytes, partner.webhook_secret)

    headers = {
        "Content-Type": "application/json",
        "X-Nerava-Signature": f"sha256={signature}",
        "X-Nerava-Event": event_type,
    }

    last_error: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = client.post(
                    partner.webhook_url,
                    content=payload_bytes,
                    headers=headers,
                )

            if 200 <= response.status_code < 300:
                logger.info(
                    f"Webhook delivered to partner {partner.slug}: "
                    f"event={event_type} status={response.status_code} "
                    f"attempt={attempt + 1}"
                )
                return True

            last_error = Exception(f"HTTP {response.status_code}: {response.text[:200]}")
            logger.warning(
                f"Webhook delivery failed for partner {partner.slug}: "
                f"event={event_type} status={response.status_code} "
                f"attempt={attempt + 1}/{MAX_RETRIES}"
            )

        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(
                f"Webhook delivery timed out for partner {partner.slug}: "
                f"event={event_type} attempt={attempt + 1}/{MAX_RETRIES}"
            )

        except Exception as e:
            last_error = e
            logger.warning(
                f"Webhook delivery error for partner {partner.slug}: "
                f"event={event_type} error={e} attempt={attempt + 1}/{MAX_RETRIES}"
            )

        # Backoff before next retry (skip sleep after last attempt)
        if attempt < MAX_RETRIES - 1:
            backoff = BACKOFF_SECONDS[attempt]
            time.sleep(backoff)

    logger.error(
        f"Webhook delivery failed after {MAX_RETRIES} attempts for partner {partner.slug}: "
        f"event={event_type} last_error={last_error}"
    )
    return False
