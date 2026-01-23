# AWS Deployment Runbook

This runbook provides step-by-step instructions for deploying and managing the Nerava application on AWS App Runner (backend) and CloudFront/S3 (frontend).

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Backend Deployment (App Runner)](#backend-deployment-app-runner)
3. [Frontend Deployment (S3/CloudFront)](#frontend-deployment-s3cloudfront)
4. [Database Migrations](#database-migrations)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)

## Initial Setup

### Prerequisites

- AWS CLI installed and configured
- App Runner service ARN and URL
- S3 bucket for frontend (already exists)
- RDS Postgres instance (to be created)

### Discovery Phase

Before making changes, collect current state:

```bash
export APP_RUNNER_SERVICE_ARN="arn:aws:apprunner:us-east-1:..."
export APP_RUNNER_URL="https://..."
./scripts/aws-discovery.sh
```

This will:
- Show current App Runner configuration
- Test health endpoints
- List S3 buckets
- Show CloudFront distributions

## Backend Deployment (App Runner)

### 1. Setup RDS Postgres

```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
export DB_PASSWORD

# Create RDS instance
./scripts/setup-rds-postgres.sh
```

**Wait 5-10 minutes** for RDS to be ready, then get the endpoint:

```bash
aws rds describe-db-instances \
  --db-instance-identifier nerava-db \
  --region us-east-1 \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

**Construct DATABASE_URL:**
```
postgresql+psycopg2://nerava_admin:PASSWORD@ENDPOINT:5432/nerava
```

### 2. Configure App Runner Environment Variables

#### Apple Wallet Configuration

To enable Apple Wallet pass signing:

```bash
APPLE_WALLET_SIGNING_ENABLED=true
APPLE_WALLET_PASS_TYPE_ID=pass.com.nerava.wallet
APPLE_WALLET_TEAM_ID=YOUR_APPLE_TEAM_ID
APPLE_WALLET_CERT_P12_PATH=/path/to/cert.p12
APPLE_WALLET_CERT_P12_PASSWORD=optional_password
APPLE_WALLET_APNS_KEY_ID=YOUR_APNS_KEY_ID
APPLE_WALLET_APNS_TEAM_ID=YOUR_APNS_TEAM_ID
APPLE_WALLET_APNS_AUTH_KEY_PATH=/path/to/auth_key.p8
```

**Note**: If `APPLE_WALLET_SIGNING_ENABLED=true`, all required certificate variables must be set or the application will fail to start.

#### Google SSO Configuration

To enable Google Sign-In:

```bash
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
```

The Google Client ID is exposed via the `/v1/public/config` endpoint for frontend consumption.

#### HubSpot Integration Configuration

HubSpot integration is disabled by default (log-only mode):

```bash
HUBSPOT_ENABLED=false
HUBSPOT_SEND_LIVE=false
HUBSPOT_PRIVATE_APP_TOKEN=
HUBSPOT_PORTAL_ID=
```

To enable HubSpot logging (still log-only, no live HTTP calls):

```bash
HUBSPOT_ENABLED=true
HUBSPOT_SEND_LIVE=false  # Keep false for log-only mode
```

To enable live HubSpot API calls (use with caution):

```bash
HUBSPOT_ENABLED=true
HUBSPOT_SEND_LIVE=true
HUBSPOT_PRIVATE_APP_TOKEN=YOUR_HUBSPOT_PRIVATE_APP_TOKEN
HUBSPOT_PORTAL_ID=YOUR_HUBSPOT_PORTAL_ID
```

**Note**: If `HUBSPOT_SEND_LIVE=true`, both `HUBSPOT_PRIVATE_APP_TOKEN` and `HUBSPOT_PORTAL_ID` must be set or the application will fail to start.

Update App Runner service with required environment variables:

```bash
aws apprunner update-service \
  --service-arn "$APP_RUNNER_SERVICE_ARN" \
  --region us-east-1 \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "YOUR_ECR_IMAGE",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "ENV": "prod",
          "DATABASE_URL": "postgresql+psycopg2://user:pass@host:5432/dbname",
          "JWT_SECRET": "YOUR_SECURE_JWT_SECRET",
          "TOKEN_ENCRYPTION_KEY": "YOUR_FERNET_KEY",
          "ALLOWED_ORIGINS": "https://YOUR_CLOUDFRONT_DOMAIN",
          "PUBLIC_BASE_URL": "https://YOUR_APP_RUNNER_URL",
          "FRONTEND_URL": "https://YOUR_CLOUDFRONT_DOMAIN",
          "REDIS_URL": "redis://YOUR_REDIS_ENDPOINT:6379/0"
        }
      }
    }
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/healthz",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }'
```

**Required Environment Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `ENV` | Environment name | `prod` or `staging` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://user:pass@host:5432/db` |
| `JWT_SECRET` | JWT signing secret (secure random) | Generate with: `openssl rand -hex 32` |
| `TOKEN_ENCRYPTION_KEY` | Fernet key for token encryption | Generate with: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `https://d1234.cloudfront.net,https://app.nerava.app` |
| `PUBLIC_BASE_URL` | Public API base URL | `https://your-app-runner-url` |
| `FRONTEND_URL` | Frontend URL for redirects | `https://your-cloudfront-domain` |
| `REDIS_URL` | Redis connection string (if needed) | `redis://host:6379/0` |

