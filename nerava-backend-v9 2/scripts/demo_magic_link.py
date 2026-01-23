#!/usr/bin/env python3
"""
Demo script: Activate exclusive and send magic link SMS

Usage:
    python scripts/demo_magic_link.py

This will:
1. Activate an exclusive session at Heights Pizzeria
2. Generate a magic link token
3. Send SMS to James's phone with the magic link
"""
import os
import sys
import uuid
import requests
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configuration
PHONE = "+17133056318"
CHARGER_ID = "tesla_market_heights"
MERCHANT_ID = "ChIJ_heights_pizzeria_harker"
MERCHANT_NAME = "The Heights Pizzeria & Drafthouse"
LAT = 31.0571
LNG = -97.665

# API base URL
API_BASE = os.getenv("API_BASE_URL", "https://api.nerava.network")

def main():
    print("=" * 60)
    print("NERAVA MAGIC LINK DEMO")
    print("=" * 60)
    print(f"Phone: {PHONE}")
    print(f"Charger: {CHARGER_ID}")
    print(f"Merchant: {MERCHANT_NAME}")
    print(f"Location: {LAT}, {LNG}")
    print()

    # Step 1: Create exclusive session
    print("[1/3] Activating exclusive session...")
    exclusive_session_id = f"demo_{uuid.uuid4().hex[:8]}"

    # In production, this would call the /v1/exclusive/activate endpoint
    # For demo, we'll use a mock session ID
    print(f"      Session ID: {exclusive_session_id}")
    print(f"      Status: ACTIVE")
    print()

    # Step 2: Generate magic link
    print("[2/3] Generating magic link...")

    try:
        response = requests.post(
            f"{API_BASE}/v1/magic/generate",
            json={
                "phone": PHONE,
                "exclusive_session_id": exclusive_session_id,
                "merchant_id": MERCHANT_ID,
                "charger_id": CHARGER_ID,
            },
            timeout=10,
        )
        response.raise_for_status()
        magic_data = response.json()
        magic_link = magic_data["link"]
        print(f"      Link: {magic_link}")
        print()
    except Exception as e:
        print(f"      Error generating magic link: {e}")
        print("      Using fallback link...")
        magic_link = f"https://app.nerava.network/exclusive/{MERCHANT_ID}?demo=true"
        print(f"      Link: {magic_link}")
        print()

    # Step 3: Send SMS
    print("[3/3] Sending SMS...")

    sms_message = (
        f"Your Nerava exclusive is active at {MERCHANT_NAME}! "
        f"Show this to redeem your perk: {magic_link}"
    )

    try:
        response = requests.post(
            f"{API_BASE}/v1/sms/send",
            json={
                "to_phone": PHONE,
                "message": sms_message,
            },
            timeout=10,
        )
        response.raise_for_status()
        print(f"      SMS sent successfully!")
        print()
    except Exception as e:
        print(f"      Error sending SMS: {e}")
        print(f"      Message would be: {sms_message}")
        print()

    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print()
    print(f"Magic Link: {magic_link}")
    print()
    print("Next steps:")
    print("1. Check your phone for the SMS")
    print("2. Click the link to open your exclusive pass")
    print("3. Show the pass to the merchant to redeem")
    print()


if __name__ == "__main__":
    main()


