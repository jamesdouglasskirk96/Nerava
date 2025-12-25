# CloudWatch Alarms Runbook for Nerava

**Purpose:** Monitor App Runner service health, errors, latency, and critical system events

---

## Prerequisites

1. **AWS CLI configured** with appropriate permissions:
   - `cloudwatch:PutMetricAlarm`
   - `cloudwatch:DescribeAlarms`
   - `logs:PutMetricFilter`
   - `logs:DescribeMetricFilters`
   - `sns:Publish` (for testing)

2. **SNS Topic created** and subscribed:
   ```bash
   aws sns create-topic --name nerava-alerts --region us-east-1
   aws sns subscribe --topic-arn <TOPIC_ARN> --protocol email --notification-endpoint your-email@example.com
   ```

3. **Environment variables** set (see script usage below)

---

## Finding Required Values

### 1. App Runner Service ARN

**Option A: From AWS Console**
1. Go to AWS App Runner console
2. Select your service (e.g., `nerava-api`)
3. Copy the ARN from the service details page
   - Format: `arn:aws:apprunner:us-east-1:123456789012:service/nerava-api/abc123def456`

**Option B: From AWS CLI**
```bash
aws apprunner list-services --region us-east-1
# Find your service and copy the ServiceArn
```

### 2. Log Group Name

**Option A: From AWS Console**
1. Go to CloudWatch Logs console
2. Look for log group starting with `/aws/apprunner/`
3. Format: `/aws/apprunner/<service-name>/service/<service-id>`

**Option B: From AWS CLI**
```bash
aws logs describe-log-groups --region us-east-1 --log-group-name-prefix "/aws/apprunner"
# Find your service log group
```

**Option C: Auto-detect from Service ARN**
The log group name follows this pattern:
```
/aws/apprunner/<service-name>/service/<service-id>
```
Where `<service-id>` is the last segment of the Service ARN.

### 3. SNS Topic ARN

**Option A: From AWS Console**
1. Go to SNS console
2. Find your topic (e.g., `nerava-alerts`)
3. Copy the ARN

**Option B: From AWS CLI**
```bash
aws sns list-topics --region us-east-1
# Find your topic ARN
```

---

## Creating Alarms

### Step 1: Set Environment Variables

```bash
export AWS_REGION=us-east-1
export APP_RUNNER_SERVICE_ARN=arn:aws:apprunner:us-east-1:123456789012:service/nerava-api/abc123
export LOG_GROUP_NAME=/aws/apprunner/nerava-api/service/abc123
export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:nerava-alerts
```

### Step 2: Run the Script

```bash
cd /path/to/Nerava
./scripts/aws_create_alarms.sh
```

The script will:
1. Create log metric filters for critical log patterns
2. Create CloudWatch alarms based on those metrics
3. Configure alarms to send notifications to the SNS topic

### Step 3: Verify Alarms Were Created

```bash
aws cloudwatch describe-alarms \
  --region us-east-1 \
  --alarm-name-prefix nerava- \
  --query 'MetricAlarms[*].[AlarmName,StateValue]' \
  --output table
```

Expected output: All alarms should be in `OK` state initially.

---

## Alarms Created

| Alarm Name | Metric | Threshold | Purpose |
|------------|--------|-----------|---------|
| `nerava-*-high-5xx-error-rate` | AppRunner5xxErrors | > 5 errors/min | Alert on high error rate |
| `nerava-*-health-check-failing` | HealthCheckFailures | > 0 failures | Alert on health check failures |
| `nerava-*-startup-validation-failed` | StartupValidationFailed | > 0 failures | Alert on startup validation failures |
| `nerava-*-db-connection-failed` | DatabaseConnectionFailed | > 0 failures/5min | Alert on DB connection issues |
| `nerava-*-redis-connection-failed` | RedisConnectionFailed | > 0 failures/5min | Alert on Redis connection issues |
| `nerava-*-high-traceback-rate` | PythonTracebacks | > 10/hour | Alert on unhandled exceptions |
| `nerava-*-high-rate-limit-rate` | RateLimitExceeded | > 100/hour | Alert on excessive rate limiting |

---

## Testing Alarms (Staging Only)

**⚠️ WARNING: Only test in staging/dev environments. Do not trigger false alarms in production.**

