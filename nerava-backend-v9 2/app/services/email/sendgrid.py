"""SendGrid email sender for production"""
import logging
import httpx
from typing import Optional
from .base import EmailSender
from app.core.config import settings

logger = logging.getLogger(__name__)


class SendGridEmailSender(EmailSender):
    """Production email sender using SendGrid API."""

    SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.EMAIL_FROM
        self.default_reply_to = settings.EMAIL_REPLY_TO

    async def send(self, to: str, subject: str, html_body: str, text_body=None, reply_to=None) -> bool:
        if not self.api_key:
            logger.error("[Email][SendGrid] No API key configured")
            return False

        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": self.from_email},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_body}],
        }

        if text_body:
            payload["content"].insert(0, {"type": "text/plain", "value": text_body})

        effective_reply_to = reply_to or self.default_reply_to
        if effective_reply_to:
            payload["reply_to"] = {"email": effective_reply_to}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.SENDGRID_API_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code in (200, 201, 202):
                    logger.info(f"[Email][SendGrid] Sent to {to[:3]}***")
                    return True
                else:
                    logger.error(f"[Email][SendGrid] Failed: {response.status_code} - {response.text}")
                    from app.core.sentry import capture_message
                    capture_message(f"SendGrid email failed: {response.status_code}", level="error")
                    return False

        except Exception as e:
            logger.exception(f"[Email][SendGrid] Error: {e}")
            from app.core.sentry import capture_exception
            capture_exception(e)
            return False


