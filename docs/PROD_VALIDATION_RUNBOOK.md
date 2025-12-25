# Production Validation Runbook

**Generated:** 2025-01-27  
**Purpose:** Manual validation steps for production deployment

---

## Prerequisites

### Environment Variables (Local Testing)

```bash
# Point to AWS App Runner instance
export BASE_URL="https://your-app-runner-url.us-east-1.awsapprunner.com"

# Or test locally
export BASE_URL="http://localhost:8001"

# For admin tests
export ADMIN_TOKEN="<jwt_token_from_admin_login>"
```

### Required Tools

- `curl` (for API testing)
- `jq` (optional, for JSON parsing)
- Admin JWT token (obtain via login)

---

## Automated Pre-Launch Validation

**Canonical validation step:** Run `scripts/prod_validation_bundle.sh` before production deployment.

This script orchestrates all critical validation checks:

1. **Unit and Integration Tests** - Runs `pytest -q` to verify test suite passes
2. **Production Quality Gate** - Runs `prod_gate.sh` to check P0 production readiness items
3. **Admin Smoke Tests** - Runs `admin_smoke_test.sh` to verify admin endpoints are functional

### Usage

```bash
# Set required environment variables
export NERAVA_BACKEND_URL="https://your-backend-url.com"
export BASE_URL="https://your-backend-url.com"  # Can be same as NERAVA_BACKEND_URL
export ADMIN_TOKEN="your-jwt-token-here"

# Run validation bundle
./scripts/prod_validation_bundle.sh
```

The script will:
- **Fail fast** on first failure (exits immediately if any check fails)
- **Redact secrets** from output (tokens, API keys, etc.)
- **Print clear PASS/FAIL summary** for each check
- **Exit with code 0** only if all checks pass

**Note:** This automated validation should be run before every production deployment. The manual steps below can be used for detailed troubleshooting or ad-hoc validation.

---

## Manual Validation Steps

The following sections provide detailed manual validation steps for troubleshooting or specific endpoint testing.

## Health Checks

### 1. Liveness Probe

```bash
curl -v "$BASE_URL/healthz"
```

**Expected:** HTTP 200 OK

**Response:**
```
OK
```

---

### 2. Readiness Probe

```bash
curl -v "$BASE_URL/readyz" | jq .
```

**Expected:** HTTP 200 OK with structured JSON

**Response:**
```json
{
  "ready": true,
  "checks": {
    "startup_validation": {
      "status": "ok",
      "error": null
    },
    "database": {
      "status": "ok",
      "error": null
    },
    "redis": {
      "status": "ok",
      "error": null
    }
  }
}
```

**If not ready:** Check `checks` object for which dependency failed.

---

## Authentication & Authorization

### 3. User Registration

```bash
curl -X POST "$BASE_URL/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "display_name": "Test User"
  }'
```

**Expected:** HTTP 200 OK with JWT token

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Save token:**
```bash
export USER_TOKEN="<access_token_from_response>"
```

---

### 4. User Login

```bash
curl -X POST "$BASE_URL/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

**Expected:** HTTP 200 OK with JWT token

**Note:** In production, magic link may be preferred (see below).

---

### 5. Magic Link (Email-Only Auth)

**Request magic link:**
```bash
curl -X POST "$BASE_URL/v1/auth/magic_link/request" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }'
```

**Expected:** HTTP 200 OK

**In non-prod:** Response includes `magic_link_url` for testing  
**In prod:** Magic link sent via email (check email inbox)

**Verify magic link:**
```bash
curl -X POST "$BASE_URL/v1/auth/magic_link/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<magic_link_token_from_email_or_debug_response>"
  }'
```

**Expected:** HTTP 200 OK with JWT token

---

### 6. Get Current User

```bash
curl "$BASE_URL/v1/auth/me" \
  -H "Authorization: Bearer $USER_TOKEN"
```

**Expected:** HTTP 200 OK with user info

**Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "display_name": "Test User",
  "role_flags": "driver"
}
```

---

## Wallet Operations

### 7. View Wallet Balance

```bash
curl "$BASE_URL/v1/drivers/me" \
  -H "Authorization: Bearer $USER_TOKEN"
```

**Expected:** HTTP 200 OK with wallet info

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "test@example.com"
  },
  "wallet": {
    "nova_balance": 0,
    "energy_reputation_score": 0
  }
}
```

---

### 8. Earn Nova (Demo Gating)

**Note:** In production, Nova is earned via purchase webhooks or charging sessions.  
**Demo mode:** May be disabled in production (`DEMO_MODE=false`).

**If demo mode enabled:**
```bash
# Nova accrual happens automatically when charging_detected=true
# This is handled by background service, not direct API call
```

**Verify Nova earned:**
```bash
curl "$BASE_URL/v1/drivers/me" \
  -H "Authorization: Bearer $USER_TOKEN" | jq .wallet.nova_balance
