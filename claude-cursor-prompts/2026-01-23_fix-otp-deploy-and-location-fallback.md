# Fix OTP Deployment & Location Permission Fallback

**Date:** 2026-01-23
**Issues:**
1. OTP endpoint still times out after code fix (App Runner using old Docker image)
2. Location permission denied prevents charger display (no fallback)

---

## Issue 1: OTP Endpoint Still Timing Out

### Root Cause
The App Runner service is using an **old Docker image** (`nerava-backend:v19-photo-fix`) instead of the latest code with the async fix.

**Current state:**
- Code fix committed and pushed to GitHub ✓
- App Runner deployment triggered ✓
- But App Runner is configured to use a **specific ECR image tag**, not auto-deploy from GitHub

### Solution: Build and Deploy New Docker Image

#### Option A: Build and Push Manually

```bash
# 1. Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 566287346479.dkr.ecr.us-east-1.amazonaws.com

# 2. Build the backend image with the OTP fix
cd /Users/jameskirk/Desktop/Nerava
docker build -t nerava-backend:latest ./backend

# 3. Tag for ECR
docker tag nerava-backend:latest 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest
docker tag nerava-backend:latest 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix

# 4. Push to ECR
docker push 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest
docker push 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix

# 5. Update App Runner to use new image
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000"
      }
    },
    "AutoDeploymentsEnabled": false,
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
    }
  }'

# 6. Wait for deployment
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0]'
```

#### Option B: Trigger GitHub Actions Workflow

If the GitHub Actions workflow is set up to build and deploy:

```bash
# Check if workflow exists
cat .github/workflows/deploy-prod.yml

# Manually trigger workflow
gh workflow run deploy-prod.yml
```

### Verification After Deploy

```bash
# Test OTP endpoint
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 45

# Expected: {"otp_sent": true}
# Then check phone for 6-digit code
```

---

## Issue 2: Location Permission Denied - No Chargers Displayed

### Root Cause
When location permission is denied:
1. `coordinates` is null in DriverHome
2. `browseMode` stays false (default)
3. `effectiveCoordinates` becomes null
4. `intentRequest` becomes null, so API isn't called
5. Result: "No chargers available"

### Solution: Auto-enable Browse Mode When Location Denied

The fix adds a `useEffect` that automatically enables browse mode when location permission is denied or skipped.

#### File: `apps/driver/src/components/DriverHome/DriverHome.tsx`

Find the existing browse mode state:
```typescript
const [browseMode, setBrowseMode] = useState(false)
```

Add this useEffect AFTER the state declarations:
```typescript
// Auto-enable browse mode when location permission is denied or skipped
useEffect(() => {
  if (locationPermission === 'denied' || locationPermission === 'skipped') {
    setBrowseMode(true)
  }
}, [locationPermission])
```

#### Full Context - Where to Add

```typescript
// ... existing imports ...

export function DriverHome() {
  // ... existing state declarations ...
  const [browseMode, setBrowseMode] = useState(false)

  // ADD THIS useEffect right after browseMode state
  useEffect(() => {
    if (locationPermission === 'denied' || locationPermission === 'skipped') {
      setBrowseMode(true)
    }
  }, [locationPermission])

  // ... rest of component ...
}
```

### How Browse Mode Works

When `browseMode` is true:
- `effectiveCoordinates` uses default Austin coordinates: `{ lat: 30.2672, lng: -97.7431 }`
- The intent capture API is called with these coordinates
- Chargers from the database are displayed
- User can explore without granting location permission

### Verification

1. Open driver app in browser
2. Deny location permission when prompted
3. App should automatically switch to browse mode
4. Chargers should appear on the map (using Austin as default location)

---

## Combined Fix Checklist

### OTP Fix
- [ ] Build new Docker image with OTP async fix
- [ ] Push to ECR with new tag (e.g., `v20-otp-fix`)
- [ ] Update App Runner service to use new image
- [ ] Wait for deployment to complete
- [ ] Test OTP endpoint returns `{"otp_sent": true}`
- [ ] Verify SMS received on phone

### Location Fallback Fix
- [ ] Add useEffect for auto-enabling browse mode
- [ ] Test with location permission denied
- [ ] Verify chargers appear using default coordinates
- [ ] Commit and push changes

---

## Code Changes Summary

### Backend (OTP Fix - Already Committed)
- `backend/app/services/auth/twilio_verify.py` - Async executor pattern
- `backend/app/services/auth/twilio_sms.py` - Async executor pattern
- `backend/app/core/config.py` - Added `TWILIO_TIMEOUT_SECONDS`

### Frontend (Location Fallback)
- `apps/driver/src/components/DriverHome/DriverHome.tsx` - Auto-enable browse mode

---

## Testing Commands

```bash
# Test OTP after deploy
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}'

# Test intent capture API directly (simulating browse mode)
curl "https://api.nerava.network/v1/intent/capture?lat=30.2672&lng=-97.7431"

# Health check
curl "https://api.nerava.network/health"
```

---

**End of Fix Prompt**