**Optional (if using):**
- `SQUARE_*` - Square API credentials
- `STRIPE_*` - Stripe API credentials
- `SMARTCAR_*` - Smartcar API credentials

### 3. Update App Runner Health Check

Ensure health check path is set to `/healthz`:

```bash
aws apprunner update-service \
  --service-arn "$APP_RUNNER_SERVICE_ARN" \
  --region us-east-1 \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/healthz",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }'
```

### 4. Redeploy Backend

After updating environment variables or code:

```bash
# Trigger new deployment (if using source repository)
aws apprunner start-deployment \
  --service-arn "$APP_RUNNER_SERVICE_ARN" \
  --region us-east-1

# Or push new image to ECR (if using image repository)
# App Runner will auto-deploy
```

**Check deployment status:**
```bash
aws apprunner list-operations \
  --service-arn "$APP_RUNNER_SERVICE_ARN" \
  --region us-east-1 \
  --max-results 5
```

## Frontend Deployment (S3/CloudFront)

### 1. Deploy to S3

```bash
export S3_BUCKET="your-bucket-name"
./scripts/deploy-frontend-s3.sh
```

This uploads files with proper cache headers:
- `index.html`: `no-cache, no-store, must-revalidate`
- CSS/JS/assets: `max-age=31536000, immutable`

### 2. Create CloudFront Distribution

```bash
export S3_BUCKET="your-bucket-name"
./scripts/create-cloudfront.sh
```

**Wait 10-15 minutes** for CloudFront to deploy, then get the domain:

```bash
aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='Nerava Frontend'].{Id:Id,DomainName:DomainName}" \
  --output table
```

### 3. Update Frontend Configuration

Add App Runner URL to `ui-mobile/index.html`:

```html
<meta name="nerava-api-base" content="https://your-app-runner-url">
```

Or set via `window.NERAVA_API_BASE` in a config script.

### 4. Update Backend CORS

Add CloudFront domain to App Runner `ALLOWED_ORIGINS`:

```bash
# Get current env vars, add CloudFront domain, update
aws apprunner update-service ... --source-configuration '{
  ...
  "RuntimeEnvironmentVariables": {
    ...
    "ALLOWED_ORIGINS": "https://d1234.cloudfront.net,https://app.nerava.app"
  }
}'
```

### 5. Invalidate CloudFront Cache

After updating frontend files:

```bash
# Get distribution ID
DIST_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='Nerava Frontend'].Id" \
  --output text)

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id "$DIST_ID" \
  --paths "/*" \
  --region us-east-1
```

**Note:** Invalidations take 1-5 minutes to complete.

## Database Migrations

### Automatic Migrations (On Deploy)

Migrations run automatically on container startup via `scripts/start.sh`:
1. Runs `alembic upgrade head` (idempotent)
2. Starts uvicorn

### Manual Migrations

If you need to run migrations manually:

```bash
# Connect to App Runner container (if possible)
# Or run locally with production DATABASE_URL

export DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db"
cd nerava-backend-v9
alembic upgrade head
```

**Check migration status:**
```bash
alembic current
alembic history
```

## Environment Variables

### View Current Variables

