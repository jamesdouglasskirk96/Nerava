#!/usr/bin/env python3
"""
Test PostHog connection by sending a simple event and checking response.
Uses PostHog's batch endpoint directly to verify API key.
"""

import os
import sys
import requests
import json
import time

POSTHOG_KEY = os.getenv("POSTHOG_KEY", "phx_kOolEppUR3mbcT7MbsVdWfWMUty7KCnIRcKdJ1KjaMhKO5b")
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://app.posthog.com")

def test_posthog_direct():
    """Test PostHog API directly using HTTP requests"""
    
    print("🧪 Testing PostHog API Connection Directly...")
    print(f"   Host: {POSTHOG_HOST}")
    print(f"   Key: {POSTHOG_KEY[:15]}...")
    print()
    
    # PostHog batch endpoint for capturing events
    batch_url = f"{POSTHOG_HOST}/batch/"
    
    # Create a test event
    test_event = {
        "api_key": POSTHOG_KEY,
        "batch": [
            {
                "event": "test.connection.verify",
                "distinct_id": "test_connection_check",
                "properties": {
                    "test": True,
                    "timestamp": time.time(),
                    "verification": "direct_api_test"
                }
            }
        ]
    }
    
    print("📤 Sending test event to PostHog batch endpoint...")
    try:
        response = requests.post(
            batch_url,
            json=test_event,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        print()
        
        if response.status_code == 200:
            print("✅ Event accepted by PostHog!")
            print("   The API key is valid and events are being received.")
            print()
            print("💡 Your geofence events should have been received.")
            print("   Check PostHog dashboard for:")
            print("   - distinct_id: driver:test_driver_geofence_demo")
            print("   - Events: ios.geofence.*")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed (401)")
            print("   The API key might be invalid or expired.")
            print("   Verify the key in PostHog → Project Settings → Project API Key")
            return False
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print("   Response:", response.text[:500])
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_posthog_direct()
    sys.exit(0 if success else 1)
