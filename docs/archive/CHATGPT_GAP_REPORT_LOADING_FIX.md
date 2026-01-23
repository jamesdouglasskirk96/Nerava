# Gap Report: Frontend Loading Issue Fix

**Purpose**: Provide ChatGPT with context to generate a comprehensive Cursor prompt
**Issue**: Frontend stuck on "Loading merchants..." animation
**Root Cause**: Authentication flow blocking unauthenticated requests in development

---

## Problem Summary

The new React frontend (`nerava-ui`) calls `POST /v1/intent/capture` to fetch nearby merchants based on user location. The endpoint requires authentication via `get_current_user` dependency, but:

1. Frontend does NOT send authentication tokens
2. Backend dev fallback (`NERAVA_DEV_ALLOW_ANON_USER`) is NOT enabled
3. Request fails with 401 or hangs, leaving UI in loading state

---

## Current Architecture

### Frontend (nerava-ui)

**Location**: `/Users/jameskirk/Desktop/Nerava/nerava-ui`
**Stack**: React + Vite + TypeScript + TanStack Query

**Flow**:
```
WhileYouChargeScreen.tsx
  → useGeolocation hook (gets lat/lng)
  → useIntentCapture hook (calls API)
  → fetchAPI('/v1/intent/capture', {...})
  → Response never received OR 401 error
  → isLoading stays true forever
```

**Key Files**:
- `src/components/WhileYouCharge/WhileYouChargeScreen.tsx` - Main screen
- `src/services/api.ts` - API client with `fetchAPI()` and `useIntentCapture()`
- `src/hooks/useGeolocation.ts` - Geolocation hook

**Problem**: `fetchAPI()` doesn't include Authorization header:
```typescript
// api.ts ~line 20-30
export async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      // NO Authorization header!
    },
    ...options,
  })
```

### Backend (nerava-backend-v9)

**Location**: `/Users/jameskirk/Desktop/Nerava/nerava-backend-v9`
**Stack**: FastAPI + SQLAlchemy + Pydantic

**Intent Endpoint**:
```python
# app/routers/intent.py:50-54
@router.post("/capture", ...)
async def capture_intent(
    request: CaptureIntentRequest,
    current_user: User = Depends(get_current_user),  # <-- REQUIRES AUTH
    db: Session = Depends(get_db),
):
```

**Auth Dependency Chain**:
```python
# app/dependencies/domain.py
get_current_user_public_id()
  → Checks Authorization header for Bearer token
  → Checks Cookie for access_token
  → If neither found:
      → If DEV_ALLOW_ANON_USER_ENABLED: use user_id=1
      → Else: raise HTTPException(401)

get_current_user()
  → Depends on get_current_user_public_id()
  → Fetches User from database
```

**Dev Fallback Flag**:
```python
# app/dependencies/domain.py:20-23
DEV_ALLOW_ANON_USER_ENABLED = (
    os.getenv("NERAVA_DEV_ALLOW_ANON_USER", "false").lower() == "true"
    and is_local_env()
)
```

---

## Gaps to Fix

### Gap 1: Frontend Missing Auth Token Handling

**Current State**:
- No auth token storage
- No auth token transmission
- No auth error handling

**Required**:
- Store JWT token after login (localStorage or cookie)
- Include `Authorization: Bearer <token>` header in API calls
- Handle 401 errors gracefully (redirect to login or use dev fallback)

### Gap 2: Dev Mode UX for Unauthenticated Users

**Current State**:
- Dev fallback exists but requires env var
- No way to test without auth in development
- No clear error message when auth fails

**Required**:
- Frontend should detect dev mode and show helpful message
- Backend should return clear error message (not hang)
- Consider adding a "dev login" button for testing

### Gap 3: Error Handling in React Query

**Current State**:
```typescript
// useIntentCapture doesn't handle errors well
return useQuery({
  queryKey: ['intent-capture', request],
  queryFn: () => fetchAPI<CaptureIntentResponse>('/v1/intent/capture', {...}),
  enabled: request !== null,
  // No onError, no retry config
})
```

**Required**:
- Add retry config
- Handle specific error codes (401, 500, network errors)
- Show user-friendly error messages
- Provide retry button

### Gap 4: Loading State Timeout

**Current State**:
- Loading animation shows indefinitely
- No timeout or fallback
- User stuck waiting forever