### Test 1: Trigger a 500 Error (Staging Only)

Create a test endpoint that returns 500:

```python
# In staging only - add to a test router
@app.get("/test/trigger-500")
async def trigger_500():
    raise HTTPException(status_code=500, detail="Test alarm trigger")
```

Then call it:
```bash
curl https://your-staging-url/test/trigger-500
```

**Expected:** Alarm `nerava-*-high-5xx-error-rate` should fire within 1 minute.

### Test 2: Verify Alarm Fired

```bash
aws cloudwatch describe-alarms \
  --region us-east-1 \
  --alarm-name nerava-*-high-5xx-error-rate \
  --query 'MetricAlarms[0].[AlarmName,StateValue,StateReason]' \
  --output table
```

**Expected:** State should be `ALARM` with reason showing metric exceeded threshold.

### Test 3: Check SNS Notification

Check your email (or SNS subscription endpoint) for the alarm notification.

### Test 4: Clear Alarm State

After testing, manually set alarm back to OK (or wait for metric to return to normal):
```bash
aws cloudwatch set-alarm-state \
  --region us-east-1 \
  --alarm-name nerava-*-high-5xx-error-rate \
  --state-value OK \
  --state-reason "Test completed"
```

---

## Monitoring Latency (Optional)

App Runner doesn't expose p95 latency metrics directly. To monitor latency:

### Option 1: CloudWatch Synthetics Canary

Create a canary that hits `/healthz` and `/readyz` endpoints:

```bash
# Create canary script (see AWS docs for full setup)
aws synthetics create-canary \
  --name nerava-health-check \
  --artifact-s3-location s3://your-bucket/canaries/ \
  --execution-role-arn arn:aws:iam::123456789012:role/SyntheticsRole \
  --schedule "rate(1 minute)" \
  --run-config '{"TimeoutInSeconds": 30}' \
  --runtime-version syn-nodejs-puppeteer-3.9 \
  --handler "pageLoadBlueprint.handler" \
  --code '{"Script": "..."}'
```

### Option 2: Application-Level Metrics

Add Prometheus metrics endpoint and use CloudWatch Container Insights (if using ECS) or custom metrics.

---

## Troubleshooting

### Alarm Not Firing

1. **Check log group exists:**
   ```bash
   aws logs describe-log-groups --log-group-name-prefix "/aws/apprunner"
   ```

2. **Check metric filter created:**
   ```bash
   aws logs describe-metric-filters \
     --log-group-name "$LOG_GROUP_NAME" \
     --region us-east-1
   ```

3. **Check metric data:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace "Nerava/Logs" \
     --metric-name "AppRunner5xxErrors" \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 60 \
     --statistics Sum \
     --region us-east-1
   ```

### Alarm Firing Too Often

Adjust thresholds in the script:
- Increase threshold values
- Increase evaluation periods
- Increase period (aggregation window)

### SNS Notifications Not Received

1. **Check SNS subscription:**
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn "$SNS_TOPIC_ARN" \
     --region us-east-1
   ```

2. **Verify email subscription confirmed** (check spam folder)

3. **Test SNS directly:**
   ```bash
   aws sns publish \
     --topic-arn "$SNS_TOPIC_ARN" \
     --message "Test message" \
     --subject "Test" \
     --region us-east-1
   ```

---

## Maintenance

### Updating Alarm Thresholds

Edit `scripts/aws_create_alarms.sh` and re-run. The script is idempotent and will update existing alarms.

### Adding New Alarms

1. Add log metric filter creation in script
2. Add alarm creation with appropriate threshold
3. Document in this runbook

### Removing Alarms

```bash
aws cloudwatch delete-alarms \
  --alarm-names nerava-*-alarm-name \
  --region us-east-1
```

---

## Cost Considerations

- **CloudWatch Alarms:** First 10 alarms free, then $0.10/alarm/month
- **Log Metric Filters:** $0.03/metric filter/month
- **SNS:** First 1M requests/month free, then $0.50/1M requests

**Estimated monthly cost:** ~$1-2 for 7 alarms + filters (within free tier)

---

## References

- [AWS App Runner Monitoring](https://docs.aws.amazon.com/apprunner/latest/dg/monitor-cloudwatch.html)
- [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [CloudWatch Logs Metric Filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html)

