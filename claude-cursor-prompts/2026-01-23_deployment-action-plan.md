# Deployment Action Plan - OTP Fix

**Date:** 2026-01-23
**Current Operation:** `5d416989a4dd485dabb43390ef72e3a6` (started 06:29:24)
**Configuration:** Egress=DEFAULT, Image=v20-otp-fix-fixed

---

## Step 1: Check Deployment Status

```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0].{Status:Status,Started:StartedAt,Ended:EndedAt}' \
  --output table
```

**If `IN_PROGRESS`:** Wait 2 minutes and check again. Normal deployment: 5-15 minutes.

**If `SUCCEEDED`:** Go to Step 2 (Test OTP).

**If `ROLLBACK_SUCCEEDED` or `FAILED`:** Go to Step 3 (Diagnose Failure).

---

## Step 2: Test OTP (If Deployment Succeeded)

### 2a. Verify Configuration

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.{Status:Status,Egress:NetworkConfiguration.EgressConfiguration.EgressType,Image:SourceConfiguration.ImageRepository.ImageIdentifier}' \
  --output json
```

**Expected:**
```json
{
  "Status": "RUNNING",
  "Egress": "DEFAULT",
  "Image": "...nerava-backend:v20-otp-fix-fixed"
}
```

### 2b. Test Health

```bash
curl -s https://api.nerava.network/health
```

**Expected:** `{"ok":true}`

### 2c. Test OTP Endpoint

```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 45
```

**Expected:** `{"otp_sent":true}` within 10 seconds.

### 2d. Check Phone

Verify SMS received on +17133056318 with 6-digit code.

**If all tests pass:** Deployment successful! Update the user.

---

## Step 3: Diagnose Failure (If Deployment Rolled Back)

### 3a. Get Service Status

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.{Status:Status,Message:StatusMessage,HealthCheck:HealthCheckConfiguration}'
```

### 3b. Check CloudWatch Logs

```bash
# List log streams (most recent first)
aws logs describe-log-streams \
  --log-group-name /aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application \
  --order-by LastEventTime \
  --descending \
  --limit 3 \
  --query 'logStreams[*].logStreamName'

# Get recent logs (replace LOG_STREAM_NAME)
aws logs get-log-events \
  --log-group-name /aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application \
  --log-stream-name "LOG_STREAM_NAME" \
  --limit 50 \
  --query 'events[*].message'
```

### 3c. Common Failure Patterns

| Log Pattern | Root Cause | Fix |
|-------------|------------|-----|
| `AttributeError: 'Settings' object has no attribute 'database_url'` | Case mismatch in config | Use `settings.DATABASE_URL` |
| `HTTPSConnectionPool...Connection timed out` | VPC egress blocking | Change egress to DEFAULT |
| `ModuleNotFoundError` | Missing dependency | Add to requirements.txt |
| `OperationalError: could not connect to server` | Database connection failed | Check DATABASE_URL env var |
| `ValidationError` | Pydantic validation failed | Check env var format |
| Health check failed on `/healthz` | App crash on startup | Check startup logs |

---

## Step 4: Apply Fix Based on Root Cause

### If Startup Error (AttributeError, ModuleNotFoundError, etc.)

1. **Fix the code locally:**
   ```bash
   cd /Users/jameskirk/Desktop/Nerava/backend
   # Make the fix
   ```

2. **Test locally:**
   ```bash
   docker build -t nerava-backend:test ./backend
   docker run --rm -p 8000:8000 \
     -e DATABASE_URL="postgresql://..." \
     -e JWT_SECRET="test" \
     -e ENV="dev" \
     nerava-backend:test
   ```

3. **Build and push new image:**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin 566287346479.dkr.ecr.us-east-1.amazonaws.com

   # Build
   docker build -t nerava-backend:v21-fix ./backend

   # Tag and push
   docker tag nerava-backend:v21-fix 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v21-fix
   docker push 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v21-fix
   ```

4. **Deploy new image:**
   ```bash
   aws apprunner update-service \
     --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
     --network-configuration '{"EgressConfiguration":{"EgressType":"DEFAULT"}}' \
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v21-fix",
         "ImageRepositoryType": "ECR",
         "ImageConfiguration": {"Port": "8000"}
       },
       "AutoDeploymentsEnabled": false,
       "AuthenticationConfiguration": {
         "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
       }
     }'
   ```

### If Database Connection Error

1. **Verify DATABASE_URL is set:**
   ```bash
   aws apprunner describe-service \
     --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
     --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables'
   ```

2. **If missing, add environment variables to the update command.**

### If Twilio Connection Error (After Egress Fixed)

1. **Verify Twilio credentials:**
   ```bash
   # Check if TWILIO vars are set
   aws apprunner describe-service \
     --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
     --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables' | \
     grep -i twilio
   ```

2. **Verify credentials in Twilio Console:** https://console.twilio.com

---

## Step 5: Alternative - Delete and Recreate Service

If multiple rollbacks continue, consider recreating the service:

```bash
# WARNING: This will cause downtime

# 1. Delete the service
aws apprunner delete-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3"

# 2. Wait for deletion
aws apprunner list-services --query 'ServiceSummaryList[?ServiceName==`nerava-backend`]'

# 3. Create new service with correct configuration
# (Would need to set up all env vars again)
```

**Only use this as last resort** - requires reconfiguring all environment variables.

---

## History of Issues Fixed

| Version | Issue | Status |
|---------|-------|--------|
| v19-photo-fix | Original version | Working but OTP times out |
| v20-otp-fix | Async Twilio calls | Rolled back - startup validation bug |
| v20-otp-fix-fixed | Fixed `DATABASE_URL` casing | Currently deploying |

---

## Quick Reference Commands

```bash
# Check operation status
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0].Status' --output text

# Check service status
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.Status' --output text

# Test health
curl -s https://api.nerava.network/health

# Test OTP
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' --max-time 45
```

---

## Success Criteria

- [ ] Deployment status: `SUCCEEDED`
- [ ] Service status: `RUNNING`
- [ ] Egress: `DEFAULT`
- [ ] Health check: `{"ok":true}`
- [ ] OTP request: `{"otp_sent":true}` (< 30 seconds)
- [ ] SMS received on +17133056318

---

**End of Action Plan**
