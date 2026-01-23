"""
SMS service for sending custom text messages via Twilio.
Supports sending custom messages with links, notifications, etc.
"""
import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from ..core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """
    Service for sending custom SMS messages via Twilio.
    
    Supports:
    - Custom messages with links
    - Notifications
    - Marketing messages
    - Any text content
    
    Requires:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - OTP_FROM_NUMBER or TWILIO_PHONE_NUMBER (phone number to send from)
    """
    
    def __init__(self):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            raise ValueError("Twilio credentials not configured")
        
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Get from number - check multiple env vars
        self.from_number = (
            getattr(settings, 'OTP_FROM_NUMBER', None) or
            getattr(settings, 'TWILIO_PHONE_NUMBER', None) or
            self._get_default_phone_number()
        )
        
        if not self.from_number:
            logger.warning("[SMS] No phone number configured. Custom SMS will fail.")
    
    def _get_default_phone_number(self) -> Optional[str]:
        """Try to get a phone number from Twilio account"""
        try:
            incoming_numbers = self.client.incoming_phone_numbers.list(limit=1)
            if incoming_numbers:
                return incoming_numbers[0].phone_number
        except Exception as e:
            logger.debug(f"[SMS] Could not auto-detect phone number: {e}")
        return None
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format"""
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # If it starts with 1 and has 11 digits, it's already US format
        if len(digits) == 11 and digits[0] == '1':
            return f"+{digits}"
        
        # If it has 10 digits, assume US number
        if len(digits) == 10:
            return f"+1{digits}"
        
        # If it already starts with +, return as is
        if phone.startswith('+'):
            return phone
        
        # Otherwise, assume it needs +1 prefix
        return f"+1{digits}"
    
    async def send_sms(
        self,
        to_phone: str,
        message: str,
        from_number: Optional[str] = None
    ) -> dict:
        """
        Send a custom SMS message.
        
        Args:
            to_phone: Recipient phone number (any format, will be normalized)
            message: Message text (can include links)
            from_number: Optional sender number (defaults to configured number)
            
        Returns:
            dict with:
                - success: bool
                - message_sid: str (Twilio message SID)
                - status: str (message status)
                - error: str (if failed)
        """
        if not self.from_number and not from_number:
            error_msg = "No phone number configured for sending SMS"
            logger.error(f"[SMS] {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        normalized_to = self.normalize_phone(to_phone)
        sender_number = from_number or self.from_number
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=sender_number,
                to=normalized_to
            )
            
            logger.info(f"[SMS] Message sent to {normalized_to}, SID: {message_obj.sid}")
            
            return {
                "success": True,
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "to": normalized_to,
                "from": sender_number
            }
            
        except TwilioException as e:
            error_msg = f"Twilio API error: {str(e)}"
            logger.error(f"[SMS] Failed to send to {normalized_to}: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"[SMS] Failed to send to {normalized_to}: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    async def send_with_link(
        self,
        to_phone: str,
        text: str,
        link_url: str,
        link_text: Optional[str] = None
    ) -> dict:
        """
        Send SMS with a clickable link.
        
        Args:
            to_phone: Recipient phone number
            text: Message text before the link
            link_url: URL for the link
            link_text: Optional text for the link (defaults to URL)
            
        Returns:
            dict with success status and message details
        """
        # Format message with link
        if link_text:
            message = f"{text}\n\n{link_text}: {link_url}"
        else:
            message = f"{text}\n\n{link_url}"
        
        return await self.send_sms(to_phone, message)


# Singleton instance
_sms_service: Optional[SMSService] = None


def get_sms_service() -> SMSService:
    """Get or create SMS service instance"""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service


