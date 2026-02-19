#!/usr/bin/env python3
"""
Direct verification of PostHog events by checking the PostHog client response.
"""

import os
import sys
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.analytics import get_analytics_client

# Test distinct ID
TEST_DISTINCT_ID = "driver:test_driver_geofence_demo"
EXPECTED_EVENTS = [
    "ios.geofence.charger.entered",
    "ios.geofence.merchant.entered",
    "ios.geofence.merchant.exited",
]

def check_posthog_status():
    """Check PostHog client status and send a test event"""
    
    print("🔍 Checking PostHog Configuration...")
    print()
    
    analytics = get_analytics_client()
    
    print(f"✅ PostHog Enabled: {analytics.enabled}")
    print(f"✅ PostHog Host: {analytics.posthog_host}")
    print(f"✅ PostHog Key Set: {bool(analytics.posthog_key)}")
    if analytics.posthog_key:
        print(f"✅ Key Prefix: {analytics.posthog_key[:15]}...")
    print(f"✅ Environment: {analytics.env}")
    print()
    
    if not analytics.enabled:
        print("❌ PostHog is not enabled. Cannot verify events.")
        return False
    
    # Check if PostHog client is initialized
    if not analytics.posthog_client:
        print("⚠️  PostHog client is not initialized")
        print("   This might indicate the API key is invalid")
        return False
    
    print("✅ PostHog client is initialized")
    print()
    
    # Send a verification event and check response
    print("📤 Sending verification event...")
    try:
        # The capture method doesn't return a response, but we can check for exceptions
        analytics.capture(
            event="test.verification.direct_check",
            distinct_id="test_verification_direct",
            properties={
                "test": True,
                "timestamp": time.time(),
                "check_type": "direct_verification"
            }
        )
        print("✅ Verification event sent (no exception raised)")
        print()
    except Exception as e:
        print(f"❌ Error sending verification event: {e}")
        print()
        return False
    
    print("📊 Verification Results:")
    print()
    print("The PostHog Python client sends events asynchronously.")
    print("It doesn't raise exceptions for API errors - it logs them instead.")
    print()
    print("To verify events were received:")
    print()
    print("1️⃣  Check PostHog Dashboard:")
    print(f"   - Filter by distinct_id: {TEST_DISTINCT_ID}")
    print("   - Look for events:")
    for event in EXPECTED_EVENTS:
        print(f"     • {event}")
    print()
    print("2️⃣  Check for Error Messages:")
    print("   The error 'API key is not valid: personal_api_key (401)'")
    print("   suggests PostHog might be rejecting the project API key.")
    print()
    print("3️⃣  Verify API Key Type:")
    print("   - Project API keys start with 'phx_' (for sending events)")
    print("   - Personal API keys are longer (for querying)")
    print("   - Make sure you're using a Project API Key from:")
    print("     PostHog → Project Settings → Project API Key")
    print()
    print("4️⃣  Check PostHog Logs:")
    print("   PostHog Python client logs errors to stderr")
    print("   Look for any 401 or authentication errors")
    
    return True

if __name__ == "__main__":
    check_posthog_status()
