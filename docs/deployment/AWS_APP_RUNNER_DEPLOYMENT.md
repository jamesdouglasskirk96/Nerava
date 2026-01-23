# AWS App Runner Deployment Status

## Current Status

**Service ARN**: `arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/6c9c71e0ed4b40f1826e9b69dc55763d`  
**Service URL**: `https://nbfmpiie6x.us-east-1.awsapprunner.com`  
**Status**: `OPERATION_IN_PROGRESS` (updating)

## Fixes Applied

### 1. Docker Image Fixes ✅
- **Port**: Changed from 8000 to 8080 (App Runner default)
- **Startup Script**: Enhanced with `set -euo pipefail` and better error handling
- **Health Check**: Updated to use port 8080
- **Script Permissions**: Ensured `start.sh` is executable

**Files Modified**:
- `nerava-backend-v9/Dockerfile` - Port defaults and healthcheck
- `nerava-backend-v9/scripts/start.sh` - Port default and error handling

### 2. Image Built and Pushed ✅
- Image built with all fixes
- Pushed to ECR: `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest`

### 3. Service Configuration Updated ✅
- Port set to 8080
- Health check path: `/healthz`
- Environment variables configured

## Current Configuration

The service is currently configured with:
- `ENV=prod` (⚠️ **This will fail with SQLite**)
- `DATABASE_URL=sqlite:///./nerava.db` (⚠️ **Not allowed in production**)
- `PORT=8080` ✅
- `JWT_SECRET` ✅ (generated)
- `TOKEN_ENCRYPTION_KEY` ✅ (generated)

## Issue: SQLite in Production

The current configuration uses `ENV=prod` with SQLite, which will **fail validation** because:
- `validate_database_url()` in `app/main_simple.py` rejects SQLite when `ENV != "local"`
- The service will exit during startup with a clear error message

## Solutions

### Option 1: Use Dev Configuration (Temporary)

Update the service to use `ENV=dev` which allows SQLite:

```bash
# Update with dev configuration
aws apprunner update-service \
    --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/6c9c71e0ed4b40f1826e9b69dc55763d" \
    --region us-east-1 \
    --source-configuration file:///tmp/apprunner-config-dev.json \
    --health-check-configuration '{"Protocol":"HTTP","Path":"/healthz","Interval":10,"Timeout":5,"HealthyThreshold":1,"UnhealthyThreshold":5}'
```

This will allow the service to start, but **SQLite is not suitable for production**.

### Option 2: Set Up RDS PostgreSQL (Recommended)

1. **Grant IAM Permissions** (if not already done):
   ```bash
   # Add to your IAM user/role:
   # - rds:CreateDBInstance
   # - rds:DescribeDBInstances
   # - rds:ModifyDBInstance
   ```

2. **Create RDS Instance**:
   ```bash
   DB_PASSWORD='your-secure-password' ./scripts/setup-rds-postgres.sh
   ```

3. **Get Database URL**:
   ```bash
   RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier nerava-db --region us-east-1 --query 'DBInstances[0].Endpoint.Address' --output text)
   DB_USERNAME="nerava_admin"
   DB_NAME="nerava"
   DATABASE_URL="postgresql+psycopg2://$DB_USERNAME:$DB_PASSWORD@$RDS_ENDPOINT:5432/$DB_NAME"
   ```

4. **Update App Runner** with production configuration:
   ```bash
   # Use the deploy script
   DATABASE_URL="$DATABASE_URL" ENV=prod ./scripts/deploy-apprunner.sh
   ```

## Deployment Script

A deployment script has been created at `scripts/deploy-apprunner.sh` that:
- Builds and pushes the Docker image
- Generates/loads secrets
- Creates proper App Runner configuration
- Updates the service
- Waits for service to be running
- Tests the health endpoint

**Usage**:
```bash
# For dev (SQLite allowed)
./scripts/deploy-apprunner.sh

# For production (requires DATABASE_URL)
DATABASE_URL="postgresql+psycopg2://..." ENV=prod ./scripts/deploy-apprunner.sh
```

## Verification

Once the service is running:

1. **Check Status**:
   ```bash
   aws apprunner describe-service \
       --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/6c9c71e0ed4b40f1826e9b69dc55763d" \
       --region us-east-1
   ```

2. **Test Health Endpoint**:
   ```bash
   curl https://nbfmpiie6x.us-east-1.awsapprunner.com/healthz
   ```
   Expected: `{"ok":true}`

3. **Check Logs** (if you have permissions):
   ```bash
   aws logs tail /aws/apprunner/nerava-backend/6c9c71e0ed4b40f1826e9b69dc55763d/service --follow
   ```

## Next Steps

1. **Wait for current update to complete** (check status every few minutes)
2. **If it fails**: Update with dev configuration to get service running
3. **Set up RDS PostgreSQL** for production
4. **Update service** with production DATABASE_URL and ENV=prod
5. **Verify health check** passes
6. **Set up Redis** (ElastiCache) if needed for rate limiting
7. **Configure CloudFront** for frontend (if needed)

## Troubleshooting

### Service Stuck in OPERATION_IN_PROGRESS
- Wait up to 10-15 minutes for App Runner to complete
- Check operation status: `aws apprunner list-operations --service-arn ...`

### Service Fails to Start
- Check CloudWatch logs (if you have permissions)
- Verify environment variables are correct
- Ensure DATABASE_URL is valid and accessible
- Check that JWT_SECRET and TOKEN_ENCRYPTION_KEY are set

### Health Check Fails
- Verify `/healthz` endpoint exists (it does - in `app/routers/ops.py`)
- Check that port 8080 is correct
- Ensure container is listening on 0.0.0.0:8080

## Files Created/Modified

- ✅ `nerava-backend-v9/Dockerfile` - Fixed port to 8080
- ✅ `nerava-backend-v9/scripts/start.sh` - Fixed port and improved error handling
- ✅ `scripts/deploy-apprunner.sh` - Deployment automation script
- ✅ `/tmp/apprunner-config-dev.json` - Dev configuration template
- ✅ `/tmp/secrets.sh` - Generated secrets (JWT_SECRET, TOKEN_ENCRYPTION_KEY)



