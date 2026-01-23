# Production Proof Run - Day 1 Mandatory Checklist

**Purpose:** Internal "go/no-go" validation before production launch  
**Audience:** Operations team, Engineering leads  
**Time Required:** 15-30 minutes  
**Frequency:** Day 1 of production launch (mandatory)

---

## Prerequisites

- AWS Console access
- Admin JWT token for backend API
- Terminal access to repository
- Browser for manual verification
- Screenshot capability (for artifact capture)

---

## 1. Production Proof Run (Day 1 – Mandatory)

### Objective
Run automated validation suite to confirm production readiness. This is your internal "go/no-go" artifact.

### Steps

#### Step 1.1: Set Environment Variables

```bash
# Navigate to repository root
cd /path/to/Nerava

# Set required environment variables
export NERAVA_BACKEND_URL="https://your-backend-url.com"
export BASE_URL="https://your-backend-url.com"  # Can be same as NERAVA_BACKEND_URL
export ADMIN_TOKEN="your-jwt-admin-token-here"
```

**How to get ADMIN_TOKEN:**
1. Log in to admin console as admin user
2. Extract JWT token from browser DevTools → Application → Cookies
3. Or use: `curl -X POST "$BASE_URL/v1/auth/login" -H "Content-Type: application/json" -d '{"email":"admin@example.com","password":"..."}'`

#### Step 1.2: Run Validation Bundle

```bash
# Make script executable (if not already)
chmod +x scripts/prod_validation_bundle.sh

# Run validation bundle
./scripts/prod_validation_bundle.sh
```

**Expected Output:**
```
==========================================
Production Validation Bundle
==========================================

Environment variables configured:
  NERAVA_BACKEND_URL: https://your-backend-url.com
  BASE_URL: https://your-backend-url.com
  ADMIN_TOKEN: [REDACTED]

==========================================
Running: pytest -q
==========================================
...
✓ PASS: pytest -q

==========================================
Running: prod_gate.sh
==========================================
...
✓ PASS: prod_gate.sh

==========================================
Running: admin_smoke_test.sh
==========================================
...
✓ PASS: admin_smoke_test.sh

==========================================
Validation Summary
==========================================

✓ PASS: pytest -q
✓ PASS: prod_gate.sh
✓ PASS: admin_smoke_test.sh

Total checks: 3
Passed: 3
Failed: 0

==========================================
ALL CHECKS PASSED
Production validation complete
==========================================
```

#### Step 1.3: Handle Failures

**If any check fails:**

1. **STOP** - Do not proceed to production launch
2. Review error output (secrets are redacted automatically)
3. Fix the underlying issue
4. Re-run validation bundle: `./scripts/prod_validation_bundle.sh`
5. Repeat until all checks pass

**Common Failure Scenarios:**

| Failure | Likely Cause | Fix |
|---------|--------------|-----|
| `pytest -q` fails | Unit/integration tests failing | Fix failing tests or update test expectations |
| `prod_gate.sh` fails | Production quality gate checks failed | Review P0 items in prod_gate.sh output |
| `admin_smoke_test.sh` fails | Admin endpoints not accessible | Verify ADMIN_TOKEN, check backend health |

#### Step 1.4: Capture Artifact

**Screenshot Requirements:**
- Capture entire terminal output showing final "ALL CHECKS PASSED" message
- Include timestamp in screenshot
- Save as: `prod-proof-run-YYYY-MM-DD-HHMMSS.png`

**Artifact Storage:**
- Store screenshot in shared drive/documentation
- Reference in launch checklist
- Keep for audit trail

**Example filename:** `prod-proof-run-2025-01-27-143022.png`

---

## 2. CloudWatch Alarm Reality Check

### Objective
Verify CloudWatch alarms exist, are configured correctly, and actually send notifications.

### Steps

#### Step 2.1: Verify Alarms Exist

1. **Open AWS Console**
   - Navigate to: AWS Console → CloudWatch → Alarms
   - Region: Select your deployment region (e.g., `us-east-1`)

2. **Filter Alarms**
   - Search for: `nerava-` prefix
   - Or filter by: Alarm name prefix = `nerava-`

