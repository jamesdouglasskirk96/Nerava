#!/bin/bash
# Send geofence test events via backend debug API (same method as yesterday)

API_BASE="http://localhost:8001"

echo "📤 Sending 3 geofence events via backend debug endpoint..."
echo "   (Same method that worked yesterday)"
echo ""

# Check backend is running
if ! curl -s "$API_BASE/health" > /dev/null 2>&1; then
    echo "❌ Backend not running on $API_BASE"
    echo "   Start backend: cd backend && python3 -m uvicorn app.main_simple:app --reload --port 8001"
    exit 1
fi

# Check PostHog status
echo "1️⃣ Checking PostHog configuration..."
STATUS=$(curl -s "$API_BASE/debug/analytics/posthog/status" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$STATUS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"   Configured: {d.get('configured', False)}\"); print(f\"   Host: {d.get('host', 'N/A')}\")" 2>/dev/null || echo "   Status check failed"
else
    echo "   ⚠️  Could not check PostHog status"
fi
echo ""

# Event 1: User entered charger radius
echo "2️⃣ Sending: ios.geofence.charger.entered"
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "ios.geofence.charger.entered",
    "distinct_id": "driver:test_driver_geofence_demo",
    "properties": {
      "charger_id": "canyon_ridge_tesla",
      "charger_name": "Tesla Supercharger - Canyon Ridge",
      "charger_address": "500 W Canyon Ridge Dr, Austin, TX 78753",
      "lat": 30.4037865,
      "lng": -97.6730044,
      "accuracy_m": 10.0,
      "radius_m": 400,
      "distance_to_charger_m": 15.0,
      "source": "ios_native",
      "test_event": true,
      "demo_location": "asadas_grill_area"
    }
  }' | python3 -m json.tool 2>/dev/null || echo "   ✅ Event sent"
echo ""

sleep 1

# Event 2: User entered merchant radius
echo "3️⃣ Sending: ios.geofence.merchant.entered"
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "ios.geofence.merchant.entered",
    "distinct_id": "driver:test_driver_geofence_demo",
    "properties": {
      "merchant_id": "asadas_grill_canyon_ridge",
      "merchant_name": "Asadas Grill",
      "merchant_address": "501 W Canyon Ridge Dr, Austin, TX 78753",
      "charger_id": "canyon_ridge_tesla",
      "lat": 30.4028469,
      "lng": -97.6718938,
      "accuracy_m": 8.0,
      "radius_m": 40,
      "distance_to_merchant_m": 5.0,
      "distance_to_charger_m": 149.0,
      "source": "ios_native",
      "test_event": true,
      "demo_location": "asadas_grill_area"
    }
  }' | python3 -m json.tool 2>/dev/null || echo "   ✅ Event sent"
echo ""

sleep 1

# Event 3: User left merchant radius
echo "4️⃣ Sending: ios.geofence.merchant.exited"
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "ios.geofence.merchant.exited",
    "distinct_id": "driver:test_driver_geofence_demo",
    "properties": {
      "merchant_id": "asadas_grill_canyon_ridge",
      "merchant_name": "Asadas Grill",
      "merchant_address": "501 W Canyon Ridge Dr, Austin, TX 78753",
      "charger_id": "canyon_ridge_tesla",
      "lat": 30.4037969,
      "lng": -97.6709438,
      "accuracy_m": 12.0,
      "radius_m": 40,
      "distance_to_merchant_m": 120.0,
      "distance_to_charger_m": 150.0,
      "source": "ios_native",
      "test_event": true,
      "demo_location": "asadas_grill_area"
    }
  }' | python3 -m json.tool 2>/dev/null || echo "   ✅ Event sent"
echo ""

echo "✅ All 3 geofence events sent!"
echo ""
echo "📊 Check PostHog dashboard:"
echo "   - Filter by distinct_id: driver:test_driver_geofence_demo"
echo "   - Look for events: ios.geofence.*"
echo "   - Check 'Last hour' time range"
echo "   - Events include geo coordinates (lat/lng)"
