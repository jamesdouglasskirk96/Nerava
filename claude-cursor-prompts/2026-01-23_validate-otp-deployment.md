# Validate OTP Deployment

**Date:** 2026-01-23
**Context:** Docker image `v20-otp-fix` deployed to App Runner, waiting for completion
**Goal:** Verify deployment completes and OTP endpoint works

---

## Step 1: Monitor Deployment Status

Check every 2-3 minutes until status is `SUCCEEDED`:

```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0]' \
  --output table
```

**Expected progression:**
- `IN_PROGRESS` → (5-15 minutes) → `SUCCEEDED`

If status is `FAILED`, check logs:
```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.{Status:Status,HealthCheck:HealthCheckConfiguration}'
```

---

## Step 2: Verify Service is Running

Once deployment completes:

```bash
# Check service status
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.Status' \
  --output text

# Expected: RUNNING
```

```bash
# Health check
curl -s https://api.nerava.network/health
# Expected: {"ok":true}
```

---

## Step 3: Test OTP Endpoint

This is the critical test - should respond within 30 seconds now:

```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 35
```

**Expected response:**
```json
{"otp_sent": true}
```

**If successful:** Check phone for 6-digit SMS code.

---

## Step 4: If OTP Still Fails

### 4a. Check if new image is actually running

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.SourceConfiguration.ImageRepository.ImageIdentifier' \
  --output text
```

**Expected:** `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix`

If it shows `v19-photo-fix`, the update didn't take effect. Retry:
```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {"Port": "8000"}
    },
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
    }
  }'
```

### 4b. Check Twilio credentials in environment

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables' \
  --output json | grep -i twilio
```

**Required variables:**
- `TWILIO_ACCOUNT_SID` - starts with `AC`
- `TWILIO_AUTH_TOKEN` - should be set
- `TWILIO_VERIFY_SERVICE_SID` - starts with `VA`
- `OTP_PROVIDER` - should be `twilio_verify`

### 4c. Check application logs

```bash
# If CloudWatch logs are configured
aws logs tail /aws/apprunner/nerava-backend --since 5m | grep -i "otp\|twilio\|error"
```

---

## Step 5: Verify OTP Code Delivery

After successful API response, verify the full flow:

1. **API Response:** `{"otp_sent": true}` ✓
2. **SMS Received:** 6-digit code on +17133056318 ✓
3. **Verify Code:**
```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/verify" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318", "code": "YOUR_CODE_HERE"}'
```

**Expected response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": {...}
}
```

---

## Troubleshooting

### Timeout after 30+ seconds
- **Cause:** Twilio API call blocking event loop (old code)
- **Fix:** Verify new image (`v20-otp-fix`) is running

### "Invalid credentials" or 401 error
- **Cause:** Twilio credentials expired/rotated
- **Fix:** Update credentials in App Runner environment variables

### "Service not found" error
- **Cause:** Twilio Verify Service SID invalid
- **Fix:** Create new Verify service in Twilio Console, update `TWILIO_VERIFY_SERVICE_SID`

### Deployment stuck in IN_PROGRESS > 20 minutes
- **Cause:** Health check failing, image issues
- **Fix:** Check service logs, verify Docker image builds locally

---

## Success Checklist

- [ ] Deployment status: `SUCCEEDED`
- [ ] Service status: `RUNNING`
- [ ] Image: `v20-otp-fix`
- [ ] Health check: `{"ok":true}`
- [ ] OTP request: `{"otp_sent":true}` (< 30 seconds)
- [ ] SMS received on phone
- [ ] OTP verify: Returns access_token

---

## Phone Number for Testing

**+17133056318**

---

**End of Validation Prompt**
