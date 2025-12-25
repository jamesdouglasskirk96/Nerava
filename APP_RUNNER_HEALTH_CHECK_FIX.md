# App Runner Health Check Hardening - Implementation Summary

## Changes Made

### 1. Non-blocking Startup (`main_simple.py`)
- Modified `@app.on_event("startup")` to use `asyncio.create_task()` instead of `await`
- Background services (Nova accrual, HubSpot sync) now start asynchronously without blocking HTTP server startup
- Added `APP_STARTUP_MODE` environment variable support:
  - `light` (default): Skips optional workers for faster startup
  - `full`: Starts all background workers (for staging/long-lived instances)

### 2. Improved `/readyz` Endpoint (`main_simple.py`)
- Added proper async timeouts:
  - Database check: 2 seconds
  - Redis check: 1 second
- Uses `asyncio.wait_for()` to prevent hanging
- Returns 503 if dependencies are unavailable, 200 if all pass
- Checks run concurrently for faster response

### 3. Enhanced `/healthz` Endpoint (`main_simple.py`)
- Already simple (no DB/Redis checks) - enhanced with better logging
- Returns 200 immediately when HTTP server is running
- Added explicit documentation that this is a liveness probe

### 4. Early Logging (`main_simple.py`)
- Added structured logging at app creation
- Added logging at startup event entry/exit
- All logs flush to stdout for App Runner visibility

### 5. Deprecated Conflicting Endpoints
- **`routers/health.py`**: `/v1/healthz` now returns simple response without DB check (deprecated)
- **`routers/ops.py`**: Removed `/healthz` endpoint (root-level is authoritative)

## AWS App Runner Configuration

After deployment, configure App Runner health check with these settings:

### Health Check Configuration
- **Path**: `/healthz`
- **Timeout**: **10 seconds** (increase from 5)
- **Interval**: 10 seconds
- **Healthy threshold**: 1
- **Unhealthy threshold**: 5

### AWS CLI Command
```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend-stable/6ab3cf05e76c46c292f54d144894919a" \
  --health-check-configuration \
    Path=/healthz,Protocol=HTTP,Interval=10,Timeout=10,HealthyThreshold=1,UnhealthyThreshold=5 \
  --region us-east-1
```

### AWS Console Steps
1. Navigate to App Runner service: `nerava-backend-stable`
2. Go to **Configuration** → **Health check**
3. Update settings:
   - **Path**: `/healthz`
   - **Timeout**: `10` seconds
   - **Interval**: `10` seconds
   - **Healthy threshold**: `1`
   - **Unhealthy threshold**: `5`
4. Save and deploy

## Environment Variables

### Required for Production
- `STRIPE_WEBHOOK_SECRET` - Required for webhook verification (validated in lifespan.py)
- `JWT_SECRET` - Must be set and not equal to `dev-secret` or `DATABASE_URL`
- `TOKEN_ENCRYPTION_KEY` - Required for secure token storage
- `DATABASE_URL` - Must be PostgreSQL (not SQLite) in production

### Optional
- `APP_STARTUP_MODE` - Set to `light` (default) for App Runner, `full` for staging/long-lived instances

## Testing

### Verify Health Checks
```bash
# Liveness check (should return 200 immediately)
curl https://35udmmcgut.us-east-1.awsapprunner.com/healthz

# Readiness check (returns 200 if DB/Redis available, 503 otherwise)
curl https://35udmmcgut.us-east-1.awsapprunner.com/readyz
```

### Verify Startup
- Check App Runner logs for `[STARTUP]` messages
- Verify startup completes quickly (should not block on background services)
- Verify `/healthz` returns 200 within seconds of container start

## Key Improvements

1. **Startup no longer blocks** - Background services start asynchronously
2. **Health checks are fast** - `/healthz` returns immediately without dependencies
3. **Readiness is separate** - `/readyz` checks dependencies with timeouts
4. **Light mode by default** - Skips optional workers for faster startup
5. **Better logging** - Early logging helps diagnose startup issues

## Notes

- The root-level `/healthz` endpoint is the authoritative health check for App Runner
- `/readyz` can be used for monitoring but should not be used for App Runner health checks
- In `light` mode, optional background workers are skipped - this is intentional for App Runner deployments
- All startup failures are logged but don't crash the application (except for critical validation errors)

