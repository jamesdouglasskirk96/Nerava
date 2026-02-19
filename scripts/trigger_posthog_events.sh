#!/bin/bash
# Script to trigger 10 PostHog events via backend API and UI interactions

set -e

API_BASE="http://localhost:8001"
FRONTEND_URL="http://localhost:5173"

echo "🎯 Triggering 10 PostHog Events"
echo "================================"
echo ""

# Check if PostHog is configured
echo "1️⃣ Checking PostHog configuration..."
STATUS=$(curl -s "$API_BASE/debug/analytics/posthog/status")
CONFIGURED=$(echo $STATUS | python3 -c "import sys, json; print(json.load(sys.stdin)['configured'])")

if [ "$CONFIGURED" != "True" ]; then
    echo "⚠️  PostHog is not configured. Events will be logged but not sent to PostHog."
    echo "   To configure, add POSTHOG_KEY to backend/.env"
    echo ""
fi

# Backend Events (via debug endpoint)
echo "2️⃣ Triggering backend events..."

# Event 1: Test event
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"test.backend.event.1","distinct_id":"test-user-1","properties":{"source":"script","type":"test"}}' \
  | python3 -m json.tool || echo "Event 1 sent"

sleep 1

# Event 2: OTP sent simulation
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"server.otp.sent","distinct_id":"phone:test123","properties":{"phone_hash":"test123","provider":"stub","purpose":"login"}}' \
  | python3 -m json.tool || echo "Event 2 sent"

sleep 1

# Event 3: OTP verified simulation
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"server.otp.verified","distinct_id":"phone:test123","properties":{"phone_hash":"test123","provider":"stub"}}' \
  | python3 -m json.tool || echo "Event 3 sent"

sleep 1

# Event 4: Intent capture success
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"server.driver.intent.capture.success","distinct_id":"test-user-intent","properties":{"charger_id":"canyon_ridge_tesla","lat":30.2672,"lng":-97.7431}}' \
  | python3 -m json.tool || echo "Event 4 sent"

sleep 1

# Event 5: Merchant click simulation
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"driver_merchant_clicked","distinct_id":"test-user-ui","properties":{"merchant_id":"asadas_grill","merchant_name":"Asadas Grill","source":"carousel"}}' \
  | python3 -m json.tool || echo "Event 5 sent"

sleep 1

# Event 6: Merchant detail viewed
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"driver_merchant_detail_viewed","distinct_id":"test-user-ui","properties":{"merchant_id":"asadas_grill","merchant_name":"Asadas Grill"}}' \
  | python3 -m json.tool || echo "Event 6 sent"

sleep 1

# Event 7: Page view
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"driver.page.view","distinct_id":"test-user-ui","properties":{"page":"while_you_charge"}}' \
  | python3 -m json.tool || echo "Event 7 sent"

sleep 1

# Event 8: Session start
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"driver.session.start","distinct_id":"test-user-ui","properties":{"app":"driver","env":"dev"}}' \
  | python3 -m json.tool || echo "Event 8 sent"

sleep 1

# Event 9: Exclusive activate click
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"driver.exclusive.activate.click","distinct_id":"test-user-ui","properties":{"merchant_id":"asadas_grill","exclusive_title":"Free Margarita"}}' \
  | python3 -m json.tool || echo "Event 9 sent"

sleep 1

# Event 10: Get directions clicked
curl -s -X POST "$API_BASE/debug/analytics/posthog/test" \
  -H "Content-Type: application/json" \
  -d '{"event":"driver_get_directions_clicked","distinct_id":"test-user-ui","properties":{"merchant_id":"asadas_grill","merchant_name":"Asadas Grill"}}' \
  | python3 -m json.tool || echo "Event 10 sent"

echo ""
echo "✅ Triggered 10 events!"
echo ""
echo "📊 Check PostHog dashboard:"
echo "   - Events may take 30-60 seconds to appear"
echo "   - Filter by 'Last 1 hour' to see new events"
echo "   - Look for events with 'is_test: true' property"
echo ""
echo "💡 Note: If PostHog is not configured, events are logged but not sent."
echo "   Add POSTHOG_KEY to backend/.env to enable PostHog integration."
