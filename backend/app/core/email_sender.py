"""
Email Sender Abstraction

Provides an interface for sending emails. Currently implements ConsoleEmailSender
for development. Future implementations can add MailgunEmailSender, SendGridEmailSender, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailSender(ABC):
    """Abstract base class for email senders"""

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text email body
            body_html: Optional HTML email body
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        pass


class ConsoleEmailSender(EmailSender):
    """Console-based email sender for development - logs email to console"""

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        """
        Log email to console instead of actually sending
        
        In development, this allows testing magic links by viewing console output.
        """
        logger.info("=" * 80)
        logger.info(f"[EMAIL] To: {to_email}")
        logger.info(f"[EMAIL] Subject: {subject}")
        logger.info(f"[EMAIL] Body (text):\n{body_text}")
        if body_html:
            logger.info(f"[EMAIL] Body (HTML):\n{body_html}")
        logger.info("=" * 80)
        return True


# Global email sender instance (can be swapped based on env vars)
_email_sender: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    """Get the configured email sender instance"""
    global _email_sender
    if _email_sender is None:
        # For now, always use console sender
        # In the future, check env vars and instantiate appropriate sender
        _email_sender = ConsoleEmailSender()
    return _email_sender


def set_email_sender(sender: EmailSender) -> None:
    """Set a custom email sender (useful for testing or runtime configuration)"""
    global _email_sender
    _email_sender = sender

