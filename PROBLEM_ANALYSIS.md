# Problem Analysis: Loading Merchants Animation Not Going Away

## Executive Summary
The frontend application is stuck in a loading state because API calls to `/v1/intent/capture` are failing due to authentication requirements. The backend endpoint requires user authentication, but the frontend is not sending authentication tokens, and the development fallback mechanism (`NERAVA_DEV_ALLOW_ANON_USER`) is not enabled.

---

## Root Cause Analysis

### 1. **Authentication Dependency Chain**

**Backend Endpoint:** `POST /v1/intent/capture`
- **Location:** `nerava-backend-v9/app/routers/intent.py:50-54`
- **Dependency:** `current_user: User = Depends(get_current_user)`
- **Status:** ✅ Requires authentication

**Authentication Flow:**
```
POST /v1/intent/capture
  ↓
get_current_user (dependency)
  ↓
get_current_user_public_id (dependency)
  ↓
Checks for JWT token in:
  1. Authorization header (Bearer token)
  2. Cookie (access_token)
  ↓
If no token found:
  → Check DEV_ALLOW_ANON_USER_ENABLED flag
  → If false → Raise HTTPException(401, "Not authenticated")
  → If true → Use user_id=1 as fallback
```

### 2. **Dev Fallback Mechanism**

**Code Location:** `nerava-backend-v9/app/dependencies/domain.py:20-23`

```python
DEV_ALLOW_ANON_USER_ENABLED = (
    os.getenv("NERAVA_DEV_ALLOW_ANON_USER", "false").lower() == "true"
    and is_local_env()
)
```

**Current State:**
- ❌ `NERAVA_DEV_ALLOW_ANON_USER` environment variable is **NOT SET**
- ❌ Default value is `"false"` (string)
- ❌ `DEV_ALLOW_ANON_USER_ENABLED` evaluates to `False`
- ❌ Backend raises `HTTPException(401)` when no token is provided

### 3. **Frontend API Call**

**Code Location:** `nerava-ui/src/services/api.ts:47-57`

```typescript
export function useIntentCapture(request: CaptureIntentRequest | null) {
  return useQuery({
    queryKey: ['intent-capture', request],
    queryFn: () => fetchAPI<CaptureIntentResponse>('/v1/intent/capture', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
    enabled: request !== null,
  })
}
```

**Issues:**
- ❌ No `Authorization` header sent
- ❌ No authentication token provided
- ❌ Request fails with "Failed to fetch" (network error or 401)

### 4. **Error Manifestation**

**Browser Console:**
```
[ERROR] [API] Fetch error: TypeError: Failed to fetch
```

**Network Tab:**
- Request: `POST http://localhost:8001/v1/intent/capture`
- Status: No response received (hanging or connection refused)
- Error: `TypeError: Failed to fetch`

**React Query State:**
- `isLoading: true` (stuck)
- `error: null` (initially, then becomes error object)
- `status: "pending"` (never resolves)

---

## Detailed Problem Breakdown

### Problem 1: Missing Authentication Token
**Severity:** 🔴 Critical

**What's Happening:**
- Frontend makes unauthenticated request
- Backend dependency `get_current_user` requires authentication
- No token in request headers or cookies
- Backend rejects request with 401 Unauthorized

**Why It's Not Visible:**
- The error might be happening but not properly logged
- Network request might be timing out before 401 response
- CORS preflight might be failing
- Backend might not be running or not responding

### Problem 2: Dev Fallback Not Enabled
**Severity:** 🔴 Critical

**What's Happening:**
- `NERAVA_DEV_ALLOW_ANON_USER` environment variable is not set
- Backend defaults to production mode (requires auth)
- Dev fallback code path never executes
- Even in local development, authentication is required

**Expected Behavior:**
```python
# If NERAVA_DEV_ALLOW_ANON_USER=true AND is_local_env():
if DEV_ALLOW_ANON_USER_ENABLED:
    print("[AUTH][DEV] NERAVA_DEV_ALLOW_ANON_USER=true -> using default user")
    user = AuthService.get_user_by_id(db, 1)
    if user:
        return user.public_id
```

**Actual Behavior:**
```python
# DEV_ALLOW_ANON_USER_ENABLED = False
# Falls through to:
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)
```

### Problem 3: Backend Server State Unknown
**Severity:** 🟡 Medium

**What's Happening:**
- Backend process might not be running
- Backend might be running but not responding
- Backend might be running on wrong port
- Backend might have crashed during startup

**Evidence:**
- "Failed to fetch" suggests connection issue
- No response status logged (suggests request never completes)
- Network tab shows request but no response

### Problem 4: CORS Configuration
**Severity:** 🟢 Low (Likely OK)

**What's Happening:**
- CORS middleware is configured in `main_simple.py`
- `localhost:5173` is in allowed origins list
- Should work, but worth verifying

**Code Location:** `nerava-backend-v9/app/main_simple.py:765-773`

---

## Solution Steps

