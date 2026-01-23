# Fix OTP Endpoint Timeout - Diagnostic & Repair

**Date:** 2026-01-23
**Issue:** `/v1/auth/otp/start` endpoint returns 504 timeout
**Last Working:** Yesterday (January 22, 2026)
**Symptom:** Health check passes, dev login works, but OTP/magic link endpoints timeout after 60s

---

## Context

The OTP endpoint was working yesterday. Today it times out. Recent changes include:
- P0-P3 cleanup commits (removed secrets from git tracking, not from AWS)
- Cursor may have removed/changed secrets during a push to GitHub

The API health check works:
```bash
curl https://api.nerava.network/health
# Returns: {"ok":true}
```

Dev login works (bypasses Twilio):
```bash
curl -X POST https://api.nerava.network/v1/auth/dev/login -H "Content-Type: application/json"
# Returns: access_token, refresh_token, user object
```

OTP times out:
```bash
curl -X POST https://api.nerava.network/v1/auth/otp/start \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}'
# Times out after 60s with 504
```

---

## Diagnosis Steps

### Step 1: Check AWS Environment Variables

The OTP service requires these environment variables in AWS (ECS/App Runner):

| Variable | Required | Purpose |
|----------|----------|---------|
| `OTP_PROVIDER` | Yes | Must be `twilio_verify` or `twilio_sms` (not `stub` in prod) |
| `TWILIO_ACCOUNT_SID` | Yes | Twilio account identifier (starts with `AC`) |
| `TWILIO_AUTH_TOKEN` | Yes | Twilio auth token |
| `TWILIO_VERIFY_SERVICE_SID` | For `twilio_verify` | Verify service ID (starts with `VA`) |
| `OTP_FROM_NUMBER` | For `twilio_sms` | Phone number to send from |
| `TWILIO_TIMEOUT_SECONDS` | No | Timeout for Twilio API calls (default: 30) |
| `ENV` | Yes | Must be `prod` for production validation |

**Check in AWS Console:**
1. Go to AWS Console > ECS > Clusters > nerava-cluster > nerava-backend service
2. Click on the running task
3. View task definition > Container definitions > Environment variables
4. Verify all Twilio variables are present and have values

**Or check via CLI:**
```bash
aws ecs describe-task-definition --task-definition nerava-backend --query 'taskDefinition.containerDefinitions[0].environment' --output table
```

### Step 2: Check Twilio Console

1. Go to https://console.twilio.com
2. Verify account is active (not suspended)
3. Check Verify > Services > your service is active
4. Note the Verify Service SID (starts with `VA`)
5. Check usage/logs for any errors from today

### Step 3: Check Backend Logs

```bash
# Get recent logs from ECS
aws logs tail /ecs/nerava-backend --since 30m --follow

# Or filter for OTP-related logs
aws logs filter-log-events \
  --log-group-name /ecs/nerava-backend \
  --filter-pattern "OTP" \
  --start-time $(date -d '30 minutes ago' +%s000)
```

Look for:
- `[OTP] Using Twilio Verify provider` - confirms provider initialized
- `[OTP] OTP sent successfully` - confirms SMS sent
- Any errors like "Invalid credentials" or "Service not found"

### Step 4: Use Diagnostic Script

**RECOMMENDED:** Use the built-in diagnostic script instead of manual testing:

```bash
# Run full diagnostic
python backend/scripts/check_twilio_config.py

# Check AWS ECS configuration
python backend/scripts/check_twilio_config.py --check-aws

# Test sending OTP
python backend/scripts/check_twilio_config.py --test-phone +17133056318
```

The script will automatically:
- Check all environment variables
- Validate Twilio credentials
- Test Verify service access
- Optionally send a test OTP

**Manual Testing (if script unavailable):**

```python
# test_twilio.py
import os
from twilio.rest import Client

account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
verify_sid = os.environ.get('TWILIO_VERIFY_SERVICE_SID')

print(f"Account SID: {account_sid[:8]}..." if account_sid else "MISSING")
print(f"Auth Token: {'*' * 8}" if auth_token else "MISSING")
print(f"Verify SID: {verify_sid[:8]}..." if verify_sid else "MISSING")

if all([account_sid, auth_token, verify_sid]):
    client = Client(account_sid, auth_token)
    try:
        # Send test verification
        verification = client.verify.v2.services(verify_sid).verifications.create(
            to='+17133056318',
            channel='sms'
        )
        print(f"SUCCESS: Verification SID = {verification.sid}")
        print(f"Status: {verification.status}")
    except Exception as e:
        print(f"ERROR: {e}")
else:
    print("ERROR: Missing required environment variables")
```

---

## Common Failure Modes

### 1. Missing Environment Variables
**Symptom:** Timeout (service hangs trying to connect)
**Fix:** Add missing variables to ECS task definition

### 2. Invalid/Expired Twilio Credentials
**Symptom:** Timeout or 500 error
**Fix:** Rotate credentials in Twilio Console, update AWS

### 3. Twilio Verify Service Deleted/Disabled
**Symptom:** Timeout or error in logs
**Fix:** Create new Verify service in Twilio Console, update `TWILIO_VERIFY_SERVICE_SID`

### 4. OTP_PROVIDER Set to "stub"
**Symptom:** Startup fails with validation error OR stub returns immediately (not timeout)
**Fix:** Set `OTP_PROVIDER=twilio_verify`

### 5. Network/Firewall Issues
**Symptom:** Timeout connecting to Twilio API
**Fix:** Check VPC security groups allow outbound HTTPS (443)

### 6. Async Event Loop Blocking (FIXED)
**Symptom:** Timeout after 60s, event loop blocked
**Root Cause:** Twilio SDK calls are synchronous and block the async event loop
**Fix:** ✅ **IMPLEMENTED** - Twilio calls now run in executor thread with explicit timeout

