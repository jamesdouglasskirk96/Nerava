#!/usr/bin/env python3
"""
Verify PostHog events were received by querying the PostHog API directly.
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# PostHog API key
POSTHOG_KEY = os.getenv("POSTHOG_KEY", "phx_kOolEppUR3mbcT7MbsVdWfWMUty7KCnIRcKdJ1KjaMhKO5b")
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
TEST_DISTINCT_ID = "driver:test_driver_geofence_demo"

# Events we're looking for
EXPECTED_EVENTS = [
    "ios.geofence.charger.entered",
    "ios.geofence.merchant.entered",
    "ios.geofence.merchant.exited",
]

def verify_events():
    """Query PostHog API to verify events were received"""
    
    print("🔍 Verifying PostHog events...")
    print(f"   PostHog Host: {POSTHOG_HOST}")
    print(f"   Distinct ID: {TEST_DISTINCT_ID}")
    print()
    
    # PostHog API endpoint for querying events
    # Note: PostHog doesn't have a direct "get events" API, but we can use insights API
    # For verification, we'll check via the events API if available
    
    # Try using PostHog's REST API to query events
    # PostHog uses project API key for ingestion, but personal API key for querying
    # We'll try a different approach - check via the events endpoint
    
    print("⚠️  Note: PostHog REST API requires a Personal API Key for querying events.")
    print("   The project API key (phx_*) is only for sending events.")
    print()
    print("📊 Alternative verification methods:")
    print()
    
    # Method 1: Check backend logs
    print("1️⃣  Check Backend Logs:")
    print("   Look for PostHog capture logs in backend output")
    print("   Search for: 'Analytics event captured'")
    print()
    
    # Method 2: Use PostHog Python client to check
    print("2️⃣  Check via PostHog Dashboard:")
    print(f"   - Go to: {POSTHOG_HOST}")
    print(f"   - Navigate to: Activity / Events")
    print(f"   - Filter by distinct_id: {TEST_DISTINCT_ID}")
    print(f"   - Look for events:")
    for event in EXPECTED_EVENTS:
        print(f"     • {event}")
    print()
    
    # Method 3: Try to use PostHog's query API if we have personal key
    personal_key = os.getenv("POSTHOG_PERSONAL_API_KEY")
    if personal_key:
        print("3️⃣  Querying PostHog API directly...")
        try:
            # PostHog query endpoint
            url = f"{POSTHOG_HOST}/api/projects/query"
            headers = {
                "Authorization": f"Bearer {personal_key}",
                "Content-Type": "application/json",
            }
            
            # Query for recent events
            query = {
                "kind": "EventsQuery",
                "select": ["event", "distinct_id", "timestamp", "properties"],
                "where": [
                    {
                        "type": "event",
                        "id": "event",
                        "name": "event",
                        "operator": "exact",
                        "value": EXPECTED_EVENTS,
                    }
                ],
                "limit": 10,
            }
            
            response = requests.post(url, json=query, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {len(data.get('results', []))} matching events")
                for result in data.get('results', [])[:5]:
                    print(f"      - {result.get('event')} at {result.get('timestamp')}")
            else:
                print(f"   ⚠️  API returned status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ⚠️  API query failed: {e}")
    else:
        print("3️⃣  Query PostHog API (requires POSTHOG_PERSONAL_API_KEY):")
        print("   Set POSTHOG_PERSONAL_API_KEY environment variable to enable")
        print("   This is different from the project API key")
    print()
    
    # Method 4: Check if events are in PostHog by making a test query
    print("4️⃣  Check Backend Analytics Service:")
    print("   The backend analytics service logs when events are sent")
    print("   Check backend logs for: 'Analytics event captured'")
    print()
    
    # Try to verify by checking the PostHog client status
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from app.services.analytics import get_analytics_client
        
        analytics = get_analytics_client()
        if analytics.enabled:
            print("✅ PostHog client is enabled and configured")
            print(f"   Host: {analytics.posthog_host}")
            print(f"   Env: {analytics.env}")
        else:
            print("❌ PostHog client is not enabled")
    except Exception as e:
        print(f"⚠️  Could not check analytics client: {e}")
    
    print()
    print("💡 Tip: Events may take 30-60 seconds to appear in PostHog dashboard")
    print("   Try clicking 'Reload' button in PostHog Activity feed")

if __name__ == "__main__":
    verify_events()
