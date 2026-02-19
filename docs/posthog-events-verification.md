# PostHog Events Verification Report

## Status: ⚠️ API Key Authentication Issue

**Date:** January 29, 2026  
**Issue:** PostHog API is returning 401 "API key is not valid: personal_api_key"

---

## Events Attempted to Send

Three geofence test events were attempted:

1. ✅ **ios.geofence.charger.entered**
   - Distinct ID: `driver:test_driver_geofence_demo`
   - Location: `lat: 30.4037865, lng: -97.6730044`
   - Status: Sent (but API returned 401)

2. ✅ **ios.geofence.merchant.entered**
   - Distinct ID: `driver:test_driver_geofence_demo`
   - Location: `lat: 30.4028469, lng: -97.6718938`
   - Status: Sent (but API returned 401)

3. ✅ **ios.geofence.merchant.exited**
   - Distinct ID: `driver:test_driver_geofence_demo`
   - Location: `lat: 30.4037969, lng: -97.6709438`
   - Status: Sent (but API returned 401)

---

## Verification Results

### ✅ Code Execution
- Script ran successfully
- All 3 events were formatted correctly
- PostHog client initialized
- Events were passed to PostHog Python library

### ❌ API Response
- **Status:** 401 Unauthorized
- **Error:** "API key is not valid: personal_api_key"
- **Endpoint Tested:** `https://app.posthog.com/batch/`
- **Key Format:** `phx_kOolEppUR3mbcT7MbsVdWfWMUty7KCnIRcKdJ1KjaMhKO5b` (starts with `phx_`)

---

## Possible Issues

### 1. Invalid API Key
The API key might be:
- Expired
- Revoked
- From a different PostHog project
- Incorrectly copied

### 2. Wrong Key Type
PostHog has two types of keys:
- **Project API Key** (`phx_*`): For sending events (what we're using)
- **Personal API Key**: For querying data (different format)

The error message mentioning "personal_api_key" is confusing since we're using a project key.

### 3. PostHog Host Mismatch
The key might be for a different PostHog instance:
- `https://app.posthog.com` (US)
- `https://eu.posthog.com` (EU)
- Self-hosted instance

---

## Verification Methods

### Method 1: Check PostHog Dashboard ✅ (Recommended)
1. Go to https://app.posthog.com
2. Navigate to **Activity** → **Events**
3. Filter by:
   - **distinct_id:** `driver:test_driver_geofence_demo`
   - **Event name:** `ios.geofence.*`
4. Check time range: **Last 24 hours** or **Last hour**
5. Click **Reload** button to refresh

**If events appear:** ✅ Events were received successfully  
**If events don't appear:** ❌ Events were rejected (likely due to API key issue)

### Method 2: Verify API Key in PostHog
1. Log into PostHog dashboard
2. Go to **Project Settings** → **Project API Key**
3. Verify the key matches: `phx_kOolEppUR3mbcT7MbsVdWfWMUty7KCnIRcKdJ1KjaMhKO5b`
4. Check if key is active/enabled
5. Verify you're in the correct project

### Method 3: Test with New Event
Run this command to send a fresh test event:

```bash
cd /Users/jameskirk/Desktop/Nerava
export POSTHOG_KEY=phx_kOolEppUR3mbcT7MbsVdWfWMUty7KCnIRcKdJ1KjaMhKO5b
python3 scripts/create_geofence_test_events.py
```

Then immediately check PostHog dashboard (events appear within 30-60 seconds).

### Method 4: Check PostHog Instance
Verify you're using the correct PostHog host:
- If your PostHog is EU-hosted, use: `https://eu.posthog.com`
- If self-hosted, use your custom domain
- Current setting: `https://app.posthog.com` (US)

---

## Next Steps

### Immediate Actions
1. ✅ **Check PostHog Dashboard** - Most reliable verification method
2. ✅ **Verify API Key** - Confirm key is correct in PostHog settings
3. ✅ **Check Project** - Ensure you're in the right PostHog project

### If Events Don't Appear
1. **Get Fresh API Key:**
   - PostHog → Project Settings → Project API Key
   - Copy the key (starts with `phx_`)
   - Update `backend/.env`: `POSTHOG_KEY=new_key_here`

2. **Verify PostHog Host:**
   - Check if you're using EU instance
   - Update `backend/.env`: `POSTHOG_HOST=https://eu.posthog.com` (if EU)

3. **Test Again:**
   ```bash
   python3 scripts/create_geofence_test_events.py
   ```

---

## Event Details (For Reference)

All events include:
- ✅ Geo coordinates (`lat`, `lng`, `accuracy_m`)
- ✅ Charger/Merchant IDs
- ✅ Distance information
- ✅ Test markers (`test_event: true`)

**Distinct ID:** `driver:test_driver_geofence_demo`

---

## Conclusion

**Most Likely Status:** Events were **not received** due to API key authentication failure (401).

**Recommended Action:** 
1. Verify API key in PostHog dashboard
2. Check PostHog dashboard for events (they may have been received despite the error)
3. If not present, get a fresh API key and retry

The PostHog Python library doesn't raise exceptions for API errors - it logs them silently. The 401 error suggests authentication failed, but it's possible some events got through before the error occurred.
