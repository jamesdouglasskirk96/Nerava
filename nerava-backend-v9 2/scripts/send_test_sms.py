#!/usr/bin/env python3
"""
Send a test SMS message using Twilio integration.
Usage: python scripts/send_test_sms.py <phone_number> [message]
"""
import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from app.core.config import settings


def normalize_phone(phone: str) -> str:
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


def send_sms(to_phone: str, message: str = "Hello from Nerava! This is a test message."):
    """Send SMS via Twilio"""
    # Check if Twilio is configured
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print("❌ ERROR: Twilio credentials not configured")
        print("   Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables")
        return False
    
    # Normalize phone number
    normalized_phone = normalize_phone(to_phone)
    print(f"📱 Sending SMS to: {normalized_phone}")
    print(f"📝 Message: {message}")
    print()
    
    try:
        # Initialize Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Get from number (check OTP_FROM_NUMBER or use account's default)
        from_number = os.getenv("OTP_FROM_NUMBER") or os.getenv("TWILIO_PHONE_NUMBER")
        
        if not from_number:
            # Try to get a number from the account
            print("⚠️  No OTP_FROM_NUMBER configured, trying to use account's phone numbers...")
            incoming_numbers = client.incoming_phone_numbers.list(limit=1)
            if incoming_numbers:
                from_number = incoming_numbers[0].phone_number
                print(f"✅ Using Twilio number: {from_number}")
            else:
                print("❌ ERROR: No phone number available to send from")
                print("   Please set OTP_FROM_NUMBER environment variable")
                return False
        else:
            print(f"📞 From: {from_number}")
        
        # Send SMS
        message_obj = client.messages.create(
            body=message,
            from_=from_number,
            to=normalized_phone
        )
        
        print(f"✅ SMS sent successfully!")
        print(f"   Message SID: {message_obj.sid}")
        print(f"   Status: {message_obj.status}")
        return True
        
    except TwilioException as e:
        print(f"❌ ERROR: Twilio API error: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to send SMS: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Send a test SMS via Twilio')
    parser.add_argument('phone', help='Phone number (e.g., +1234567890 or 1234567890)')
    parser.add_argument('message', nargs='?', default="Hello from Nerava! This is a test message.",
                       help='Message to send (optional)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Nerava - Twilio SMS Test")
    print("=" * 60)
    print()
    
    # Check configuration
    print("Configuration:")
    print(f"  TWILIO_ACCOUNT_SID: {'✅ Set' if settings.TWILIO_ACCOUNT_SID else '❌ Not set'}")
    print(f"  TWILIO_AUTH_TOKEN: {'✅ Set' if settings.TWILIO_AUTH_TOKEN else '❌ Not set'}")
    print(f"  OTP_FROM_NUMBER: {'✅ Set' if os.getenv('OTP_FROM_NUMBER') else '⚠️  Not set (will try to auto-detect)'}")
    print()
    
    success = send_sms(args.phone, args.message)
    
    if success:
        print()
        print("=" * 60)
        print("✅ Test SMS sent successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("❌ Failed to send SMS")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()


