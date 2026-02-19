#!/bin/bash
# Test OTP flow - sends OTP and waits for verification

API_BASE_URL="${API_BASE_URL:-https://api.nerava.network}"
PHONE="${1:-+17133056318}"

echo "=== Testing OTP Flow ==="
echo ""
echo "Phone: $PHONE"
echo "API: $API_BASE_URL"
echo ""

# Step 1: Start OTP
echo "Step 1: Sending OTP..."
RESPONSE=$(curl -s -X POST "$API_BASE_URL/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\"}" \
  -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" != "200" ]; then
  echo "❌ Failed to send OTP"
  echo "Status: $HTTP_STATUS"
  echo "Response: $BODY"
  exit 1
fi

echo "✅ OTP sent successfully!"
echo ""
echo "Please check your phone for the verification code."
echo ""
read -p "Enter the 6-digit code: " CODE

# Step 2: Verify OTP
echo ""
echo "Step 2: Verifying OTP..."
VERIFY_RESPONSE=$(curl -s -X POST "$API_BASE_URL/v1/auth/otp/verify" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\", \"code\": \"$CODE\"}" \
  -w "\nHTTP_STATUS:%{http_code}")

VERIFY_STATUS=$(echo "$VERIFY_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
VERIFY_BODY=$(echo "$VERIFY_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$VERIFY_STATUS" != "200" ]; then
  echo "❌ Failed to verify OTP"
  echo "Status: $VERIFY_STATUS"
  echo "Response: $VERIFY_BODY"
  exit 1
fi

echo "✅ OTP verified successfully!"
echo ""
echo "Access Token:"
echo "$VERIFY_BODY" | python3 -m json.tool | grep -A 1 "access_token" | head -2

# Extract token for demo simulation
ACCESS_TOKEN=$(echo "$VERIFY_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$ACCESS_TOKEN" ]; then
  echo ""
  echo "Token saved. You can now use this for authenticated requests."
  echo "Example: export ACCESS_TOKEN=\"$ACCESS_TOKEN\""
fi




