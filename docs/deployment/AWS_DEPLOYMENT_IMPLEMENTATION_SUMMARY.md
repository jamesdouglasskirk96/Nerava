# AWS Deployment Implementation Summary

This document summarizes all changes made to complete the AWS App Runner + CloudFront deployment.

## Files Modified

### Backend Changes

1. **`nerava-backend-v9/app/main_simple.py`**
   - Added `validate_database_url()` function to prevent SQLite in production
   - Added `validate_dev_flags()` function to prevent dev flags in production
   - Integrated both validations into startup sequence (fail-fast)

2. **`nerava-backend-v9/Dockerfile`**
   - Updated CMD to use `scripts/start.sh` instead of direct uvicorn command
   - This enables automatic migrations on container startup

3. **`nerava-backend-v9/scripts/start.sh`** (NEW)
   - Runs `alembic upgrade head` before starting uvicorn
   - Idempotent migrations (safe to run multiple times)
   - Proper error handling

### Frontend Changes

4. **`ui-mobile/js/core/api.js`**
   - Added CloudFront domain detection (cloudfront.net, amazonaws.com)
   - Added support for `window.NERAVA_API_BASE` configuration
   - Added support for meta tag: `<meta name="nerava-api-base" content="...">`
   - Improved production environment detection

## Files Created

### Scripts

1. **`scripts/aws-discovery.sh`**
   - Collects current AWS state (App Runner, S3, CloudFront)
   - Tests health endpoints
   - No changes made, read-only discovery

2. **`scripts/setup-rds-postgres.sh`**
   - Creates RDS Postgres instance
   - Configures security settings
   - Generates connection string format

3. **`scripts/deploy-frontend-s3.sh`**
   - Uploads ui-mobile files to S3
   - Sets proper cache headers:
     - `index.html`: no-cache
     - CSS/JS/assets: long cache (immutable)

4. **`scripts/create-cloudfront.sh`**
   - Creates CloudFront distribution
   - Sets up Origin Access Control (OAC)
   - Configures SPA routing (403/404 → index.html)
   - Sets proper cache behaviors

5. **`scripts/update-app-runner-env.sh`**
   - Helper script to view/update App Runner environment variables
   - Shows current configuration
   - Provides update instructions

### Documentation

6. **`AWS_DEPLOYMENT_RUNBOOK.md`**
   - Complete deployment guide
   - Step-by-step instructions for:
     - RDS setup
     - App Runner configuration
     - Frontend deployment
     - Database migrations
     - Troubleshooting
   - Quick reference commands

## Key Features Implemented

### Production Safety Validations

- **SQLite Prevention**: App refuses to start if `DATABASE_URL` is SQLite in non-local environments
- **Dev Flag Prevention**: App refuses to start if `NERAVA_DEV_ALLOW_ANON_*` flags are enabled in production
- **JWT Secret Validation**: Already existed, now part of comprehensive validation suite

### Automatic Migrations

- Migrations run automatically on container startup
- Idempotent (safe for multiple instances)
- Fail-fast if migrations fail

### Frontend API Routing

- Detects CloudFront domains automatically
- Supports configuration via:
  - `window.NERAVA_API_BASE` (JavaScript)
  - `<meta name="nerava-api-base">` (HTML)
  - Environment variables (Vite)
  - localStorage overrides (for testing)

### CORS Configuration

- Backend validates CORS origins in non-local environments
- CloudFront domain can be added via `ALLOWED_ORIGINS` env var
- No wildcards allowed in production

## Next Steps (Manual Actions Required)

1. **Run Discovery Script**
   ```bash
   export APP_RUNNER_SERVICE_ARN="arn:..."
   export APP_RUNNER_URL="https://..."
   ./scripts/aws-discovery.sh
   ```

2. **Create RDS Postgres**
   ```bash
   DB_PASSWORD="..." ./scripts/setup-rds-postgres.sh
   ```

3. **Update App Runner Environment Variables**
   - Use AWS Console or CLI
   - Set all required variables (see runbook)
   - Update health check path to `/healthz`

4. **Deploy Frontend to S3**
   ```bash
   S3_BUCKET="..." ./scripts/deploy-frontend-s3.sh
   ```

5. **Create CloudFront Distribution**
   ```bash
   S3_BUCKET="..." ./scripts/create-cloudfront.sh
   ```

6. **Update Backend CORS**
   - Add CloudFront domain to `ALLOWED_ORIGINS` in App Runner

7. **Update Frontend Config**
   - Add `<meta name="nerava-api-base" content="https://app-runner-url">` to `index.html`

## Validation Checklist

After deployment, verify:

- [ ] `curl https://app-runner-url/healthz` returns 200
- [ ] `curl https://app-runner-url/openapi.json` returns 200
- [ ] App Runner logs show successful startup
- [ ] Migrations applied (check logs)
- [ ] Database is Postgres (check logs for dialect)
- [ ] CloudFront serves `index.html`
- [ ] Frontend JS can call `/healthz` without CORS errors
- [ ] Login flow works
- [ ] Wallet loads with real data

## Hard Failure Tests

Verify these fail correctly:

- [ ] SQLite in prod → App crashes on startup
- [ ] Dev flags in prod → App crashes on startup
- [ ] Missing JWT_SECRET in prod → App crashes on startup

## Notes

- All changes are backward compatible
- Local development still works (Dockerfile changes don't break local dev)
- Migrations are idempotent (safe for multi-instance deployments)
- Health check endpoint `/healthz` already existed, no changes needed
- CORS validation already existed, just needs CloudFront domain added



