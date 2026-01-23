# Quick Start - Complete AWS Deployment

## Current Status

**App Runner Service**: `OPERATION_IN_PROGRESS` (creation takes 10-15 minutes)
- ARN: `arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/6c9c71e0ed4b40f1826e9b69dc55763d`
- URL: `https://nbfmpiie6x.us-east-1.awsapprunner.com`

**S3 Frontend**: ✅ Deployed to `nerava-frontend-1766451028`

## Quick Commands

### Check App Runner Status
```bash
export APP_RUNNER_SERVICE_ARN="arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/6c9c71e0ed4b40f1826e9b69dc55763d"
aws apprunner describe-service --service-arn "$APP_RUNNER_SERVICE_ARN" --region us-east-1 --query 'Service.Status' --output text
```

### Test Health Endpoint (once RUNNING)
```bash
export APP_RUNNER_URL="https://nbfmpiie6x.us-east-1.awsapprunner.com"
curl -i "$APP_RUNNER_URL/healthz"
```

### Complete All Phases (after permissions granted)
```bash
./scripts/complete-aws-deployment.sh
```

### Individual Phase Scripts
```bash
# RDS (after IAM permissions)
./scripts/setup-rds-with-permissions.sh

# Redis (after IAM permissions)
./scripts/setup-redis-with-permissions.sh

# CloudFront (after account verification)
export S3_BUCKET="nerava-frontend-1766451028"
S3_BUCKET="$S3_BUCKET" ./scripts/create-cloudfront.sh
```

## What's Been Done

✅ Phase 0: Discovery completed
✅ Phase 1: App Runner service created with /healthz
✅ Phase 2: Secrets generated
✅ Phase 5: Frontend deployed to S3
✅ Phase 6: Frontend configured with API base URL

## What Remains

⏳ Wait for App Runner to be RUNNING
❌ Phase 3: RDS (needs IAM permissions)
❌ Phase 4: Redis (needs IAM permissions)
❌ Phase 6: CloudFront (needs account verification)
⏳ Phase 7: CORS configuration (after CloudFront)
⏳ Phase 8: Smoke tests (after all phases)

## Files Reference

- `FINAL_DEPLOYMENT_STATUS.md` - Detailed status
- `scripts/complete-aws-deployment.sh` - Auto-complete script
- `scripts/setup-rds-with-permissions.sh` - RDS setup
- `scripts/setup-redis-with-permissions.sh` - Redis setup
- `/tmp/secrets.sh` - Generated secrets
- `/tmp/db-password.txt` - RDS password



