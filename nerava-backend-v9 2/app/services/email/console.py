"""Console email sender for development"""
import logging
from .base import EmailSender

logger = logging.getLogger(__name__)


class ConsoleEmailSender(EmailSender):
    """Development email sender that logs to console."""

    async def send(self, to: str, subject: str, html_body: str, text_body=None, reply_to=None) -> bool:
        logger.info(f"[Email][Console] To: {to}")
        logger.info(f"[Email][Console] Subject: {subject}")
        logger.info(f"[Email][Console] Body preview: {html_body[:200]}...")
        return True