---

## Repair Actions

### If Environment Variables Are Missing

Update ECS task definition with required variables:

```bash
# Get current task definition
aws ecs describe-task-definition --task-definition nerava-backend > task-def.json

# Edit task-def.json to add/update environment variables:
# {
#   "name": "OTP_PROVIDER",
#   "value": "twilio_verify"
# },
# {
#   "name": "TWILIO_ACCOUNT_SID",
#   "value": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# },
# {
#   "name": "TWILIO_AUTH_TOKEN",
#   "value": "your-auth-token"
# },
# {
#   "name": "TWILIO_VERIFY_SERVICE_SID",
#   "value": "VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# }

# Register new task definition
aws ecs register-task-definition --cli-input-json file://task-def-updated.json

# Update service to use new task definition
aws ecs update-service --cluster nerava-cluster --service nerava-backend --force-new-deployment
```

### If Twilio Credentials Need Rotation

1. **In Twilio Console:**
   - Go to Account > API keys & tokens
   - Create new Auth Token or rotate existing
   - Note the new token

2. **In AWS:**
   - Update `TWILIO_AUTH_TOKEN` in task definition
   - Deploy new task

### If Verify Service Needs Recreation

1. **In Twilio Console:**
   - Go to Verify > Services
   - Create new service named "Nerava OTP"
   - Note the Service SID (starts with `VA`)
   - Configure: SMS channel enabled, code length 6

2. **In AWS:**
   - Update `TWILIO_VERIFY_SERVICE_SID` in task definition
   - Deploy new task

---

## Verification After Fix

```bash
# 1. Wait for deployment to complete
aws ecs wait services-stable --cluster nerava-cluster --services nerava-backend

# 2. Test health endpoint
curl https://api.nerava.network/health

# 3. Test OTP endpoint
curl -X POST https://api.nerava.network/v1/auth/otp/start \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}'
# Should return: {"otp_sent": true}

# 4. Check your phone for SMS with 6-digit code
```

---

## Root Cause: Async Event Loop Blocking

**IMPLEMENTED FIX:** The Twilio SDK calls are synchronous and blocking. When called directly in async functions, they block the FastAPI event loop, causing timeouts.

### Solution Implemented

1. **Added explicit timeout configuration** to Twilio HTTP client (default: 30 seconds, configurable via `TWILIO_TIMEOUT_SECONDS`)
2. **Run Twilio calls in executor thread** using `asyncio.to_thread()` to avoid blocking the event loop
3. **Improved error handling** with specific error messages for timeouts vs. credential errors
4. **Enhanced logging** with phone last4 and error types

### Code Changes

**`backend/app/services/auth/twilio_verify.py`:**
- Added `TwilioHttpClient` with explicit timeout
- Wrapped Twilio API calls in `asyncio.to_thread()` to run in executor
- Added timeout error handling with `asyncio.wait_for()`
- Improved error messages and logging

**`backend/app/services/auth/twilio_sms.py`:**
- Same pattern applied for consistency

**`backend/app/core/config.py`:**
- Added `TWILIO_TIMEOUT_SECONDS` environment variable (default: 30 seconds)

### Using the Diagnostic Script

A diagnostic script is available to check configuration:

```bash
# Check environment variables and test Twilio credentials
python backend/scripts/check_twilio_config.py

# Also check AWS ECS task definition (requires AWS CLI)
python backend/scripts/check_twilio_config.py --check-aws

# Test sending OTP to a phone number
python backend/scripts/check_twilio_config.py --test-phone +17133056318
```

The script will:
1. Validate all required environment variables are set
2. Check AWS ECS task definition (if AWS CLI configured)
3. Test Twilio credentials directly
4. Verify Verify service exists and is active
5. Optionally test sending OTP to a phone number

---

## Checklist

- [ ] AWS ECS task definition has all Twilio env vars
- [ ] `OTP_PROVIDER` is set to `twilio_verify` (not `stub`)
- [ ] Twilio account is active and not suspended
- [ ] Twilio Verify service exists and is enabled
- [ ] Auth token is valid (not rotated/expired)
- [ ] VPC security groups allow outbound HTTPS
- [ ] Backend logs show successful provider initialization
- [ ] Test OTP request returns `{"otp_sent": true}`
- [ ] SMS received on phone with 6-digit code

---

## Related Files

- `backend/app/core/config.py` - Environment variable definitions (includes `TWILIO_TIMEOUT_SECONDS`)
- `backend/app/services/auth/otp_factory.py` - Provider selection logic
- `backend/app/services/auth/twilio_verify.py` - Twilio Verify implementation (with timeout & executor)
- `backend/app/services/auth/twilio_sms.py` - Twilio SMS implementation (with timeout & executor)
- `backend/app/services/otp_service_v2.py` - OTP service with rate limiting
- `backend/app/routers/auth.py` - `/auth/otp/start` endpoint (line 346)
- `backend/scripts/check_twilio_config.py` - Diagnostic script for troubleshooting

---

## Quick Reference: Twilio Verify Flow

```
1. Client calls POST /v1/auth/otp/start {phone: "+1..."}
2. Backend normalizes phone number
3. Backend checks rate limits (5 attempts per phone per 15 min)
4. Backend calls Twilio Verify API to send SMS
5. Twilio sends SMS with 6-digit code to phone
6. Backend returns {otp_sent: true}
7. User enters code in app
8. Client calls POST /v1/auth/otp/verify {phone: "+1...", code: "123456"}
9. Backend verifies with Twilio
10. Backend creates user (if new) and returns access_token
```

---

**End of Diagnostic Prompt**
