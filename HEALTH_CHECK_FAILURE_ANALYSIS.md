# Health Check Failure - Root Cause Analysis

## Current Situation

**Service Status:** OPERATION_IN_PROGRESS  
**Service URL:** xgxqvxxnjv.us-east-1.awsapprunner.com  
**Health Check:** HTTP 404 Not Found  
**Application Logs:** None visible in CloudWatch

## Investigation Results

### ✅ Issues Fixed
1. **Config Router Import** - Fixed (changed `config_router` to `config_router.router`)

### ✅ Configuration Verified
1. **Environment Variables** - All present and correct:
   - `ENV=prod` ✅
   - `DATABASE_URL` - Set to RDS PostgreSQL ✅
   - `REDIS_URL` - Set to ElastiCache ✅
   - `DEMO_MODE` - Not set (nova_accrual won't start) ✅
   - All required secrets present ✅

2. **VPC Connector** - Configured and attached ✅
3. **Network Configuration** - VPC egress configured ✅
4. **Health Check Configuration** - Path: `/healthz`, Port: 8000 ✅

### ❌ Missing/Unknown

1. **Application Logs** - No logs visible in CloudWatch
   - Expected: `[STARTUP]` messages should appear
   - Actual: Only App Runner infrastructure logs
   - **ObservabilityEnabled: null** - May indicate logging not configured

2. **Application Startup Status** - Unknown
   - Cannot determine if application is starting, running, or crashing
   - 404 response suggests routes not registered (app not started or crashed)

## Root Cause Hypothesis

### Most Likely: Application Startup Failure (Silent Crash)

**Evidence:**
- No application logs appear (even early startup prints)
- Health check returns 404 (routes not registered)
- Local test shows application starts successfully
- Environment variables are correct

**Possible Causes:**
1. **Database Connection Failure**
   - App tries to connect to RDS during startup
   - Connection fails (timeout, unreachable, auth failure)
   - Application crashes or hangs before logging anything
   - No error captured because process dies too quickly

2. **Import/Module Error**
   - Python module import fails during startup
   - Error occurs before logging is configured
   - Process exits with non-zero code
   - App Runner retries but keeps failing

3. **Config Validation Failure**
   - Startup validation in `config.py` raises exception
   - Exception not caught, process exits
   - Happens before FastAPI app initialization

### Less Likely: CloudWatch Logging Not Forwarding

**Evidence:**
- ObservabilityEnabled is null
- But App Runner should forward stdout/stderr by default

**If this is the issue:**
- Application might actually be running
- Health check 404 could be for different reason
- Need to enable observability to see logs

## Recommended Actions

### 1. Check Database Connectivity (IMMEDIATE)
Test if App Runner instances can reach RDS:
```bash
# Check RDS security group inbound rules
# Verify VPC Connector security group can access RDS on port 5432
# Test connection from App Runner network
```

### 2. Add Startup Error Handling (IMMEDIATE)
Wrap critical startup code in try/except to ensure errors are logged:
```python
# In main_simple.py startup event handler
try:
    # Startup code
except Exception as e:
    print(f"[STARTUP ERROR] {e}", flush=True)
    logger.error(f"Startup failed: {e}", exc_info=True)
    raise  # Re-raise to fail fast
```

### 3. Simplify Health Check (IMMEDIATE)
Make `/healthz` endpoint even simpler - avoid any database/import dependencies:
```python
@app.get("/healthz")
async def root_healthz():
    """Minimal health check - no dependencies"""
    return {"ok": True}
```

### 4. Enable CloudWatch Observability (HIGH PRIORITY)
Create observability configuration to ensure logs are captured:
```bash
aws apprunner create-observability-configuration \
  --observability-configuration-name nerava-backend-observability \
  --trace-configuration Vendor=AWSXRAY
```

### 5. Test Database Connection from VPC
Create a simple test script to verify RDS connectivity from App Runner network.

## Next Steps

1. **Enable observability** to see application logs
2. **Verify RDS security group** allows traffic from VPC Connector
3. **Test database connection** with App Runner credentials
4. **Add more defensive error handling** in startup code
5. **Monitor service status** until it transitions to RUNNING or shows clear error

The critical missing piece is **visibility** - we need to see what's happening during startup to diagnose the root cause.

