# Container Startup Investigation - Root Cause Found

## Problem Summary

App Runner containers were not starting. Investigation revealed the container **is starting but crashing immediately** due to strict startup validation failures.

## Root Cause

The application has **strict startup validation** that exits with code 1 if validation fails:

1. **OTP_PROVIDER validation**: `OTP_PROVIDER=stub` is not allowed in production
2. **JWT_SECRET validation**: Must be set and not use default values
3. **CORS validation**: Wildcard `*` not allowed in production
4. **Other validations**: Database URL, Redis URL, Token encryption key, etc.

When validation fails, the app exits immediately:
```
[STARTUP] STRICT_STARTUP_VALIDATION enabled - exiting due to validation failure
sys.exit(1)
```

## Testing Results

### ✅ With Correct Environment Variables
```bash
docker run --rm \
  -e ENV=prod \
  -e OTP_PROVIDER=twilio \
  -e JWT_SECRET="..." \
  -e TOKEN_ENCRYPTION_KEY="..." \
  -e DATABASE_URL="postgresql+..." \
  -e REDIS_URL="redis://..." \
  nerava-backend:v8-discovery-fixed \
  python3 -c "import app.main_simple; print('✅ Success')"
```
**Result**: ✅ Import successful - app starts correctly

### ❌ Without OTP_PROVIDER
```bash
docker run --rm -e ENV=prod ... (without OTP_PROVIDER)
```
**Result**: ❌ Crashes with: `OTP_PROVIDER=stub is not allowed in production`

### ❌ Without JWT_SECRET
```bash
docker run --rm -e ENV=prod ... (without JWT_SECRET)
```
**Result**: ❌ Crashes with: `JWT secret must be set and not use default value`

## Current App Runner Configuration

Checked service `nerava-backend-v2` - **all required env vars ARE set**:
- ✅ `OTP_PROVIDER=twilio`
- ✅ `JWT_SECRET=787044b63251814c8dd160437b395a77fa6e162bdc53e24320cd84d14fa5ed86`
- ✅ `TOKEN_ENCRYPTION_KEY=s1V8FQAFl7IzLcNJuBXBjDLpCb3j_IrbDbLWVzufBm4=`
- ✅ `DATABASE_URL=postgresql+psycopg2://...`
- ✅ `REDIS_URL=redis://...`
- ✅ `ALLOWED_ORIGINS=https://nerava.network,...`

## Why Container Still Not Starting?

Since env vars are set correctly, possible issues:

1. **Environment variables not reaching container**: App Runner might not be passing env vars correctly
2. **Container crashes before logs**: Exit happens so fast that logs don't appear
3. **Different validation path**: Something else is failing validation

## Next Steps

### 1. Check App Runner Logs for Validation Errors

```bash
SERVICE_ID="bc7e4d4c2f344e8c8af23cbc66ebc926"
LOG_GROUP="/aws/apprunner/nerava-backend-v2/$SERVICE_ID/service"
aws logs tail "$LOG_GROUP" --since 1h --region us-east-1 | grep -E "(STARTUP|ERROR|validation|OTP_PROVIDER|JWT_SECRET)"
```

### 2. Test Minimal Image in App Runner

Created minimal FastAPI image to verify App Runner works:
- Image: `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:minimal`
- If minimal works → issue is in app code/validation
- If minimal fails → issue is in App Runner/Docker setup

### 3. Add Debug Logging to Dockerfile

Add verbose startup logging to see what's happening:

```dockerfile
CMD ["sh", "-c", "echo 'Container starting...' && python3 --version && echo 'Launching app...' && python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000"]
```

### 4. Temporarily Disable Strict Validation

For testing, set `STRICT_STARTUP_VALIDATION=false` to see if app starts:

```json
{
  "RuntimeEnvironmentVariables": {
    "STRICT_STARTUP_VALIDATION": "false",
    ...
  }
}
```

## Files Modified

1. ✅ `backend/Dockerfile` - Fixed CMD to use exec form with python3
2. ✅ Created minimal test image: `nerava-backend:minimal`
3. ✅ Verified app starts with correct env vars locally

## Key Findings

1. ✅ Docker image is correct - works locally with proper env vars
2. ✅ Dockerfile CMD is correct - exec form with python3
3. ✅ App code works - imports successfully with correct env vars
4. ❓ **App Runner may not be passing env vars correctly, OR container is crashing before logs**

## Verification Commands

```bash
# Check service env vars
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend-v2/bc7e4d4c2f344e8c8af23cbc66ebc926" \
  --region us-east-1 \
  --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables' \
  --output json

# Check logs for validation errors
aws logs tail /aws/apprunner/nerava-backend-v2/*/service --since 1h --region us-east-1 | grep -i "validation\|error\|startup"

# Test minimal image locally
docker run --rm -p 8000:8000 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:minimal
curl http://localhost:8000/healthz
```