```bash
aws apprunner describe-service \
  --service-arn "$APP_RUNNER_SERVICE_ARN" \
  --region us-east-1 \
  --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables' \
  --output json
```

### Update Single Variable

You must update the entire service configuration. Use the update command from [Configure App Runner Environment Variables](#2-configure-app-runner-environment-variables).

## Troubleshooting

### Backend Health Check Failing

1. **Check logs:**
   ```bash
   aws apprunner list-operations \
     --service-arn "$APP_RUNNER_SERVICE_ARN" \
     --region us-east-1 \
     --max-results 10
   ```

2. **Test health endpoint manually:**
   ```bash
   curl -i "https://$APP_RUNNER_URL/healthz"
   ```

3. **Verify health check path:** Should be `/healthz` (not `/` or `/v1/healthz`)

### Database Connection Issues

1. **Check RDS security group:** Must allow inbound from App Runner VPC connector
2. **Verify DATABASE_URL format:** `postgresql+psycopg2://user:pass@host:5432/db`
3. **Test connection:**
   ```bash
   psql "$DATABASE_URL" -c "SELECT 1;"
   ```

### CORS Errors

1. **Check ALLOWED_ORIGINS:** Must include CloudFront domain
2. **Verify origin format:** No trailing slashes, include `https://`
3. **Check backend logs:** CORS errors are logged

### Frontend Not Loading

1. **Check S3 bucket:** Files should be uploaded
2. **Check CloudFront status:** Distribution must be "Deployed"
3. **Invalidate cache:** After updates, invalidate CloudFront cache
4. **Check browser console:** Look for CORS or 404 errors

### Migrations Failing

1. **Check database connection:** Verify DATABASE_URL is correct
2. **Check migration status:** `alembic current`
3. **Review logs:** App Runner logs show migration output
4. **Manual run:** Run migrations manually if needed

### App Won't Start (Validation Errors)

The app validates on startup:
- **SQLite in prod:** Must use PostgreSQL in non-local environments
- **Dev flags enabled:** `NERAVA_DEV_ALLOW_ANON_*` cannot be `true` in prod
- **Missing secrets:** JWT_SECRET, TOKEN_ENCRYPTION_KEY required in prod

Check App Runner logs for specific error messages.

## Recreate App Runner Service

### When to Recreate

Recreate the App Runner service when:
- Service is stuck in `OPERATION_IN_PROGRESS` state for >30 minutes
- Service configuration is locked and you cannot edit instance role, environment variables, or health check settings
- Service is in a failed state and cannot be recovered via update
- You need to change the instance role but the dropdown is empty (trust policy issue)

### Step-by-Step Console Checklist

1. **Delete the existing service:**
   - Go to AWS Console → App Runner → Services
   - Select your service
   - Click "Delete" and confirm
   - Wait for deletion to complete (may take 5-10 minutes)

2. **Create a new service:**
   - Click "Create service"
   - Choose "Container image" (if using ECR) or "Source code repository" (if using GitHub/CodeCommit)

3. **Configure source:**
   - **For ECR:** Select your image repository and tag
   - **For source:** Connect repository and select branch

4. **Configure deployment:**
   - **Port:** `8000` (or ensure `PORT` env var is set)
   - **Build command:** (if using source) Leave default or customize
   - **Start command:** (if using source) Leave default or customize

5. **Configure service:**
   - **Service name:** Use the same name or a new one
   - **Virtual CPU:** Choose based on workload (0.25 vCPU minimum)
   - **Memory:** Choose based on workload (0.5 GB minimum)

6. **Configure instance role (CRITICAL):**
   - **Instance role dropdown:** Should show available IAM roles
   - **If dropdown is empty:**
     - The role trust policy is incorrect or missing
     - The role must trust `apprunner.amazonaws.com`
     - See `aws/iam/apprunner-instance-role-trust.json` for correct trust policy
     - Create or update the role with the trust policy, then refresh the page
   - **Select role:** Choose the role that has the trust policy and required permissions
   - **Required permissions:** See `aws/iam/apprunner-instance-role-policy.json` for minimal permissions

7. **Configure environment variables:**
   - Add all required environment variables (see [Environment Variables](#environment-variables) section)
   - **Critical vars:** `ENV`, `DATABASE_URL`, `JWT_SECRET`, `TOKEN_ENCRYPTION_KEY`
   - **CORS:** `ALLOWED_ORIGINS`, `PUBLIC_BASE_URL`, `FRONTEND_URL`

8. **Configure health check:**
   - **Protocol:** `HTTP`
   - **Path:** `/healthz` (must match the endpoint in your app)
   - **Interval:** `10` seconds
   - **Timeout:** `5` seconds
   - **Healthy threshold:** `1`
   - **Unhealthy threshold:** `5`

9. **Review and create:**
   - Review all settings
   - Click "Create & deploy"
   - Wait for service to reach `RUNNING` state (5-15 minutes)

10. **Verify deployment:**
    ```bash
    # Check service status
    aws apprunner describe-service \
      --service-arn "$APP_RUNNER_SERVICE_ARN" \
      --region us-east-1 \
      --query 'Service.Status' \
      --output text

    # Test health endpoint
    curl -i "https://$APP_RUNNER_URL/healthz"
    ```

### Instance Role Trust Policy

The instance role **must** have a trust policy that allows App Runner to assume it:

**Trust Policy (required):**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "apprunner.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```

**Location:** `aws/iam/apprunner-instance-role-trust.json`

**To apply:**
```bash
# Create or update the role trust policy
aws iam update-assume-role-policy \
  --role-name YourAppRunnerRoleName \
  --policy-document file://aws/iam/apprunner-instance-role-trust.json
```

### Instance Role Permissions

The instance role needs minimal permissions for:
- **CloudWatch Logs:** Write logs (required)
- **Secrets Manager:** Read secrets (if using)
- **RDS/ElastiCache:** Describe resources (optional, for troubleshooting)

**Minimal Policy:** See `aws/iam/apprunner-instance-role-policy.json`

**To attach:**
```bash
# Attach the policy to the role
aws iam put-role-policy \
  --role-name YourAppRunnerRoleName \
  --policy-name AppRunnerInstancePolicy \
  --policy-document file://aws/iam/apprunner-instance-role-policy.json
```

### Common Issues

**Issue: Instance role dropdown is empty**
- **Cause:** Role trust policy is missing or incorrect
- **Fix:** Create/update role with trust policy from `aws/iam/apprunner-instance-role-trust.json`
- **Verify:** `aws iam get-role --role-name YourRoleName` should show the trust policy

**Issue: Service stuck in OPERATION_IN_PROGRESS**
- **Cause:** Deployment is taking longer than expected, or service is in a bad state
- **Fix:** Wait 30 minutes, then delete and recreate if still stuck
- **Check logs:** CloudWatch logs may show startup errors

**Issue: Health check failing after recreation**
- **Cause:** Health check path is incorrect or endpoint is not responding
- **Fix:** Verify `/healthz` endpoint returns 200, update health check path in service config
- **Test:** `curl -i "https://$APP_RUNNER_URL/healthz"`

## Quick Reference

### Common Commands

```bash
# Check App Runner status
aws apprunner describe-service --service-arn "$APP_RUNNER_SERVICE_ARN" --region us-east-1

# Check RDS status
aws rds describe-db-instances --db-instance-identifier nerava-db --region us-east-1

# Check CloudFront status
aws cloudfront get-distribution --id "$DIST_ID" --region us-east-1

# View App Runner logs (via CloudWatch)
aws logs tail /aws/apprunner/nerava-backend --follow --region us-east-1

# Test health endpoint
curl -i "https://$APP_RUNNER_URL/healthz"

# Test API endpoint
curl -i "https://$APP_RUNNER_URL/openapi.json"
```

### URLs to Document

- **Backend App Runner URL:** `https://...`
- **Frontend CloudFront URL:** `https://...`
- **RDS Endpoint:** `...rds.amazonaws.com:5432`
- **Database Name:** `nerava`

## Security Checklist

- [ ] RDS is in private subnet (or security group restricts access)
- [ ] App Runner VPC connector configured
- [ ] Database password is secure and stored in secrets manager
- [ ] JWT_SECRET is secure random value
- [ ] TOKEN_ENCRYPTION_KEY is Fernet key (44 chars)
- [ ] CORS origins are explicit (no wildcards in prod)
- [ ] Dev flags are disabled (`NERAVA_DEV_ALLOW_ANON_*` = false)
- [ ] SQLite is not used (validation prevents this)

