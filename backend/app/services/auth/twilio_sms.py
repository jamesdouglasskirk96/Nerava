"""
Twilio direct SMS OTP provider implementation (fallback)
"""
import logging
import secrets
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ...core.config import settings
from ...core.security import hash_password, verify_password
from ...models import OTPChallenge
from .otp_provider import OTPProvider

logger = logging.getLogger(__name__)


class TwilioSMSProvider(OTPProvider):
    """
    Twilio direct SMS OTP provider (fallback).
    
    Generates code, stores in DB, and sends via SMS.
    Requires OTP_FROM_NUMBER to be configured.
    """
    
    OTP_LENGTH = 6
    OTP_EXPIRE_MINUTES = 10
    
    def __init__(self, db: Session):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            raise ValueError("Twilio credentials not configured")
        
        if not settings.OTP_FROM_NUMBER:
            raise ValueError("OTP_FROM_NUMBER not configured for SMS provider")
        
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.OTP_FROM_NUMBER
        self.db = db
    
    def _generate_otp_code(self) -> str:
        """Generate a random 6-digit OTP code"""
        return str(secrets.randbelow(10**self.OTP_LENGTH)).zfill(self.OTP_LENGTH)
    
    async def send_otp(self, phone: str) -> bool:
        """
        Generate OTP code, store in DB, and send via SMS.
        
        Args:
            phone: Normalized phone number in E.164 format
            
        Returns:
            True if OTP was sent successfully
        """
        import uuid
        
        # Generate OTP code
        otp_code = self._generate_otp_code()
        code_hash = hash_password(otp_code)
        
        # Create challenge record
        expires_at = datetime.utcnow() + timedelta(minutes=self.OTP_EXPIRE_MINUTES)
        
        challenge = OTPChallenge(
            id=str(uuid.uuid4()),
            phone=phone,
            code_hash=code_hash,
            expires_at=expires_at,
            attempts=0,
            max_attempts=5,
            consumed=False
        )
        
        self.db.add(challenge)
        self.db.commit()
        
        # Send SMS
        try:
            message = self.client.messages.create(
                body=f"Your Nerava verification code is: {otp_code}",
                from_=self.from_number,
                to=phone
            )
            
            logger.info(f"[OTP][TwilioSMS] SMS sent to {phone}, SID: {message.sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"[OTP][TwilioSMS] Failed to send SMS to {phone}: {e}")
            # Don't fail - OTP is stored, can be verified
            return False
    
    async def verify_otp(self, phone: str, code: str) -> bool:
        """
        Verify OTP code against stored challenge.
        
        Args:
            phone: Normalized phone number in E.164 format
            code: OTP code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        from sqlalchemy import and_
        
        # Find active challenge
        challenge = self.db.query(OTPChallenge).filter(
            and_(
                OTPChallenge.phone == phone,
                OTPChallenge.consumed == False,
                OTPChallenge.expires_at > datetime.utcnow()
            )
        ).order_by(OTPChallenge.created_at.desc()).first()
        
        if not challenge:
            return False
        
        # Check attempt limit
        if challenge.attempts >= challenge.max_attempts:
            challenge.consumed = True
            self.db.commit()
            return False
        
        # Increment attempts
        challenge.attempts += 1
        
        # Verify code
        is_valid = verify_password(code, challenge.code_hash)
        
        if is_valid:
            challenge.consumed = True
            logger.info(f"[OTP][TwilioSMS] Verification successful for {phone}")
        else:
            logger.warning(f"[OTP][TwilioSMS] Verification failed for {phone} (attempt {challenge.attempts}/{challenge.max_attempts})")
        
        self.db.commit()
        return is_valid

