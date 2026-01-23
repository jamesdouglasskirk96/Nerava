"""Base email sender interface"""
from abc import ABC, abstractmethod
from typing import Optional


class EmailSender(ABC):
    """Abstract base class for email senders"""

    @abstractmethod
    async def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Optional plain text email body
            reply_to: Optional reply-to email address
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        pass


