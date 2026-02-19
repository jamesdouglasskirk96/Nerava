# Fix VPC Egress and Test OTP Endpoint

**Date:** 2026-01-23
**Priority:** CRITICAL - Blocking OTP/SMS functionality
**Issue:** App Runner VPC egress prevents outbound internet access to Twilio API

---

## Problem Summary

The current deployment (`v20-otp-fix-fixed`) has the startup validation bug fixed, but **OTP will still fail** because:

1. App Runner is configured with `EgressType: VPC`
2. The VPC connector doesn't have a NAT Gateway
3. Outbound connections to `verify.twilio.com` timeout

**Evidence from logs:**
```
HTTPSConnectionPool(host='verify.twilio.com', port=443): Failed to establish a new connection: [Errno 110] Connection timed out
```

---

## Solution

Change App Runner egress from `VPC` to `DEFAULT` (public internet). This is safe because:
- RDS database is publicly accessible (`PubliclyAccessible: true`)
- App can still connect to RDS via its public endpoint
- Twilio API calls will work

---

## Step 1: Wait for Current Deployment

Check if current deployment has completed:

```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0].{Status:Status,Started:StartedAt,Ended:EndedAt}' \
  --output table
```

If status is `IN_PROGRESS`, wait and check again every 2 minutes.
If status is `SUCCEEDED` or `ROLLBACK_SUCCEEDED`, proceed to Step 2.

---

## Step 2: Update Egress to DEFAULT

Once no operation is in progress:

```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --network-configuration '{"EgressConfiguration":{"EgressType":"DEFAULT"}}' \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix-fixed",
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

## Step 3: Monitor Deployment

```bash
# Check every 2 minutes until SUCCEEDED
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0]' \
  --output table
```

Expected: `Status: SUCCEEDED` within 5-15 minutes.

---

## Step 4: Verify Configuration

After deployment succeeds, verify egress is now DEFAULT:

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.{Status:Status,Image:SourceConfiguration.ImageRepository.ImageIdentifier,Egress:NetworkConfiguration.EgressConfiguration.EgressType}' \
  --output json
```

Expected:
```json
{
  "Status": "RUNNING",
  "Image": "...nerava-backend:v20-otp-fix-fixed",
  "Egress": "DEFAULT"
}
```

---

## Step 5: Test Health Endpoint

```bash
curl -s https://api.nerava.network/health
# Expected: {"ok":true}
```

---

## Step 6: Test OTP Endpoint

**This is the critical test:**

```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 45
```

**Expected response:**
```json
{"otp_sent": true}
```

**Expected time:** < 10 seconds (was timing out at 60s before)

---

## Step 7: Verify SMS Received

Check phone +17133056318 for 6-digit SMS code from Twilio.

---

## Step 8: Test OTP Verification (Optional)

If SMS received:

```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/verify" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318", "code": "YOUR_6_DIGIT_CODE"}'
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

### If deployment fails

Check service status:
```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.{Status:Status,Message:StatusMessage}'
```

### If OTP still times out after egress change

Check that egress is actually DEFAULT:
```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.NetworkConfiguration.EgressConfiguration'
```

### If database connection fails after egress change

The RDS is publicly accessible, so this shouldn't happen. But if it does:
```bash
# Verify RDS is publicly accessible
aws rds describe-db-instances \
  --db-instance-identifier nerava-db \
  --query 'DBInstances[0].PubliclyAccessible'
# Should return: true
```

---

## Success Checklist

- [ ] Current deployment completed (SUCCEEDED or ROLLBACK_SUCCEEDED)
- [ ] Egress update command executed
- [ ] New deployment status: SUCCEEDED
- [ ] Egress configuration: DEFAULT
- [ ] Health check: `{"ok":true}`
- [ ] OTP request: `{"otp_sent":true}` (< 30 seconds)
- [ ] SMS received on +17133056318
- [ ] OTP verify returns access_token (optional)

---

## Root Cause Summary

| Component | Issue | Fix |
|-----------|-------|-----|
| App Runner Egress | VPC mode without NAT Gateway | Change to DEFAULT |
| Startup Validation | `settings.database_url` vs `settings.DATABASE_URL` | Already fixed in v20-otp-fix-fixed |
| Twilio SDK | Synchronous calls blocking event loop | Already fixed with `asyncio.to_thread()` |

---

## After OTP Works

Once OTP is confirmed working:

1. **Run database migration** for merchant claim flow:
   ```bash
   cd backend && alembic upgrade head
   ```

2. **Test merchant claim endpoints** (new feature):
   ```bash
   curl https://api.nerava.network/v1/merchant/claim/session/test
   ```

3. **Deploy frontend changes** for merchant portal claim flow

---

**End of Fix Prompt**
