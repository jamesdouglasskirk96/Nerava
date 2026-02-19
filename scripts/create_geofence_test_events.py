#!/usr/bin/env python3
"""
Create test PostHog events for geofence entry/exit tracking.

This script creates 3 test events:
1. User entered charger radius
2. User entered merchant radius  
3. User left merchant radius

Uses real coordinates from Asadas Grill and Canyon Ridge charger.
"""

import os
import sys
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.analytics import get_analytics_client

# Real coordinates from production data
ASADAS_GRILL_LAT = 30.4027969
ASADAS_GRILL_LNG = -97.6719438
ASADAS_GRILL_ADDRESS = "501 W Canyon Ridge Dr, Austin, TX 78753"

# Charger coordinates (Tesla Supercharger near Asadas)
CHARGER_LAT = 30.403686500000003
CHARGER_LNG = -97.6731044
CHARGER_ID = "canyon_ridge_tesla"
CHARGER_ADDRESS = "500 W Canyon Ridge Dr, Austin, TX 78753"

# Geofence radii (from SessionConfig)
CHARGER_INTENT_RADIUS_M = 400  # User enters this zone to start monitoring
MERCHANT_UNLOCK_RADIUS_M = 40  # User must be within this radius to unlock merchant

# Test user ID
TEST_USER_ID = "test_driver_geofence_demo"
TEST_DISTINCT_ID = f"driver:{TEST_USER_ID}"

