#!/bin/bash
# Test demo simulation endpoint

API_BASE_URL="${API_BASE_URL:-https://api.nerava.network}"
INTERNAL_SECRET="${INTERNAL_SECRET:-your-secret-here}"
DRIVER_PHONE="${1:-+17133056318}"
MERCHANT_ID="${2:-merchant-123}"
CHARGER_ID="${3:-charger-456}"

echo "=== Testing Demo Simulation ==="
echo ""
echo "Driver Phone: $DRIVER_PHONE"
echo "Merchant ID: $MERCHANT_ID"
echo "Charger ID: $CHARGER_ID"
echo ""

if [ "$INTERNAL_SECRET" = "your-secret-here" ]; then
  echo "⚠️  Warning: INTERNAL_SECRET not set. Set it as an environment variable."
  echo "   Example: INTERNAL_SECRET=your-secret ./scripts/test-demo-simulation.sh"
  exit 1
fi

RESPONSE=$(curl -s -X POST "$API_BASE_URL/v1/admin/internal/demo/simulate-verified-visit" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -d "{
    \"driver_phone\": \"$DRIVER_PHONE\",
    \"merchant_id\": \"$MERCHANT_ID\",
    \"charger_id\": \"$CHARGER_ID\"
  }" \
  -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" != "200" ]; then
  echo "❌ Failed to simulate visit"
  echo "Status: $HTTP_STATUS"
  echo "Response: $BODY"
  exit 1
fi

echo "✅ Visit simulated successfully!"
echo ""
echo "$BODY" | python3 -m json.tool




