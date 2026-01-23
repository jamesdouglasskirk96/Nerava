"""
Twilio Verify OTP provider implementation
"""
import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from ...core.config import settings
from .otp_provider import OTPProvider

logger = logging.getLogger(__name__)


class TwilioVerifyProvider(OTPProvider):
    """
    Twilio Verify OTP provider.
    
    Uses Twilio Verify API which handles code generation, TTL, retries, and fraud tooling.
    """
    
    def __init__(self):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            raise ValueError("Twilio credentials not configured")
        
        if not settings.TWILIO_VERIFY_SERVICE_SID:
            raise ValueError("TWILIO_VERIFY_SERVICE_SID not configured")
        
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.service_sid = settings.TWILIO_VERIFY_SERVICE_SID
    
    async def send_otp(self, phone: str) -> bool:
        """
        Send OTP via Twilio Verify.
        
        Args:
            phone: Normalized phone number in E.164 format
            
        Returns:
            True if OTP was sent successfully
        """
        try:
            verification = self.client.verify.v2.services(self.service_sid).verifications.create(
                to=phone,
                channel='sms'
            )
            
            logger.info(f"[OTP][TwilioVerify] Verification sent to {phone}, SID: {verification.sid}")
            return verification.status in ['pending', 'approved']
            
        except TwilioException as e:
            logger.exception(f"[OTP][TwilioVerify] Failed to send verification to {phone}: {e}")
            from app.core.sentry import capture_exception
            capture_exception(e, extra={"phone_masked": phone[:3] + "***"})
            raise Exception(f"Failed to send OTP: {str(e)}")
    
    async def verify_otp(self, phone: str, code: str) -> bool:
        """
        Verify OTP code via Twilio Verify.
        
        Args:
            phone: Normalized phone number in E.164 format
            code: OTP code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            verification_check = self.client.verify.v2.services(self.service_sid).verification_checks.create(
                to=phone,
                code=code
            )
            
            is_valid = verification_check.status == 'approved'
            
            if is_valid:
                logger.info(f"[OTP][TwilioVerify] Verification successful for {phone}")
            else:
                logger.warning(f"[OTP][TwilioVerify] Verification failed for {phone}: {verification_check.status}")
            
            return is_valid
            
        except TwilioException as e:
            logger.exception(f"[OTP][TwilioVerify] Error verifying code for {phone}: {e}")
            from app.core.sentry import capture_exception
            capture_exception(e, extra={"phone_masked": phone[:3] + "***"})
            return False

