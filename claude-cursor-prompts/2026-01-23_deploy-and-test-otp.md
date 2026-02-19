# Deploy and Test OTP Endpoint

**Date:** 2026-01-23
**Goal:** Push code changes, verify Twilio credentials, and send OTP to +17133056318

---

## Step 1: Push Changes to Trigger Deployment

```bash
cd /Users/jameskirk/Desktop/Nerava
git push origin main
```

This will trigger the GitHub Actions workflow which deploys to AWS.

**Wait for deployment to complete** (check GitHub Actions or run):
```bash
# Check workflow status
gh run list --limit 5

# Watch the latest run
gh run watch
```

---

## Step 2: Verify Deployment is Live

```bash
# Wait ~5 minutes for deployment, then check health
curl https://api.nerava.network/health
# Expected: {"ok":true}
```

---

## Step 3: Verify Twilio Credentials in AWS

Check that Twilio environment variables are configured in AWS ECS:

```bash
# Get the current task definition and check for Twilio vars
aws ecs describe-task-definition \
  --task-definition nerava-backend \
  --query 'taskDefinition.containerDefinitions[0].environment[?starts_with(name, `TWILIO`) || name==`OTP_PROVIDER`]' \
  --output table
```

**Required variables:**
| Variable | Expected Value |
|----------|----------------|
| `OTP_PROVIDER` | `twilio_verify` |
| `TWILIO_ACCOUNT_SID` | `AC...` (starts with AC) |
| `TWILIO_AUTH_TOKEN` | (should be set, not empty) |
| `TWILIO_VERIFY_SERVICE_SID` | `VA...` (starts with VA) |

**If variables are missing**, they need to be added to the ECS task definition or Terraform configuration.

---

## Step 4: Check Backend Logs for OTP Provider Initialization

```bash
# Get recent logs
aws logs tail /ecs/nerava-backend --since 10m | grep -i "otp\|twilio"
```

Look for:
- `[OTP] Using Twilio Verify provider` - Good, provider initialized
- `Twilio credentials not configured` - Bad, missing credentials
- `TWILIO_VERIFY_SERVICE_SID not configured` - Bad, missing service SID

---

## Step 5: Test OTP Endpoint

```bash
# Send OTP to James's phone
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 45

# Expected response:
# {"otp_sent": true}
```

**If it works:** Check phone for 6-digit SMS code.

**If it times out or errors:**
1. Check AWS logs for error details
2. Verify Twilio credentials are correct
3. Verify Twilio account is active at https://console.twilio.com

---

## Step 6: If Credentials Are Missing - Add Them

If Twilio variables are not in AWS, add them via Terraform or directly to ECS:

### Option A: Check/Update Terraform (Recommended)

Look for Twilio variables in `infra/terraform/`:
```bash
grep -r "TWILIO" infra/terraform/
```

If missing, add to the ECS task definition in Terraform:
```hcl
environment = [
  {
    name  = "OTP_PROVIDER"
    value = "twilio_verify"
  },
  {
    name  = "TWILIO_ACCOUNT_SID"
    value = var.twilio_account_sid  # From tfvars or secrets
  },
  {
    name  = "TWILIO_AUTH_TOKEN"
    value = var.twilio_auth_token
  },
  {
    name  = "TWILIO_VERIFY_SERVICE_SID"
    value = var.twilio_verify_service_sid
  },
]
```

### Option B: Add Directly to ECS (Quick Fix)

```bash
# 1. Get current task definition
aws ecs describe-task-definition --task-definition nerava-backend > /tmp/task-def.json

# 2. Edit the environment section to add Twilio vars
# (manually edit /tmp/task-def.json)

# 3. Register updated task definition
aws ecs register-task-definition --cli-input-json file:///tmp/task-def-updated.json

# 4. Update service to use new task definition
aws ecs update-service \
  --cluster nerava-cluster \
  --service nerava-backend \
  --force-new-deployment
```

---

## Troubleshooting

### OTP still times out after fix
The async fix is deployed but credentials may be wrong:
```bash
# Run diagnostic script locally with prod credentials
export TWILIO_ACCOUNT_SID="AC..."
export TWILIO_AUTH_TOKEN="..."
export TWILIO_VERIFY_SERVICE_SID="VA..."
python backend/scripts/check_twilio_config.py --test-phone +17133056318
```

### "Invalid credentials" error
- Twilio auth token may have been rotated
- Go to Twilio Console > Account > API Keys to get current token

### "Service not found" error
- Verify service SID exists in Twilio Console > Verify > Services
- Create new service if needed and update `TWILIO_VERIFY_SERVICE_SID`

---

## Success Criteria

- [ ] `git push origin main` completes successfully
- [ ] GitHub Actions deployment workflow passes
- [ ] `curl https://api.nerava.network/health` returns `{"ok":true}`
- [ ] AWS ECS has all Twilio environment variables
- [ ] OTP request returns `{"otp_sent": true}`
- [ ] SMS with 6-digit code received on +17133056318

---

**Phone number for testing:** +17133056318
