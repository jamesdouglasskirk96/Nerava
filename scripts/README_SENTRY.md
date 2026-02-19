# Sentry Error Tracking Configuration

This document describes how to configure Sentry error tracking for the Nerava backend and frontend.

## Backend Configuration

### Environment Variables

The backend uses the following environment variables for Sentry:

- `SENTRY_DSN` - Your Sentry DSN (required)
- `SENTRY_ENVIRONMENT` - Environment name (defaults to `prod` or value of `ENV`)
- `SENTRY_ENABLED` - Enable/disable Sentry (defaults to `true`)

### Current Sentry DSN

```
https://1341c6825636c6edf9c2e40f8901c07f@o4510756278697984.ingest.us.sentry.io/4510756291739648
```

### Updating App Runner Service

To update the App Runner service with Sentry DSN:

```bash
export SENTRY_DSN="https://1341c6825636c6edf9c2e40f8901c07f@o4510756278697984.ingest.us.sentry.io/4510756291739648"
export SENTRY_ENVIRONMENT="prod"
export SERVICE_NAME="nerava-backend"

./scripts/update_sentry_dsn.sh
```

Or use the deployment script which now includes Sentry configuration:

```bash
export SENTRY_DSN="https://1341c6825636c6edf9c2e40f8901c07f@o4510756278697984.ingest.us.sentry.io/4510756291739648"
export SENTRY_ENVIRONMENT="prod"

./scripts/deploy_api_apprunner.sh
```

### Testing Sentry

Test that Sentry is working by calling the test endpoint:

```bash
curl -H "X-Internal-Test: test" https://api.nerava.network/v1/internal/sentry-test
```

This will trigger a test error that should appear in your Sentry dashboard.

## Frontend Configuration

### Environment Variables

The frontend uses the following environment variables (set at build time):

- `VITE_SENTRY_DSN` - Your Sentry DSN (required)
- `VITE_SENTRY_ENVIRONMENT` - Environment name (defaults to `development`)

### Building with Sentry

When deploying the frontend, set the Sentry DSN before building:

```bash
export VITE_SENTRY_DSN="https://1341c6825636c6edf9c2e40f8901c07f@o4510756278697984.ingest.us.sentry.io/4510756291739648"
export VITE_SENTRY_ENVIRONMENT="production"

./scripts/deploy_static_sites.sh
```

Or set it in the deployment script:

```bash
export VITE_SENTRY_DSN="https://1341c6825636c6edf9c2e40f8901c07f@o4510756278697984.ingest.us.sentry.io/4510756291739648"
export VITE_SENTRY_ENVIRONMENT="production"
export API_BASE_URL="https://api.nerava.network"

./scripts/deploy_static_sites.sh
```

## Sentry Dashboard

Access your Sentry dashboard at:
https://sentry.io/organizations/[your-org]/projects/[your-project]/

## Configuration Files

- Backend Sentry initialization: `nerava-backend-v9 2/app/core/sentry.py`
- Frontend Sentry initialization: `nerava-app-driver/src/lib/sentry.ts`
- Backend config: `nerava-backend-v9 2/app/core/config.py`

## Features

### Backend
- Automatic error capture for unhandled exceptions
- FastAPI integration for HTTP errors
- SQLAlchemy integration for database errors
- Performance monitoring (10% sample rate)
- PII scrubbing (emails, passwords, tokens)

### Frontend
- Automatic error capture for unhandled exceptions
- Browser tracing integration
- Session replay (10% sample rate, 100% on errors)
- PII scrubbing (location data)





