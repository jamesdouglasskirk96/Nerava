"""Email sender factory - returns appropriate sender based on config."""
from app.core.config import settings
from .base import EmailSender
from .console import ConsoleEmailSender
from .sendgrid import SendGridEmailSender

_sender_instance: EmailSender | None = None


def get_email_sender() -> EmailSender:
    """Get configured email sender instance."""
    global _sender_instance
    
    if _sender_instance is None:
        provider = settings.EMAIL_PROVIDER.lower()
        
        if provider == "sendgrid" and settings.SENDGRID_API_KEY:
            _sender_instance = SendGridEmailSender()
        else:
            _sender_instance = ConsoleEmailSender()
    
    return _sender_instance

