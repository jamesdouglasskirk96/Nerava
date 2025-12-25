# Health Check Failure - Current Diagnosis

## Current Status
- **Service Status:** OPERATION_IN_PROGRESS
- **Service URL:** xgxqvxxnjv.us-east-1.awsapprunner.com
- **Health Check Response:** HTTP 404 Not Found
- **Application Logs:** None visible in CloudWatch

## Issues Found

### 1. Missing Application Logs
**No application logs appear in CloudWatch**, despite:
- Startup logging code that prints `[STARTUP]` messages
- Application code that should log to stdout

This suggests:
- Application is not starting at all
- Or logs are not being captured/forwarded to CloudWatch

### 2. Config Router Fix Applied
The fix for `config_router.router` has been applied (line 613), so that's not the issue.

### 3. Nova Accrual Service
The `nova_accrual_service` starts on startup but:
- Should only run if `DEMO_MODE` or `DEMO_QR_ENABLED` is true
- In production, these should be false, so it should return early
- Even if enabled, errors are caught and logged (shouldn't crash app)

## Next Steps to Diagnose

### Check Environment Variables
Verify that DEMO_MODE is not enabled in production:
```bash
aws apprunner describe-service --service-arn "$SERVICE_ARN" \
  --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables' \
  --output json | jq '.DEMO_MODE'
```

### Check if Application is Actually Starting
The fact that we see NO logs (not even `[STARTUP]` messages) suggests:
1. The Docker container CMD is failing before Python even starts
2. Or Python is starting but crashing before any imports complete
3. Or logs are not being forwarded to CloudWatch

### Test Locally with Production-like Environment
```bash
docker run --rm \
  -e ENV=prod \
  -e DATABASE_URL=postgresql+psycopg2://test:test@localhost/test \
  -e PORT=8000 \
  -e JWT_SECRET=test \
  -e TOKEN_ENCRYPTION_KEY=test \
  566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest \
  timeout 15 python -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000
```

This will show if there are import errors or startup failures.

### Check if Observability is Enabled
App Runner might not be forwarding logs if observability configuration is missing.

## Possible Root Causes

1. **Environment Variable Missing/Invalid**
   - Database connection failing
   - JWT_SECRET or TOKEN_ENCRYPTION_KEY invalid
   - Required env vars missing

2. **Database Connection Failure**
   - RDS endpoint unreachable from VPC Connector
   - Security group rules incorrect
   - Database credentials invalid

3. **Application Startup Validation Failing**
   - Config validation throwing exception
   - Startup checks failing silently

4. **Log Forwarding Not Configured**
   - Observability configuration missing
   - CloudWatch log group permissions incorrect

