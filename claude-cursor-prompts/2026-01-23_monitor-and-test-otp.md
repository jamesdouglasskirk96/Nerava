# Monitor Deployment and Test OTP

**Date:** 2026-01-23
**Operation ID:** `4dd37102e9c849d4a3c6ad7b929b31f7`
**Started:** 06:53:14 AM CST
**Expected Completion:** 07:03-07:08 AM CST

---

## Current Configuration

```
Image: v20-otp-fix-fixed
Egress: DEFAULT (allows Twilio API access)
Environment: 28 variables preserved
```

---

## Step 1: Monitor Until Complete

Check status every 2 minutes:

```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0].{Status:Status,Ended:EndedAt}' \
  --output table
```

**Continue until status is NOT `IN_PROGRESS`:**
- `SUCCEEDED` → Go to Step 2
- `ROLLBACK_SUCCEEDED` → Go to Step 4
- `FAILED` → Go to Step 4

---

## Step 2: Verify Configuration (After SUCCEEDED)

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.{Status:Status,Image:SourceConfiguration.ImageRepository.ImageIdentifier,Egress:NetworkConfiguration.EgressConfiguration.EgressType}' \
  --output json
```

**Must show:**
```json
{
  "Status": "RUNNING",
  "Image": "...nerava-backend:v20-otp-fix-fixed",
  "Egress": "DEFAULT"
}
```

If egress is still `VPC`, the rollback happened silently. Go to Step 4.

---

## Step 3: Test OTP (Critical Test)

### 3a. Health Check

```bash
curl -s https://api.nerava.network/health
```

**Expected:** `{"ok":true}`

### 3b. Send OTP

```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 45
```

**Expected:** `{"otp_sent":true}` within 10 seconds

### 3c. Verify SMS

Check phone **+17133056318** for 6-digit code from Twilio.

### 3d. (Optional) Verify OTP Code

If SMS received, test verification:

```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/verify" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318", "code": "YOUR_6_DIGIT_CODE"}'
```

**Expected:** Returns `access_token`, `refresh_token`, `user` object

---

## Step 4: Diagnose Failure (If Rollback)

### 4a. Check What Went Wrong

```bash
# Get service status message
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.{Status:Status,Message:StatusMessage}'
```

### 4b. Get CloudWatch Logs

```bash
# Find log stream
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name /aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application \
  --order-by LastEventTime --descending --limit 1 \
  --query 'logStreams[0].logStreamName' --output text)

echo "Log stream: $LOG_STREAM"

# Get recent logs
aws logs get-log-events \
  --log-group-name /aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application \
  --log-stream-name "$LOG_STREAM" \
  --limit 30 \
  --query 'events[*].message' --output text
```

### 4c. Known Failure Patterns

| Error | Cause | Fix |
|-------|-------|-----|
| `AttributeError: 'Settings'...database_url` | Case mismatch | Use `DATABASE_URL` (uppercase) |
| `Connection timed out...twilio.com` | VPC blocking | Egress must be DEFAULT |
| `ModuleNotFoundError` | Missing package | Add to requirements.txt |
| `OperationalError: could not connect` | DB connection | Check DATABASE_URL format |
| Health check failed `/healthz` | App crashed | Check startup logs |

### 4d. If Rollback Due to Health Check

The health check endpoint is `/healthz`. If app crashes on startup:

1. **Check startup validation:**
   ```bash
   grep -n "database_url\|DATABASE_URL" backend/app/core/startup_validation.py
   ```
   Ensure all references use `settings.DATABASE_URL` (uppercase)

2. **Test locally:**
   ```bash
   cd /Users/jameskirk/Desktop/Nerava/backend
   docker build -t test-backend .
   docker run --rm -p 8000:8000 \
     -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
     -e JWT_SECRET="test" \
     -e ENV="dev" \
     test-backend
   ```

---

## Step 5: Retry Deployment (If Needed)

If the deployment failed, fix the issue and retry:

```bash
# 1. Build and push fixed image
cd /Users/jameskirk/Desktop/Nerava
docker build -t nerava-backend:v21-fix ./backend

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 566287346479.dkr.ecr.us-east-1.amazonaws.com

docker tag nerava-backend:v21-fix 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v21-fix
docker push 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v21-fix

# 2. Update service (use the JSON from previous successful update)
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

---

## Quick One-Liner Status Check

```bash
STATUS=$(aws apprunner list-operations --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" --query 'OperationSummaryList[0].Status' --output text) && echo "Status: $STATUS" && if [ "$STATUS" = "SUCCEEDED" ]; then curl -s https://api.nerava.network/health && echo "" && curl -X POST "https://api.nerava.network/v1/auth/otp/start" -H "Content-Type: application/json" -d '{"phone": "+17133056318"}' --max-time 45; fi
```

---

## Success Checklist

- [ ] Deployment status: `SUCCEEDED`
- [ ] Service status: `RUNNING`
- [ ] Egress type: `DEFAULT`
- [ ] Image: `v20-otp-fix-fixed`
- [ ] Health check: `{"ok":true}`
- [ ] OTP request: `{"otp_sent":true}` (< 30 seconds)
- [ ] SMS received on +17133056318
- [ ] (Optional) OTP verify returns tokens

---

## After OTP Works

Once OTP is confirmed working:

1. **Run database migration for merchant claim flow:**
   ```bash
   cd /Users/jameskirk/Desktop/Nerava/backend
   alembic upgrade head
   ```

2. **Commit any pending changes:**
   ```bash
   git add -A
   git commit -m "fix: OTP async + VPC egress + startup validation"
   git push origin main
   ```

3. **Test merchant claim endpoints:**
   ```bash
   curl https://api.nerava.network/v1/merchant/claim/session/test
   ```

---

## Timeline

| Time | Event |
|------|-------|
| 06:53:14 | Deployment started |
| ~07:03-07:08 | Expected completion |
| After success | Test OTP → Check phone |

---

**End of Monitoring Prompt**
