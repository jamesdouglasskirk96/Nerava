# Fix Health Check Failure - Container Not Starting

**Date:** 2026-01-23
**Issue:** `v20-otp-fix-fixed` image fails health check - container not responding on port 8000
**Evidence:** App Runner service events show repeated "Health check failed on `/healthz`"

---

## Problem

```
[AppRunner] Health check failed on protocol `HTTP`[Path: '/healthz'], [Port: '8000']
[AppRunner] Deployment failed. Failure reason: Health check failed.
```

The container is either:
1. Crashing on startup (before it can respond)
2. Not listening on port 8000
3. Has an import/initialization error

---

## Step 1: Test Image Locally

```bash
cd /Users/jameskirk/Desktop/Nerava

# Pull the image from ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 566287346479.dkr.ecr.us-east-1.amazonaws.com

docker pull 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix-fixed

# Run locally with minimal env vars
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql://dummy:dummy@localhost:5432/dummy" \
  -e JWT_SECRET="test-secret-key" \
  -e ENV="dev" \
  566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix-fixed
```

**Watch for:**
- Import errors (`ModuleNotFoundError`)
- Syntax errors
- Configuration errors
- Port binding issues

---

## Step 2: Check Dockerfile

```bash
cat backend/Dockerfile
```

Verify:
- `EXPOSE 8000`
- Correct `CMD` or `ENTRYPOINT`
- Working directory is correct

---

## Step 3: Check Startup Script

```bash
# Check if there's a startup script
cat backend/start.sh 2>/dev/null || echo "No start.sh"

# Check main.py entrypoint
head -50 backend/app/main.py
```

---

## Step 4: Check for Import Errors

```bash
cd /Users/jameskirk/Desktop/Nerava/backend

# Test imports
python -c "from app.main import app; print('OK')"

# Check for missing dependencies
pip freeze | grep -i twilio
```

---

## Step 5: Compare Working vs Broken Image

```bash
# Check what's different between v19 (works) and v20 (fails)
docker pull 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v19-photo-fix

# Get image layers/history
docker history 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v19-photo-fix
docker history 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix-fixed
```

---

## Step 6: Check startup_validation.py

The startup validation might be failing silently:

```bash
cat backend/app/core/startup_validation.py
```

**Look for:**
- Calls to `settings.database_url` (should be `settings.DATABASE_URL`)
- Any `raise` statements that could crash the app
- Missing environment variable checks

---

## Step 7: Build Fresh Image

If the image is corrupted or has issues:

```bash
cd /Users/jameskirk/Desktop/Nerava

# Build fresh
docker build -t nerava-backend:v21-fresh ./backend

# Test locally
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql://dummy:dummy@localhost:5432/dummy" \
  -e JWT_SECRET="test-secret-key" \
  -e ENV="dev" \
  nerava-backend:v21-fresh

# In another terminal, test health
curl http://localhost:8000/healthz
```

**If health check works locally:**

```bash
# Tag and push
docker tag nerava-backend:v21-fresh 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v21-fresh
docker push 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v21-fresh

# Deploy
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v21-fresh",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {"Port": "8000"}
    },
    "AutoDeploymentsEnabled": false,
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
    }
  }'
```

---

## Common Causes of Health Check Failure

| Symptom | Cause | Fix |
|---------|-------|-----|
| Container exits immediately | Import error | Check `python -c "from app.main import app"` |
| Container runs but no response | Wrong port | Check `EXPOSE` in Dockerfile |
| Container runs but 500 error | Startup validation fails | Check env vars |
| Container hangs on startup | Blocking operation | Check for sync calls in startup |

---

## Step 8: Check if uvicorn is starting

Add debug logging to see if uvicorn even starts:

```python
# backend/app/main.py - add at top
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add before app creation
logger.info("Starting Nerava backend...")

# Add after app creation
logger.info(f"App created, listening on 0.0.0.0:8000")
```

---

## Quick Diagnosis Script

```bash
#!/bin/bash
echo "=== Diagnosing v20-otp-fix-fixed ==="

cd /Users/jameskirk/Desktop/Nerava

# Test python imports
echo "1. Testing imports..."
cd backend
python -c "
import sys
print(f'Python: {sys.version}')
try:
    from app.main import app
    print('✓ Main app imports OK')
except Exception as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)

try:
    from app.core.config import settings
    print(f'✓ Settings loaded')
    print(f'  DATABASE_URL defined: {hasattr(settings, \"DATABASE_URL\")}')
except Exception as e:
    print(f'✗ Settings failed: {e}')
"
cd ..

# Test Docker build
echo ""
echo "2. Building fresh image..."
docker build -t nerava-test:latest ./backend 2>&1 | tail -10

# Test container
echo ""
echo "3. Running container..."
docker run --rm -d --name nerava-test -p 8000:8000 \
  -e DATABASE_URL="postgresql://x:x@localhost:5432/x" \
  -e JWT_SECRET="test" \
  -e ENV="dev" \
  nerava-test:latest

sleep 5

echo ""
echo "4. Testing health..."
curl -s http://localhost:8000/healthz || echo "Health check failed"

echo ""
echo "5. Container logs:"
docker logs nerava-test 2>&1 | tail -20

docker stop nerava-test
```

---

## Expected Outcome

After fixing:
1. Container starts without errors
2. Health check returns `{"ok":true}`
3. Deployment succeeds
4. OTP endpoint works

---

**End of Health Check Fix Prompt**