```

---

### 9. Redeem Nova (With Idempotency)

**Get merchant QR token first:**
```bash
# Query merchants to find a test merchant
curl "$BASE_URL/v1/drivers/merchants/nearby?lat=40.7128&lng=-74.0060" \
  -H "Authorization: Bearer $USER_TOKEN"
```

**Redeem Nova:**
```bash
curl -X POST "$BASE_URL/v1/checkout/redeem" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "<merchant_id>",
    "amount": 10,
    "idempotency_key": "test-redeem-$(date +%s)"
  }'
```

**Expected:** HTTP 200 OK

**Response:**
```json
{
  "success": true,
  "redemption_id": "...",
  "driver_balance": 90,
  "merchant_balance": 10
}
```

**Test idempotency (replay same request):**
```bash
# Use same idempotency_key
curl -X POST "$BASE_URL/v1/checkout/redeem" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "<merchant_id>",
    "amount": 10,
    "idempotency_key": "test-redeem-<same_timestamp>"
  }'
```

**Expected:** HTTP 200 OK with same redemption_id (idempotent)

---

## Admin Operations

### 10. Admin Login

```bash
# Login as admin user (must have admin role)
curl -X POST "$BASE_URL/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "<admin_password>"
  }'
```

**Save admin token:**
```bash
export ADMIN_TOKEN="<access_token_from_response>"
```

---

### 11. Admin Overview

```bash
curl "$BASE_URL/v1/admin/overview" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected:** HTTP 200 OK with statistics

**Response:**
```json
{
  "total_drivers": 10,
  "total_merchants": 5,
  "total_driver_nova": 1000,
  "total_merchant_nova": 500,
  "total_nova_outstanding": 1500,
  "total_stripe_usd": 0
}
```

---

### 12. Admin User Search

```bash
curl "$BASE_URL/v1/admin/users?query=test" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected:** HTTP 200 OK with user list

---

### 13. Admin Wallet View

```bash
curl "$BASE_URL/v1/admin/users/1/wallet" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected:** HTTP 200 OK with wallet details

---

### 14. Admin Wallet Adjustment

```bash
curl -X POST "$BASE_URL/v1/admin/users/1/wallet/adjust" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_cents": 1000,
    "reason": "Test adjustment"
  }'
```

**Expected:** HTTP 200 OK

**Response:**
```json
{
  "success": true,
  "user_id": 1,
  "amount_cents": 1000,
  "before_balance_cents": 0,
  "after_balance_cents": 1000
}
```

---

## Fraud Abuse Checks

### 15. Rate Limit Trigger

**Test rate limiting on magic link endpoint:**
```bash
# Send 4 requests rapidly (limit is typically 3/min)
for i in {1..4}; do
  curl -X POST "$BASE_URL/v1/auth/magic_link/request" \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}' \
    -w "\nHTTP Status: %{http_code}\n"
  sleep 1
done
```

**Expected:** First 3 requests succeed (200), 4th request fails (429 Too Many Requests)

---

### 16. Double Spend Attempt

**Attempt to redeem more Nova than available:**
```bash
# First, check current balance
BALANCE=$(curl -s "$BASE_URL/v1/drivers/me" \
  -H "Authorization: Bearer $USER_TOKEN" | jq -r .wallet.nova_balance)

# Attempt to redeem more than balance
curl -X POST "$BASE_URL/v1/checkout/redeem" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"merchant_id\": \"<merchant_id>\",
    \"amount\": $((BALANCE + 100)),
    \"idempotency_key\": \"test-double-spend-$(date +%s)\"
  }"
```

**Expected:** HTTP 400 Bad Request with "Insufficient Nova balance" error

---

### 17. Concurrent Redemption Attempt

**Test race condition protection:**
```bash
# Start two concurrent redemption requests with different idempotency keys
(
  curl -X POST "$BASE_URL/v1/checkout/redeem" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"merchant_id\": \"<merchant_id>\",
      \"amount\": 50,
      \"idempotency_key\": \"test-concurrent-1-$(date +%s)\"
    }" &
  
  curl -X POST "$BASE_URL/v1/checkout/redeem" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"merchant_id\": \"<merchant_id>\",
      \"amount\": 50,
      \"idempotency_key\": \"test-concurrent-2-$(date +%s)\"
    }" &
  
  wait
)
```

**Expected:** 
- If balance >= 100: Both succeed
- If balance < 100: One succeeds, one fails with "Insufficient Nova balance"
- Atomic balance check prevents double spend

---

### 18. Replay Webhook Attempt

**Test webhook replay protection (P0-1):**

**Create old webhook payload (10 minutes ago):**
```bash
OLD_TIMESTAMP=$(date -u -v-10M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d '10 minutes ago' +"%Y-%m-%dT%H:%M:%SZ")

curl -X POST "$BASE_URL/v1/webhooks/purchase" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: <webhook_secret_if_configured>" \
  -d "{
    \"provider\": \"clo\",
    \"transaction_id\": \"test-replay-$(date +%s)\",
    \"user_id\": 1,
    \"amount_cents\": 1000,
    \"ts\": \"$OLD_TIMESTAMP\",
    \"merchant_ext_id\": \"merchant-123\"
  }"
```

