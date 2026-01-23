# Dockerfile Fix Summary

## Problem Identified

App Runner containers were not starting. The pattern was:
1. ✅ Image pulled from ECR successfully
2. ✅ Instance provisioning started
3. ❌ Container never started (no application logs)
4. ❌ Health check timed out after 20+ minutes

## Root Cause

The Dockerfile used shell form CMD with variable expansion that doesn't work reliably in App Runner:

```dockerfile
CMD ["/bin/sh", "-c", "python -m uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Issues:
1. Shell form CMD with `${PORT:-8000}` variable expansion may not work in App Runner's environment
2. Using `python` instead of `python3` - `python` may not be available in App Runner
3. Variable expansion in shell form is less reliable than exec form

## Fix Applied

Updated `backend/Dockerfile` to use exec form with explicit `python3`:

```dockerfile
# Run uvicorn with exec form (more reliable than shell form)
# Use python3 explicitly and hardcode port 8000 (App Runner sets PORT=8000 in env)
CMD ["python3", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

Changes:
1. ✅ Switched from shell form to exec form CMD
2. ✅ Changed `python` to `python3` (explicit)
3. ✅ Hardcoded port 8000 (App Runner always sets PORT=8000)
4. ✅ Removed HEALTHCHECK (App Runner has its own health checks)

## Testing

✅ Local Docker test passed:
- Container starts successfully
- Health endpoint responds: `{"ok": true, "service": "nerava-backend", "version": "0.9.0", "status": "healthy"}`
- Application logs show proper startup

## Image Pushed

Fixed image pushed to ECR:
- Tag: `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v8-discovery-fixed`
- Digest: `sha256:84b7cbb99416e5a90b58297fe89de03c3b014d25c166949cb305afc19de5a133`

## Next Steps

1. Wait for current stuck services to fail or timeout
2. Delete stuck services once they're deletable
3. Create new service using fixed image: `v8-discovery-fixed`
4. Verify container starts and application logs appear
5. Test health and discovery endpoints

## Deployment Script Updated

The deployment script (`scripts/create-fresh-apprunner-service.sh`) now defaults to using the fixed image tag.

## Verification Commands

Once new service is created with fixed image:

```bash
# Check service status
aws apprunner describe-service --service-arn <ARN> --region us-east-1

# Check for application logs (should see Python/FastAPI startup logs)
aws logs tail /aws/apprunner/nerava-backend-v2/*/service --follow --region us-east-1

# Test health endpoint
curl https://<service-url>/healthz

# Test discovery endpoint
curl "https://<service-url>/v1/chargers/discovery?lat=30.27&lng=-97.74"
```

## Expected Behavior After Fix

1. ✅ Image pulled from ECR
2. ✅ Instance provisioning starts
3. ✅ **Container starts** (application logs appear)
4. ✅ **Health check passes** within 1-2 minutes
5. ✅ Service reaches RUNNING status


