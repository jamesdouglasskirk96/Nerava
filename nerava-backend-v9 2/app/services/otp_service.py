"""
Phone OTP (One-Time Password) service
Uses Twilio Verify API for secure OTP delivery and verification
"""
import httpx
import phonenumbers
from phonenumbers import NumberParseException
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..core.config import settings


class OTPService:
    """Service for sending and verifying OTP codes via Twilio Verify"""

    TWILIO_VERIFY_URL = "https://verify.twilio.com/v2/Services"

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize phone number to E.164 format.

        Raises:
            ValueError: If phone number is invalid
        """
        try:
            # Parse phone number (assume US if no country code)
            parsed = phonenumbers.parse(phone, "US")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException as e:
            raise ValueError(f"Invalid phone number format: {str(e)}")

    @staticmethod
    def _get_twilio_credentials():
        """Get Twilio credentials, raise if not configured"""
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        verify_sid = settings.TWILIO_VERIFY_SERVICE_SID

        if not account_sid or not auth_token or not verify_sid:
            return None, None, None

        return account_sid, auth_token, verify_sid

    @staticmethod
    async def send_otp(db: Session, phone: str) -> bool:
        """
        Send OTP code via Twilio Verify.

        Returns:
            True if OTP was sent successfully
        """
        # Normalize phone number
        normalized_phone = OTPService.normalize_phone(phone)

        account_sid, auth_token, verify_sid = OTPService._get_twilio_credentials()

        if not account_sid:
            # Twilio not configured - dev mode fallback
            print(f"[OTP][DEV] Twilio Verify not configured. Skipping send for {normalized_phone}")
            print(f"[OTP][DEV] For testing, use code: 123456")
            return True

        # Send verification via Twilio Verify API
        url = f"{OTPService.TWILIO_VERIFY_URL}/{verify_sid}/Verifications"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data={
                        "To": normalized_phone,
                        "Channel": "sms"
                    },
                    auth=(account_sid, auth_token),
                    timeout=30.0
                )

                if response.status_code == 201:
                    print(f"[OTP] Verification sent to {normalized_phone}")
                    return True
                elif response.status_code == 429:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many verification attempts. Please wait before trying again."
                    )
                else:
                    error_data = response.json()
                    print(f"[OTP] Twilio Verify error: {error_data}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to send code. Try again later."
                    )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Verification service timeout. Please try again."
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[OTP] Error sending verification: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to send code. Try again later."
            )

    @staticmethod
    async def verify_otp(db: Session, phone: str, code: str) -> str:
        """
        Verify OTP code via Twilio Verify.

        Returns:
            Normalized phone number if verification succeeds

        Raises:
            HTTPException: If verification fails
        """
        # Normalize phone number
        normalized_phone = OTPService.normalize_phone(phone)

        account_sid, auth_token, verify_sid = OTPService._get_twilio_credentials()

        if not account_sid:
            # Twilio not configured - dev mode fallback (accept 123456)
            if code == "123456":
                print(f"[OTP][DEV] Dev mode verification passed for {normalized_phone}")
                return normalized_phone
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid verification code"
                )

        # Verify via Twilio Verify API
        url = f"{OTPService.TWILIO_VERIFY_URL}/{verify_sid}/VerificationCheck"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data={
                        "To": normalized_phone,
                        "Code": code
                    },
                    auth=(account_sid, auth_token),
                    timeout=30.0
                )

                data = response.json()

                if response.status_code == 200 and data.get("status") == "approved":
                    print(f"[OTP] Verification approved for {normalized_phone}")
                    return normalized_phone
                elif response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No active verification found. Please request a new code."
                    )
                elif response.status_code == 429:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many verification attempts. Please wait before trying again."
                    )
                else:
                    # Verification failed (wrong code or expired)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid verification code"
                    )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Verification service timeout. Please try again."
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[OTP] Error verifying code: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Verification failed. Try again later."
            )
