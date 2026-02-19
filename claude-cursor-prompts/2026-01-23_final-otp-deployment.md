# Final OTP Deployment - Monitor and Test

**Date:** 2026-01-23 08:19 AM CST
**Deployment Started:** Just now
**Configuration:** VPC Egress + NAT Gateway + v20-otp-fix-fixed

---

## Infrastructure Status (Verified)

| Component | Status |
|-----------|--------|
| NAT Gateway | ✅ `nat-0d7b414381999725d` (available) |
| Route Table | ✅ `0.0.0.0/0 → NAT Gateway` |
| VPC Connector | ✅ Active |
| Image | ✅ `v20-otp-fix-fixed` |

---

## Step 1: Monitor Deployment

Check status every 2-3 minutes:

```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0].{Status:Status,Started:StartedAt,Ended:EndedAt}' \
  --output table
```

**Expected:** `SUCCEEDED` within 10-15 minutes.

---

## Step 2: Verify Configuration (After Success)

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.{Status:Status,Egress:NetworkConfiguration.EgressConfiguration.EgressType,Image:SourceConfiguration.ImageRepository.ImageIdentifier}' \
  --output json
```

**Must show:**
```json
{
  "Status": "RUNNING",
  "Egress": "VPC",
  "Image": "...nerava-backend:v20-otp-fix-fixed"
}
```

---

## Step 3: Test Health

```bash
curl -s https://api.nerava.network/health
```

**Expected:** `{"ok":true}`

---

## Step 4: Test OTP (Critical)

```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 45
```

**Expected:** `{"otp_sent":true}` within 10 seconds.

**Then:** Check phone +17133056318 for 6-digit SMS code.

---

## Step 5: Verify OTP Code (Optional)

If SMS received:

```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/verify" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318", "code": "YOUR_CODE"}'
```

**Expected:** Returns `access_token`, `refresh_token`, `user`.

---

## If Deployment Rolls Back Again

### Check CloudWatch Logs

```bash
LOG_GROUP="/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application"

# Get most recent log stream
LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime --descending --limit 1 \
  --query 'logStreams[0].logStreamName' --output text)

# Get logs
aws logs get-log-events \
  --log-group-name "$LOG_GROUP" \
  --log-stream-name "$LOG_STREAM" \
  --limit 50 \
  --query 'events[*].message' --output text
```

### Check Service Events Log

```bash
LOG_GROUP="/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/service"

LOG_STREAM=$(aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime --descending --limit 1 \
  --query 'logStreams[0].logStreamName' --output text 2>/dev/null)

if [ "$LOG_STREAM" != "None" ]; then
  aws logs get-log-events \
    --log-group-name "$LOG_GROUP" \
    --log-stream-name "$LOG_STREAM" \
    --limit 30 \
    --query 'events[*].message' --output text
fi
```

### Test NAT Gateway Connectivity

If logs show connection timeouts, verify NAT Gateway is working:

```bash
# Check NAT Gateway state
aws ec2 describe-nat-gateways \
  --nat-gateway-ids nat-0d7b414381999725d \
  --query 'NatGateways[0].State'

# Check route table
aws ec2 describe-route-tables \
  --route-table-ids rtb-0d4d2b5de461259f9 \
  --query 'RouteTables[0].Routes[?DestinationCidrBlock==`0.0.0.0/0`]'
```

---

## After OTP Works

1. **Run merchant claim migration:**
   ```bash
   cd /Users/jameskirk/Desktop/Nerava/backend
   alembic upgrade head
   ```

2. **Test merchant claim endpoint:**
   ```bash
   curl -s https://api.nerava.network/v1/merchant/claim/session/test
   ```

3. **Commit and push:**
   ```bash
   git add -A
   git commit -m "fix: OTP async Twilio calls, VPC NAT Gateway config"
   git push origin main
   ```

---

## Quick Status Check One-Liner

```bash
STATUS=$(aws apprunner list-operations --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" --query 'OperationSummaryList[0].Status' --output text) && echo "Deployment: $STATUS" && if [ "$STATUS" = "SUCCEEDED" ]; then echo "Testing OTP..." && curl -X POST "https://api.nerava.network/v1/auth/otp/start" -H "Content-Type: application/json" -d '{"phone": "+17133056318"}' --max-time 45; elif [ "$STATUS" = "ROLLBACK_SUCCEEDED" ]; then echo "FAILED - check logs"; fi
```

---

## Success Checklist

- [ ] Deployment status: `SUCCEEDED`
- [ ] Service status: `RUNNING`
- [ ] Egress: `VPC`
- [ ] Image: `v20-otp-fix-fixed`
- [ ] Health: `{"ok":true}`
- [ ] OTP: `{"otp_sent":true}` (< 30 seconds)
- [ ] SMS received on +17133056318
- [ ] Migration run: `alembic upgrade head`

---

**End of Final Deployment Prompt**
