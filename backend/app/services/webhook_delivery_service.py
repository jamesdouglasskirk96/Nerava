"""
Webhook Delivery Service — Delivers webhook events to partner endpoints.

Sends HMAC-SHA256 signed payloads with retry logic and exponential backoff.
"""
import asyncio
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class WebhookDeliveryService:
    """Delivers webhook events to partner endpoints with HMAC-SHA256 signing."""

    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 10

    @staticmethod
    async def deliver(partner, event_type: str, payload: dict):
        """Fire-and-forget webhook delivery with retries."""
        if not partner.webhook_enabled or not partner.webhook_url:
            return

        event_id = str(uuid.uuid4())
        body = json.dumps({
            "event_id": event_id,
            "event_type": event_type,
            "partner_id": str(partner.id),
            "occurred_at": datetime.utcnow().isoformat() + "Z",
            "data": payload,
        }, default=str)

        # Sign with HMAC-SHA256
        signature = ""
        if partner.webhook_secret:
            signature = hmac.new(
                partner.webhook_secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Nerava-Event": event_type,
            "X-Nerava-Signature": f"sha256={signature}",
            "X-Nerava-Event-Id": event_id,
        }

        for attempt in range(1, WebhookDeliveryService.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=WebhookDeliveryService.TIMEOUT_SECONDS) as client:
                    resp = await client.post(partner.webhook_url, content=body, headers=headers)
                if resp.status_code < 300:
                    logger.info(f"Webhook delivered to {partner.slug}: {event_type} (attempt {attempt})")
                    return
                logger.warning(f"Webhook {event_type} to {partner.slug} returned {resp.status_code} (attempt {attempt})")
            except Exception as e:
                logger.warning(f"Webhook {event_type} to {partner.slug} failed (attempt {attempt}): {e}")

            if attempt < WebhookDeliveryService.MAX_RETRIES:
                await asyncio.sleep(5 ** attempt)  # 5s, 25s backoff

        logger.error(f"Webhook {event_type} to {partner.slug} failed after {WebhookDeliveryService.MAX_RETRIES} attempts")

    @staticmethod
    def build_session_resolved_payload(session_event, grant=None):
        """Build the partner.session.resolved webhook payload."""
        payload = {
            "session_event_id": session_event.id,
            "partner_session_id": session_event.source_session_id,
            "partner_driver_id": session_event.partner_driver_id,
            "status": "completed" if session_event.session_end else "charging",
            "verified": session_event.verified,
            "quality_score": session_event.quality_score,
            "session_start": session_event.session_start.isoformat() if session_event.session_start else None,
            "session_end": session_event.session_end.isoformat() if session_event.session_end else None,
            "kwh_delivered": session_event.kwh_delivered,
        }
        if grant:
            from app.core.config import settings
            platform_fee_bps = getattr(settings, 'PLATFORM_FEE_BPS', 2000)
            platform_fee_cents = (grant.amount_cents * platform_fee_bps) // 10000
            payload["reward_outcome"] = {
                "grant_id": grant.id,
                "campaign_id": grant.campaign_id,
                "amount_cents": grant.amount_cents,
                "platform_fee_cents": platform_fee_cents,
                "net_reward_cents": grant.amount_cents - platform_fee_cents,
                "reward_destination": grant.reward_destination,
                "status": grant.status,
            }
        return payload