def create_test_events(dry_run=False):
    """Create 3 test PostHog events with real coordinates"""
    
    analytics = get_analytics_client()
    
    if not analytics.enabled and not dry_run:
        print("❌ PostHog not configured. Set POSTHOG_KEY environment variable.")
        print("   Running in DRY-RUN mode to show what would be sent...")
        print()
        dry_run = True
    
    if dry_run:
        print("🔍 DRY-RUN MODE: Showing event details (not sending to PostHog)")
        print()
    
    print("📍 Creating geofence test events with real coordinates...")
    print(f"   Charger: {CHARGER_ADDRESS}")
    print(f"   Merchant: {ASADAS_GRILL_ADDRESS}")
    print()
    
    # Event 1: User entered charger radius
    print("1️⃣  Creating event: user_entered_charger_radius")
    event1_data = {
        "event": "ios.geofence.charger.entered",
        "distinct_id": TEST_DISTINCT_ID,
        "user_id": TEST_USER_ID,
        "charger_id": CHARGER_ID,
        "lat": CHARGER_LAT + 0.0001,  # Slightly inside radius (simulate entry point)
        "lng": CHARGER_LNG + 0.0001,
        "accuracy_m": 10.0,
        "properties": {
            "charger_name": "Tesla Supercharger - Canyon Ridge",
            "charger_address": CHARGER_ADDRESS,
            "radius_m": CHARGER_INTENT_RADIUS_M,
            "distance_to_charger_m": 15.0,  # Approximate distance
            "source": "ios_native",
            "test_event": True,
            "demo_location": "asadas_grill_area",
        }
    }
    
    if dry_run:
        import json
        print(f"   Event: {event1_data['event']}")
        print(f"   Distinct ID: {event1_data['distinct_id']}")
        print(f"   Location: lat={event1_data['lat']:.7f}, lng={event1_data['lng']:.7f}")
        print(f"   Properties: {json.dumps(event1_data['properties'], indent=6)}")
    else:
        analytics.capture(**event1_data)
    print("   ✅ Event sent" if not dry_run else "   ✅ Event prepared (dry-run)")
    print()
    
    # Event 2: User entered merchant radius
    print("2️⃣  Creating event: user_entered_merchant_radius")
    event2_data = {
        "event": "ios.geofence.merchant.entered",
        "distinct_id": TEST_DISTINCT_ID,
        "user_id": TEST_USER_ID,
        "merchant_id": "asadas_grill_canyon_ridge",
        "charger_id": CHARGER_ID,
        "lat": ASADAS_GRILL_LAT + 0.00005,  # Slightly inside merchant radius
        "lng": ASADAS_GRILL_LNG + 0.00005,
        "accuracy_m": 8.0,
        "properties": {
            "merchant_name": "Asadas Grill",
            "merchant_address": ASADAS_GRILL_ADDRESS,
            "radius_m": MERCHANT_UNLOCK_RADIUS_M,
            "distance_to_merchant_m": 5.0,  # Approximate distance
            "distance_to_charger_m": 149.0,  # Known distance from data
            "source": "ios_native",
            "test_event": True,
            "demo_location": "asadas_grill_area",
        }
    }
    
    if dry_run:
        import json
        print(f"   Event: {event2_data['event']}")
        print(f"   Distinct ID: {event2_data['distinct_id']}")
        print(f"   Location: lat={event2_data['lat']:.7f}, lng={event2_data['lng']:.7f}")
        print(f"   Properties: {json.dumps(event2_data['properties'], indent=6)}")
    else:
        analytics.capture(**event2_data)
    print("   ✅ Event sent" if not dry_run else "   ✅ Event prepared (dry-run)")
    print()
    
    # Event 3: User left merchant radius
    print("3️⃣  Creating event: user_left_merchant_radius")
    event3_data = {
        "event": "ios.geofence.merchant.exited",
        "distinct_id": TEST_DISTINCT_ID,
        "user_id": TEST_USER_ID,
        "merchant_id": "asadas_grill_canyon_ridge",
        "charger_id": CHARGER_ID,
        "lat": ASADAS_GRILL_LAT + 0.001,  # Outside merchant radius (simulate exit point)
        "lng": ASADAS_GRILL_LNG + 0.001,
        "accuracy_m": 12.0,
        "properties": {
            "merchant_name": "Asadas Grill",
            "merchant_address": ASADAS_GRILL_ADDRESS,
            "radius_m": MERCHANT_UNLOCK_RADIUS_M,
            "distance_to_merchant_m": 120.0,  # Approximate distance (outside radius)
            "distance_to_charger_m": 150.0,
            "source": "ios_native",
            "test_event": True,
            "demo_location": "asadas_grill_area",
        }
    }
    
    if dry_run:
        import json
        print(f"   Event: {event3_data['event']}")
        print(f"   Distinct ID: {event3_data['distinct_id']}")
        print(f"   Location: lat={event3_data['lat']:.7f}, lng={event3_data['lng']:.7f}")
        print(f"   Properties: {json.dumps(event3_data['properties'], indent=6)}")
    else:
        analytics.capture(**event3_data)
    print("   ✅ Event sent" if not dry_run else "   ✅ Event prepared (dry-run)")
    print()
    
    if dry_run:
        print("✅ All 3 test events prepared (DRY-RUN mode)")
        print()
        print("⚠️  To actually send events to PostHog:")
        print("   1. Set POSTHOG_KEY in backend/.env")
        print("   2. Or export POSTHOG_KEY environment variable")
        print("   3. Run script again")
    else:
        print("✅ All 3 test events created successfully!")
        print()
        print("📊 Check PostHog dashboard:")
        print(f"   - Filter by distinct_id: {TEST_DISTINCT_ID}")
        print("   - Look for events:")
        print("     • ios.geofence.charger.entered")
        print("     • ios.geofence.merchant.entered")
        print("     • ios.geofence.merchant.exited")
    
    print()
    print("📍 Events include geo coordinates:")
    print(f"   - Charger: lat={CHARGER_LAT}, lng={CHARGER_LNG}")
    print(f"   - Merchant: lat={ASADAS_GRILL_LAT}, lng={ASADAS_GRILL_LNG}")
    
    return True

if __name__ == "__main__":
    success = create_test_events()
    sys.exit(0 if success else 1)