3. **Expected Alarms** (from `aws_create_alarms.sh`):
   - `nerava-{service-name}-high-5xx-error-rate`
   - `nerava-{service-name}-health-check-failing`
   - `nerava-{service-name}-startup-validation-failed`
   - `nerava-{service-name}-db-connection-failed`
   - `nerava-{service-name}-redis-connection-failed`
   - `nerava-{service-name}-high-traceback-rate`
   - `nerava-{service-name}-high-rate-limit-rate`

4. **Verify Count**
   - Should see 7+ alarms (depending on service configuration)
   - If fewer alarms exist → alarms were not created properly

#### Step 2.2: Verify Alarm States

**Check Each Alarm:**
- **State:** Should be `OK` (green)
- **SNS Target:** Click each alarm → Check "Actions" tab
  - Should show SNS topic ARN (e.g., `arn:aws:sns:us-east-1:123456789012:nerava-alerts`)
  - Should NOT show "No actions configured"

**If any alarm:**
- Has no SNS target → **FAIL** - Alarms won't notify
- Is in `ALARM` state → Investigate why (may be legitimate)
- Is in `INSUFFICIENT_DATA` → May be normal for new alarms, wait 5-10 minutes

#### Step 2.3: Verify SNS Topic Configuration

1. **Navigate to SNS**
   - AWS Console → SNS → Topics
   - Find topic: `nerava-alerts` (or your configured topic name)

2. **Check Subscriptions**
   - Click topic → Subscriptions tab
   - Verify subscriptions exist (email, SMS, Slack webhook, etc.)
   - Verify subscription status is `Confirmed` (for email)

3. **Test Notification** (Optional but recommended)
   - Click "Publish message"
   - Subject: `Test Alert - Production Proof Run`
   - Message: `This is a test notification from production proof run`
   - Publish
   - **Verify:** You receive notification within 1 minute

#### Step 2.4: Trigger Safe Alarm Test

**⚠️ IMPORTANT:** Only do this during maintenance window or with approval.

**Option A: Temporarily Lower Threshold (Safest)**

1. Select alarm: `nerava-{service-name}-health-check-failing`
2. Click "Edit"
3. Temporarily change threshold to trigger alarm:
   - Original: `GreaterThanThreshold` with threshold `1`
   - Change to: `GreaterThanThreshold` with threshold `0` (will trigger immediately)
4. Save changes
5. **Wait 2-5 minutes** for alarm to evaluate
6. **Verify:**
   - Alarm state changes to `ALARM` (red)
   - You receive notification via configured SNS channel
7. **Restore threshold** to original value
8. **Wait 2-5 minutes** for alarm to return to `OK`

**Option B: Stop App Runner Briefly (More Disruptive)**

1. AWS Console → App Runner → Services
2. Select your service
3. Click "Pause" (or stop service)
4. **Wait 2-5 minutes**
5. **Verify:**
   - Health check alarm triggers (`ALARM` state)
   - You receive notification
6. **Resume service** immediately
7. **Wait 2-5 minutes** for alarm to return to `OK`

**Option C: Use Verification Script**

```bash
# Run CloudWatch alarms verification script
export AWS_REGION=us-east-1
export APP_RUNNER_SERVICE_ARN=arn:aws:apprunner:us-east-1:123456789012:service/nerava-api/abc123

./scripts/verify_cloudwatch_alarms.sh
```

This script will:
- List all alarms
- Verify SNS targets are configured
- Show alarm states
- Identify any misconfigurations

#### Step 2.5: Confirm Notification Received

**Within 5 minutes of alarm trigger, verify:**

- ✅ Email notification received (check spam folder)
- ✅ SMS notification received (if configured)
- ✅ Slack/Discord webhook notification received (if configured)
- ✅ PagerDuty alert triggered (if configured)

**If notification NOT received:**
- **FAIL** - Alarms are not functional
- Check SNS topic subscriptions
- Verify subscription endpoints are correct
- Check spam/junk folders
- Verify webhook URLs are valid

#### Step 2.6: Document Results

**Create checklist entry:**

```
[ ] CloudWatch alarms exist (7+ alarms found)
[ ] All alarms have SNS targets configured
[ ] All alarms in OK state (or INSUFFICIENT_DATA for new alarms)
[ ] SNS topic has confirmed subscriptions
[ ] Test alarm triggered successfully
[ ] Notification received within 5 minutes
[ ] Alarm returned to OK state after test
```