**Expected:** HTTP 400 Bad Request with "replay protection" or "too old" error

**Test recent webhook (2 minutes ago):**
```bash
RECENT_TIMESTAMP=$(date -u -v-2M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d '2 minutes ago' +"%Y-%m-%dT%H:%M:%SZ")

curl -X POST "$BASE_URL/v1/webhooks/purchase" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: <webhook_secret_if_configured>" \
  -d "{
    \"provider\": \"clo\",
    \"transaction_id\": \"test-recent-$(date +%s)\",
    \"user_id\": 1,
    \"amount_cents\": 1000,
    \"ts\": \"$RECENT_TIMESTAMP\",
    \"merchant_ext_id\": \"merchant-123\"
  }"
```

**Expected:** HTTP 200 OK (within 5-minute window)

---

### 19. Invalid Square Webhook Signature

**Test Square signature verification (P0-4):**

```bash
# If SQUARE_WEBHOOK_SIGNATURE_KEY is configured, test invalid signature
curl -X POST "$BASE_URL/v1/webhooks/purchase" \
  -H "Content-Type: application/json" \
  -H "X-Square-Signature: invalid_signature" \
  -d '{
    "type": "payment.created",
    "data": {
      "object": {
        "id": "test-payment-123",
        "amount_money": {
          "amount": 1000
        },
        "metadata": {
          "user_id": "1"
        }
      }
    }
  }'
```

**Expected:** HTTP 401 Unauthorized with "Invalid Square webhook signature" error

---

## Validation Checklist

### Health & Readiness
- [ ] `/healthz` returns 200
- [ ] `/readyz` returns 200 with all checks passing
- [ ] `/readyz` shows startup validation status
- [ ] `/readyz` shows database connectivity
- [ ] `/readyz` shows Redis connectivity

### Authentication
- [ ] User registration works
- [ ] User login works
- [ ] Magic link request works (email sent or debug URL returned)
- [ ] Magic link verification works
- [ ] JWT token is valid and accepted
- [ ] `/auth/me` returns user info
- [ ] Google Sign-In works (if configured)
- [ ] Apple Sign-In button is hidden if not configured (intentionally disabled for launch)

**Note on Apple Sign-In:**
- Apple Sign-In is intentionally disabled for launch
- Backend endpoint `/v1/auth/apple` exists and is functional
- Requires Apple Developer account + `APPLE_CLIENT_ID` configuration
- Frontend button is automatically hidden if `APPLE_CLIENT_ID` is not set
- Can be enabled post-launch by configuring `APPLE_CLIENT_ID` environment variable

### Wallet Operations
- [ ] Wallet balance can be read
- [ ] Nova balance is correct
- [ ] Redeem Nova works with idempotency
- [ ] Idempotency prevents duplicate redemptions
- [ ] Insufficient balance is rejected

### Admin Operations
- [ ] Admin login works
- [ ] Admin overview endpoint accessible
- [ ] Admin user search works
- [ ] Admin wallet view works
- [ ] Admin wallet adjustment works
- [ ] Non-admin users are rejected (403)

### Security & Fraud Protection
- [ ] Rate limiting triggers on magic link (429 after limit)
- [ ] Double spend attempt is rejected
- [ ] Concurrent redemptions are handled correctly (atomic)
- [ ] Old webhook replay is rejected (>5 minutes)
- [ ] Recent webhook is accepted (<5 minutes)
- [ ] Invalid Square signature is rejected (if configured)

---

## Troubleshooting

### Readiness Check Fails

**Check startup validation:**
```bash
curl "$BASE_URL/readyz" | jq .checks.startup_validation
```

**Common issues:**
- Missing `JWT_SECRET` → Set in environment
- Missing `TOKEN_ENCRYPTION_KEY` → Generate Fernet key
- `JWT_SECRET == DATABASE_URL` → Use different values
- Dev flags enabled in prod → Disable `NERAVA_DEV_ALLOW_*`

### Authentication Fails

**Check token:**
```bash
# Decode JWT (without verification)
echo "$USER_TOKEN" | cut -d. -f2 | base64 -d | jq .
```

**Check user role:**
```bash
curl "$BASE_URL/v1/auth/me" \
  -H "Authorization: Bearer $USER_TOKEN" | jq .role_flags
```

### Webhook Rejected

**Check webhook secret:**
- If `WEBHOOK_SHARED_SECRET` is set, include `X-Webhook-Secret` header
- If `SQUARE_WEBHOOK_SIGNATURE_KEY` is set, include valid `X-Square-Signature` header

**Check timestamp:**
- Webhook `ts` must be within 5 minutes of current time
- Use ISO 8601 format: `2025-01-27T12:00:00Z`

---

## Notes

- All endpoints require HTTPS in production
- JWT tokens expire after configured time (default: 60 minutes)
- Magic links expire after 15 minutes
- Rate limits are per IP/user (configurable)
- Webhook replay protection: 5-minute window
- Square signature verification: HMAC-SHA256 with base64 encoding

