# PostHog Events Missing for Saturday Jan 24, 2026

## Investigation Summary

**Date:** January 28, 2026  
**Issue:** Only a few PostHog events from Saturday despite 10+ visits

## Findings

### Database Query Results
- **Intent Sessions (Saturday Jan 24, 2026):** 0
- **Verified Visits (Saturday Jan 24, 2026):** 0

### Root Cause Analysis

#### 1. Anonymous Visits Don't Create Intent Sessions
Looking at `/backend/app/routers/intent.py` line 104:
```python
# Create intent session only for authenticated users
if current_user:
    session = await create_intent_session(...)
```

**Impact:** Anonymous users (not logged in) don't create `intent_sessions` records, but they should still trigger:
- Frontend PostHog events (`driver.session.start`)
- Backend PostHog events (`server.driver.intent.capture.success` with `distinct_id="anonymous"`)

#### 2. Frontend PostHog Event Flow

**Initialization (`apps/driver/src/analytics/index.ts`):**
- PostHog initializes in `main.tsx` BEFORE consent check
- If `VITE_POSTHOG_KEY` is missing or `VITE_ANALYTICS_ENABLED=false`, PostHog won't initialize
- `capture()` function checks `if (!isInitialized)` and returns early if not initialized

**Consent Check:**
- Consent banner shows AFTER PostHog init
- `capture()` does NOT check consent - it only checks if initialized
- However, if PostHog key is missing, events won't be sent

#### 3. Backend PostHog Event Flow

**Configuration (`backend/app/services/analytics.py`):**
- Checks `ANALYTICS_ENABLED` (defaults to "true")
- Requires `POSTHOG_KEY` or `POSTHOG_API_KEY` environment variable
- If key missing, logs warning and disables analytics

**Event Capture:**
- Backend sends events for both authenticated and anonymous users
- Anonymous users get `distinct_id="anonymous"`
- Events are non-blocking (errors don't crash requests)

## Likely Causes

### 1. Frontend PostHog Key Missing (Most Likely)
**Symptom:** Frontend events (`driver.session.start`) not appearing in PostHog

**Check:**
```bash
# Check if VITE_POSTHOG_KEY is set in production build
grep -r "VITE_POSTHOG_KEY" apps/driver/.env*
# Or check deployment environment variables
```

**Fix:** Ensure `VITE_POSTHOG_KEY` is set during frontend build/deployment

### 2. Analytics Consent Denied
**Symptom:** Users declined consent banner, but this shouldn't block events (consent check is only for `identify()`)

**Note:** `capture()` doesn't check consent, so this is unlikely the issue

### 3. Backend PostHog Key Missing
**Symptom:** Backend events (`server.driver.intent.capture.success`) not appearing

**Check:**
```bash
# Check backend environment variables
aws apprunner describe-service --service-arn <arn> | grep POSTHOG
```

### 4. PostHog API Errors
**Symptom:** Events sent but PostHog API rejected them

**Check:** Backend logs for PostHog errors:
```bash
# Check for PostHog errors in logs
grep -i "posthog\|analytics" backend/logs/*.log | grep -i error
```

### 5. Date/Time Filtering Issue
**Symptom:** Events exist but filtered out in PostHog UI

**Check:** PostHog filter settings:
- Date range filter
- "Filter out internal and test users" toggle
- Event name filters

## Recommended Actions

### Immediate Checks

1. **Verify Frontend PostHog Key:**
   ```bash
   # Check production build environment
   # Ensure VITE_POSTHOG_KEY is set during build
   ```

2. **Verify Backend PostHog Key:**
   ```bash
   # Check App Runner environment variables
   aws apprunner describe-service --service-arn <arn>
   ```

3. **Check PostHog Dashboard Filters:**
   - Verify date range includes Saturday Jan 24
   - Check if "Filter out internal and test users" is enabled
   - Verify event name filters aren't excluding events

4. **Review Backend Logs:**
   ```bash
   # Check for PostHog initialization and errors
   aws logs tail /aws/apprunner/nerava-backend --since 2026-01-24 --filter-pattern "posthog|analytics"
   ```

### Code Changes Needed

1. **Add Consent Check to Frontend Capture (Optional):**
   Currently `capture()` doesn't check consent. If we want to respect consent:
   ```typescript
   export function capture(eventName: string, properties?: Record<string, unknown>): void {
     if (!isInitialized) {
       return
     }
     
     // Check consent before capturing
     const consent = localStorage.getItem('consent_analytics')
     if (consent === 'denied') {
       return
     }
     
     // ... rest of capture logic
   }
   ```

2. **Add Logging for PostHog Initialization:**
   Add more detailed logging when PostHog fails to initialize:
   ```typescript
   if (!analyticsEnabled || !posthogKey) {
     console.warn('[Analytics] PostHog not initialized:', {
       analyticsEnabled,
       hasKey: !!posthogKey,
       env: import.meta.env.MODE
     })
     return
   }
   ```

3. **Track Anonymous Intent Sessions:**
   Consider creating `intent_sessions` for anonymous users to track visits:
   ```python
   # In intent.py, create session for anonymous users too
   if current_user:
       session = await create_intent_session(...)
   else:
       # Create anonymous session for tracking
       session = await create_intent_session(
           db=db,
           user_id=None,  # Or use a system user
           ...
       )
   ```

## Next Steps

1. ✅ Check frontend PostHog key configuration
2. ✅ Check backend PostHog key configuration  
3. ✅ Review PostHog dashboard filters
4. ✅ Check backend logs for PostHog errors
5. ✅ Verify PostHog API is accessible from production

## Related Files

- Frontend Analytics: `apps/driver/src/analytics/index.ts`
- Backend Analytics: `backend/app/services/analytics.py`
- Intent Capture: `backend/app/routers/intent.py`
- Consent Banner: `apps/driver/src/components/ConsentBanner.tsx`