**Screenshot Evidence:**
- CloudWatch Alarms page showing all alarms
- Alarm detail page showing SNS action configured
- SNS topic subscriptions page
- Notification received (email/SMS/Slack)

---

## 3. Go/No-Go Decision

### Go Criteria (ALL must pass):

- ✅ Production validation bundle: **ALL CHECKS PASSED**
- ✅ CloudWatch alarms: **All exist and have SNS targets**
- ✅ Alarm test: **Notification received within 5 minutes**
- ✅ Screenshots captured: **Proof run + alarm verification**

### No-Go Criteria (ANY of these):

- ❌ Production validation bundle: **Any check failed**
- ❌ CloudWatch alarms: **Missing or no SNS targets**
- ❌ Alarm test: **No notification received**
- ❌ Critical P0 items: **Any unresolved**

### Decision Log

**Date:** _______________  
**Operator:** _______________  
**Validation Bundle:** [ ] PASS [ ] FAIL  
**CloudWatch Alarms:** [ ] PASS [ ] FAIL  
**Alarm Test:** [ ] PASS [ ] FAIL  
**Decision:** [ ] GO [ ] NO-GO  
**Notes:** _______________

---

## 4. Troubleshooting

### Validation Bundle Fails

**pytest fails:**
```bash
# Run pytest with verbose output
cd nerava-backend-v9
pytest -v

# Check specific test failures
pytest tests/path/to/failing_test.py -v
```

**prod_gate.sh fails:**
```bash
# Run prod_gate.sh directly for detailed output
cd nerava-backend-v9
NERAVA_BACKEND_URL="https://your-backend-url.com" ./scripts/prod_gate.sh
```

**admin_smoke_test.sh fails:**
```bash
# Verify admin token is valid
curl "$BASE_URL/v1/auth/me" -H "Authorization: Bearer $ADMIN_TOKEN"

# Run admin smoke test directly
BASE_URL="https://your-backend-url.com" ADMIN_TOKEN="your-token" ./scripts/admin_smoke_test.sh
```

### CloudWatch Alarms Missing

**If alarms don't exist:**
```bash
# Create alarms using aws_create_alarms.sh
export AWS_REGION=us-east-1
export APP_RUNNER_SERVICE_ARN=arn:aws:apprunner:...
export LOG_GROUP_NAME=/aws/apprunner/nerava-api/service/...
export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:nerava-alerts

./scripts/aws_create_alarms.sh
```

**Verify alarms were created:**
```bash
# Use verification script
./scripts/verify_cloudwatch_alarms.sh
```

### SNS Notifications Not Working

**Check SNS topic:**
1. AWS Console → SNS → Topics → `nerava-alerts`
2. Verify subscriptions are `Confirmed`
3. For email: Check inbox (and spam) for confirmation email
4. For webhooks: Verify endpoint is reachable

**Test SNS directly:**
1. SNS → Topics → `nerava-alerts` → Publish message
2. Send test message
3. Verify delivery

---

## 5. Post-Launch Verification

After production launch, verify:

- [ ] Alarms remain in OK state (check daily for first week)
- [ ] No false alarms triggered
- [ ] Notifications are received promptly
- [ ] Alarm thresholds are appropriate

---

## Appendix: Quick Reference

### Environment Variables Template

```bash
# Production Proof Run Environment Variables
export NERAVA_BACKEND_URL="https://your-backend-url.com"
export BASE_URL="https://your-backend-url.com"
export ADMIN_TOKEN="your-jwt-admin-token"
export AWS_REGION="us-east-1"
```

### Command Cheat Sheet

```bash
# Run full validation
./scripts/prod_validation_bundle.sh

# Verify CloudWatch alarms
./scripts/verify_cloudwatch_alarms.sh

# Run individual checks
cd nerava-backend-v9 && pytest -q
NERAVA_BACKEND_URL="..." ./scripts/prod_gate.sh
BASE_URL="..." ADMIN_TOKEN="..." ./scripts/admin_smoke_test.sh
```

### AWS Console Links

- **CloudWatch Alarms:** https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:
- **SNS Topics:** https://console.aws.amazon.com/sns/v3/home?region=us-east-1#/topics
- **App Runner:** https://console.aws.amazon.com/apprunner/home?region=us-east-1

---

**Last Updated:** 2025-01-27  
**Owner:** Operations Team  
**Review Frequency:** Before each production launch