**Required**:
- Add timeout to loading state (e.g., 10 seconds)
- Show error state after timeout
- Provide retry button

### Gap 5: Backend CORS for Errors

**Current State**:
- CORS configured for successful responses
- May not apply to 401 error responses

**Required**:
- Verify CORS headers on error responses
- Ensure 401 response includes proper CORS headers

---

## Recommended Fixes

### Option A: Enable Dev Fallback (Quick Fix)

1. Start backend with: `NERAVA_DEV_ALLOW_ANON_USER=true`
2. Frontend works without auth
3. Good for development only

### Option B: Implement Auth Flow (Production Fix)

1. Add login page to frontend
2. Store JWT token after login
3. Include token in all API calls
4. Handle token refresh

### Option C: Hybrid Approach (Recommended)

1. **Frontend**: Add auth token handling if available
2. **Frontend**: Detect missing token in dev mode, show helper
3. **Backend**: Keep dev fallback for local testing
4. **Both**: Add proper error handling and timeouts

---

## Files to Modify

### Frontend Files

| File | Changes Needed |
|------|----------------|
| `src/services/api.ts` | Add auth token header, error handling |
| `src/hooks/useAuth.ts` | Create auth context/hook (new file) |
| `src/components/WhileYouCharge/WhileYouChargeScreen.tsx` | Add error state, timeout |
| `src/App.tsx` | Add auth provider |

### Backend Files

| File | Changes Needed |
|------|----------------|
| `app/dependencies/domain.py` | Already has dev fallback, just needs env var |
| `app/routers/intent.py` | Consider adding public endpoint for dev |
| `app/main_simple.py` | Verify CORS includes error responses |

---

## Environment Variables Required

### Backend (for dev testing)
```bash
NERAVA_DEV_ALLOW_ANON_USER=true
MOCK_PLACES=true
ENV=local
```

### Frontend
```bash
VITE_API_BASE=http://localhost:8001
VITE_DEV_MODE=true  # Optional: show dev helpers
```

---

## Test Cases to Verify Fix

1. **Without Auth, Dev Mode**: Should use fallback user, return merchants
2. **With Auth**: Should authenticate normally, return merchants
3. **Network Error**: Should show error message, not hang
4. **Backend Down**: Should show connection error
5. **401 Error**: Should show auth required message (not hang)
6. **Timeout**: Should show timeout message after 10 seconds

---

## Key Code References

### Frontend API Client (Current)
```typescript
// nerava-ui/src/services/api.ts
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

export async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })
  // ... no auth handling
}
```

### Backend Auth Dependency (Current)
```python
# nerava-backend-v9/app/dependencies/domain.py:61-69
if DEV_ALLOW_ANON_USER_ENABLED:
    print("[AUTH][DEV] NERAVA_DEV_ALLOW_ANON_USER=true -> using default user")
    user = AuthService.get_user_by_id(db, 1)
    if user:
        return user.public_id
    return "dev-user-public-id"

# If not dev mode, raises 401
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)
```

---

## Context for Cursor Prompt

When generating the Cursor prompt, ChatGPT should include:

1. **Objective**: Fix the loading issue by implementing proper auth handling
2. **Scope**: Frontend API client, error handling, optional backend tweaks
3. **Constraints**:
   - Keep existing dev fallback mechanism
   - Don't break production auth
   - Use existing patterns from codebase
4. **Success Criteria**:
   - Loading resolves within 10 seconds (success or error)
   - Clear error messages for auth failures
   - Dev mode works without manual token generation
5. **Files to Reference**:
   - `nerava-ui/src/services/api.ts`
   - `nerava-ui/src/components/WhileYouCharge/WhileYouChargeScreen.tsx`
   - `nerava-backend-v9/app/dependencies/domain.py`
   - `nerava-backend-v9/app/routers/intent.py`

---

## Additional Notes

1. The backend dev fallback works correctly when `NERAVA_DEV_ALLOW_ANON_USER=true`
2. The frontend currently has no auth infrastructure
3. The React Query setup is minimal and lacks error handling
4. The loading animation component exists but has no timeout logic
5. CORS is configured in `main_simple.py` for localhost:5173

This gap report should give ChatGPT enough context to generate a comprehensive Cursor prompt that addresses all the issues.
