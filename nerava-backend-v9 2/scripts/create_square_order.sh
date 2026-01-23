#!/bin/bash
# Script to create a Square order and payment for sandbox merchant
# Usage: ./scripts/create_square_order.sh [merchant_id] [amount_cents] [demo_admin_key]

MERCHANT_ID="${1:-e9adf8d7-6730-4253-93b4-8e6f3b809581}"
AMOUNT_CENTS="${2:-850}"
DEMO_ADMIN_KEY="${3:-${DEMO_ADMIN_KEY:-demo-admin-key}}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8001}"

echo "Creating Square order for merchant: $MERCHANT_ID"
echo "Amount: \$$(echo "scale=2; $AMOUNT_CENTS/100" | bc)"
echo ""

# Step 1: Create Order
echo "Step 1: Creating Square order..."
ORDER_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/demo/square/orders/create" \
  -H "Content-Type: application/json" \
  -H "X-Demo-Admin-Key: ${DEMO_ADMIN_KEY}" \
  -d "{
    \"merchant_id\": \"${MERCHANT_ID}\",
    \"amount_cents\": ${AMOUNT_CENTS},
    \"name\": \"Coffee\"
  }")

ORDER_ID=$(echo "$ORDER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('order_id', ''))" 2>/dev/null)

if [ -z "$ORDER_ID" ]; then
  echo "ERROR: Failed to create order"
  echo "Response: $ORDER_RESPONSE"
  exit 1
fi

echo "✓ Order created: $ORDER_ID"
echo ""

# Step 2: Create Payment
echo "Step 2: Creating payment for order..."
PAYMENT_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/demo/square/payments/create" \
  -H "Content-Type: application/json" \
  -H "X-Demo-Admin-Key: ${DEMO_ADMIN_KEY}" \
  -d "{
    \"merchant_id\": \"${MERCHANT_ID}\",
    \"order_id\": \"${ORDER_ID}\",
    \"amount_cents\": ${AMOUNT_CENTS}
  }")

PAYMENT_STATUS=$(echo "$PAYMENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
PAYMENT_ID=$(echo "$PAYMENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('payment_id', ''))" 2>/dev/null)

if [ -z "$PAYMENT_ID" ]; then
  echo "ERROR: Failed to create payment"
  echo "Response: $PAYMENT_RESPONSE"
  exit 1
fi

echo "✓ Payment created: $PAYMENT_ID"
echo "✓ Payment status: $PAYMENT_STATUS"
echo ""
echo "Order ID: $ORDER_ID"
echo "Payment ID: $PAYMENT_ID"
echo ""
echo "You can now redeem this order at:"
echo "http://127.0.0.1:8001/app/checkout.html?token=YmcvPMCgnJ46fXzdnGgD16eVv64v2xpDKsJOwx0Y_9g"