### Step 1: Verify Backend is Running
```bash
# Check if backend process is running
lsof -ti:8001

# Check backend health
curl http://localhost:8001/healthz
```

### Step 2: Enable Dev Authentication Fallback
```bash
# Option A: Set environment variable when starting backend
cd nerava-backend-v9
export NERAVA_DEV_ALLOW_ANON_USER=true
export MOCK_PLACES=true
python3 -m uvicorn app.main_simple:app --port 8001 --reload

# Option B: Add to .env file
echo "NERAVA_DEV_ALLOW_ANON_USER=true" >> .env
echo "MOCK_PLACES=true" >> .env
```

### Step 3: Verify Environment Detection
The backend checks `is_local_env()` which likely checks:
- `ENV` environment variable
- `REGION` environment variable
- Defaults to local if not set

**Code Location:** `nerava-backend-v9/app/core/env.py`

### Step 4: Test Backend Endpoint Directly
```bash
# Test with curl (should fail without auth)
curl -X POST http://localhost:8001/v1/intent/capture \
  -H "Content-Type: application/json" \
  -d '{"lat":30.4053865,"lng":-97.6717792,"accuracy_m":50}'

# Expected: 401 Unauthorized (if dev flag not set)
# Expected: 200 OK with JSON response (if dev flag is set)
```

### Step 5: Check Backend Logs
Look for these log messages:
- `[AUTH][DEV] NERAVA_DEV_ALLOW_ANON_USER=true -> using default user` ✅ (if working)
- `>>>> REQUEST POST /v1/intent/capture <<<<` ✅ (if request received)
- `>>>> RESPONSE POST /v1/intent/capture -> 401 <<<<` ❌ (if auth fails)

---

## Alternative Solutions

### Option A: Add Authentication to Frontend (Production Approach)
1. Implement login flow
2. Store JWT token in localStorage/cookies
3. Send token in `Authorization: Bearer <token>` header
4. Handle token refresh

**Pros:** Production-ready, secure
**Cons:** More complex, requires auth UI

### Option B: Enable Dev Fallback (Development Approach)
1. Set `NERAVA_DEV_ALLOW_ANON_USER=true`
2. Backend uses user_id=1 automatically
3. No frontend changes needed

**Pros:** Simple, quick fix for development
**Cons:** Only works in local environment

### Option C: Create Test User and Token
1. Create test user in database
2. Generate JWT token for test user
3. Hardcode token in frontend for development

**Pros:** Tests real auth flow
**Cons:** Token expires, requires token refresh logic

---

## Recommended Fix (Immediate)

**For Development:**
```bash
# Stop current backend (if running)
pkill -f "uvicorn app.main_simple"

# Start backend with dev flags
cd nerava-backend-v9
export NERAVA_DEV_ALLOW_ANON_USER=true
export MOCK_PLACES=true
export ENV=local
python3 -m uvicorn app.main_simple:app --port 8001 --reload
```

**Verify:**
1. Check backend logs for `[AUTH][DEV]` message
2. Test endpoint with curl (should return 200)
3. Refresh frontend (should load merchants)

---

## Files Involved

### Backend:
- `nerava-backend-v9/app/routers/intent.py` - Endpoint definition
- `nerava-backend-v9/app/dependencies/domain.py` - Auth dependency
- `nerava-backend-v9/app/main_simple.py` - CORS configuration
- `nerava-backend-v9/app/core/env.py` - Environment detection

### Frontend:
- `nerava-ui/src/services/api.ts` - API client
- `nerava-ui/src/components/WhileYouCharge/WhileYouChargeScreen.tsx` - UI component
- `nerava-ui/src/hooks/useGeolocation.ts` - Geolocation hook

---

## Testing Checklist

- [ ] Backend is running on port 8001
- [ ] `NERAVA_DEV_ALLOW_ANON_USER=true` is set
- [ ] `MOCK_PLACES=true` is set (for deterministic test data)
- [ ] Backend logs show `[AUTH][DEV]` message
- [ ] `curl` test returns 200 OK
- [ ] Frontend API call succeeds
- [ ] React Query resolves with data
- [ ] UI displays merchants (not loading state)

---

## Additional Notes

### Why "Failed to fetch" Instead of 401?
The "Failed to fetch" error typically indicates:
1. Network connection issue (backend not running)
2. CORS preflight failure
3. Request timeout before response
4. Browser blocking the request

If backend was returning 401, we'd see:
- `[API] Response status: 401 Unauthorized` in console
- Error message in React Query error state

The fact that we're seeing "Failed to fetch" suggests the backend might not be responding at all, or there's a network-level issue.

### Location: Tesla Supercharger
The mock location is set to:
- **Address:** 500 W Canyon Ridge Dr, Austin, TX 78753
- **Coordinates:** lat=30.4053865, lng=-97.6717792

This location should work with `MOCK_PLACES=true` to return deterministic test merchants (Asadas Grill, Eggman ATX, etc.).




