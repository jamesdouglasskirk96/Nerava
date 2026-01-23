# Gap Analysis: nerava-ui ↔ nerava-backend-v9 Integration

**Target:** Production-ready integration for real users this week  
**Date:** 2025-01-27

## Executive Summary

The frontend (`nerava-ui`) is currently in **mock mode** and needs to be wired to the backend (`nerava-backend-v9`). The backend APIs exist and match the frontend's expectations, but the integration is incomplete. Critical gaps include authentication flow, intent capture integration, and removing mock mode.

---

## ✅ What's Already Working

### Backend APIs (All Exist)
1. ✅ `POST /v1/intent/capture` - Intent capture endpoint
2. ✅ `GET /v1/merchants/{merchant_id}` - Merchant details endpoint  
3. ✅ `POST /v1/wallet/pass/activate` - Wallet activation endpoint
4. ✅ `POST /v1/auth/otp/start` - OTP initiation
5. ✅ `POST /v1/auth/otp/verify` - OTP verification (returns token)

### Frontend Structure
- ✅ API service layer (`src/services/api.ts`) with proper error handling
- ✅ Type definitions match backend schemas
- ✅ React Query hooks for data fetching
- ✅ Environment variable support (`VITE_API_BASE_URL`)

---

## 🔴 Critical Gaps (P0 - Block Production)

### 1. **Mock Mode is Hardcoded ON**
**Location:** `nerava-ui/src/services/api.ts:19-22`

```typescript
function isMockMode(): boolean {
  // Always use mock mode for Figma visual parity
  // TODO: Wire to backend when ready
  return true  // ❌ BLOCKER
}
```

**Impact:** All API calls use mock data, backend never called  
**Fix:** Remove mock mode or make it configurable via env var

---

### 2. **OTP Authentication Flow is Mocked**
**Location:** `nerava-ui/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx`

**Current State:**
- Phone number entry ✅
- OTP input UI ✅  
- **OTP verification is mocked** (accepts any 6 digits) ❌
- No API calls to `/v1/auth/otp/start` or `/v1/auth/otp/verify`

**Backend Endpoints Available:**
- `POST /v1/auth/otp/start` - Sends OTP to phone
- `POST /v1/auth/otp/verify` - Verifies OTP, returns `TokenResponse`

**Required Changes:**
1. Call `/v1/auth/otp/start` when user submits phone number
2. Call `/v1/auth/otp/verify` when user submits OTP code
3. Store `access_token` from response in `localStorage` (currently stores mock data)
4. Handle API errors (invalid phone, wrong code, rate limiting)

---

### 3. **Intent Capture Never Called**
**Location:** `nerava-ui/src/components/DriverHome/DriverHome.tsx`

**Current State:**
- Uses mock merchant/charger data from `mockMerchants.ts` and `mockChargers.ts`
- `useIntentCapture` hook exists but is **never called**
- Geolocation hook exists (`useGeolocation`) but not integrated

**Required Flow:**
1. On app load, get user's geolocation
2. Call `POST /v1/intent/capture` with lat/lng
3. Use response to populate merchant carousel
4. Handle confidence tiers (A/B/C) and fallback messages

**Backend Expects:**
```typescript
POST /v1/intent/capture
{
  lat: number,
  lng: number,
  accuracy_m?: number,
  client_ts?: string
}
```

**Backend Returns:**
```typescript
{
  session_id: string,
  confidence_tier: "A" | "B" | "C",
  charger_summary?: ChargerSummary,
  merchants: MerchantSummary[],
  fallback_message?: string,
  next_actions: NextActions
}
```

---

### 4. **Authentication Token Not Sent**
**Location:** `nerava-ui/src/services/api.ts:56-65`

**Current State:**
- Reads `access_token` from localStorage ✅
- Adds to Authorization header ✅
- **But token is never set** because OTP flow is mocked ❌

**Impact:** All authenticated API calls will fail with 401

---

### 5. **Pre-Charging Screen Uses Mock Data**
**Location:** `nerava-ui/src/components/PreCharging/PreChargingScreen.tsx`

**Current State:**
- Uses `getAllMockChargers()` - no backend integration
- Should use charger data from intent capture response

**Fix:** Use `charger_summary` from intent capture response

---

## 🟡 Important Gaps (P1 - Needed for Good UX)

### 6. **No Token Refresh Logic**
**Backend Provides:** `POST /v1/auth/refresh` endpoint  
**Frontend:** No refresh token handling

**Required:**
- Store `refresh_token` alongside `access_token`
- Implement token refresh on 401 errors
- Handle token expiration gracefully

---

### 7. **No Error Handling for Auth Failures**
**Current:** Basic error display, no retry logic  
**Needed:**
- Handle 401 errors → redirect to login/OTP flow
- Handle 403 errors → show appropriate message
- Network errors → retry logic or offline mode

---

### 8. **Session ID Not Persisted**
**Current:** `session_id` from intent capture is not stored  
**Needed:** Store session_id for merchant details and wallet activation

**Fix:** Store in component state or localStorage, pass to merchant details API

---

### 9. **Geolocation Error Handling**
**Location:** `nerava-ui/src/hooks/useGeolocation.ts`

**Current:** Basic error state  
**Needed:**
- User-friendly error messages
- Retry mechanism
- Fallback to manual location entry (if needed)

---

## 🟢 Nice-to-Have (P2 - Polish)

### 10. **CORS Configuration**
**Backend:** `nerava-backend-v9/app/main.py:87-104`

**Current:** Allows localhost origins  
**Needed:** Add production frontend origin when deploying

**Check:** Ensure production frontend URL is in `cors_origins` list

---

### 11. **Loading States**
**Current:** Basic loading states exist  
**Enhancement:** Skeleton loaders, better UX during API calls

---

### 12. **Analytics/Telemetry**
**Backend:** `POST /v1/telemetry/*` endpoints exist  
**Frontend:** No telemetry calls

**Optional:** Add client-side telemetry for user actions

---

## 📋 Implementation Checklist

### Phase 1: Authentication (P0)
- [ ] Remove hardcoded `isMockMode() = true`
- [ ] Wire OTP start API call (`/v1/auth/otp/start`)
- [ ] Wire OTP verify API call (`/v1/auth/otp/verify`)
- [ ] Store `access_token` and `refresh_token` in localStorage
- [ ] Update `ActivateExclusiveModal` to use real APIs
- [ ] Handle OTP errors (invalid phone, wrong code, rate limits)

### Phase 2: Intent Capture (P0)
- [ ] Integrate `useGeolocation` with `useIntentCapture`
- [ ] Call intent capture on app load (or when geolocation available)
- [ ] Use intent capture response to populate merchant carousel
- [ ] Handle confidence tiers (A/B/C) and fallback messages
- [ ] Store `session_id` from response
- [ ] Update PreCharging screen to use charger data from intent capture

### Phase 3: API Integration (P0)
- [ ] Ensure all API calls include Authorization header
- [ ] Wire merchant details API with session_id
- [ ] Wire wallet activation API
- [ ] Test end-to-end flow: geolocation → intent → merchant → wallet activation

### Phase 4: Error Handling (P1)
- [ ] Implement token refresh on 401 errors
- [ ] Handle auth failures gracefully
- [ ] Add retry logic for network errors
- [ ] Improve geolocation error handling

### Phase 5: Production Readiness (P1)
- [ ] Update CORS configuration for production
- [ ] Add environment variable documentation
- [ ] Test with real backend (not localhost)
- [ ] Verify all API endpoints work end-to-end

---

## 🔧 Quick Start: Minimal Integration

To get basic functionality working **today**:

1. **Disable Mock Mode:**
   ```typescript
   // nerava-ui/src/services/api.ts
   function isMockMode(): boolean {
     return import.meta.env.VITE_UI_MODE === 'figma_mock'
   }
   ```

2. **Wire OTP Flow:**
   ```typescript
   // In ActivateExclusiveModal.tsx
   const handleSendCode = async () => {
     const cleaned = phoneNumber.replace(/\D/g, '')
     if (cleaned.length !== 10) {
       setError('Please enter a valid 10-digit phone number')
       return
     }
     
     try {
       const response = await fetch(`${API_BASE_URL}/v1/auth/otp/start`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ phone: `+1${cleaned}` })
       })
       if (!response.ok) throw new Error('Failed to send OTP')
       setStep('code')
     } catch (err) {
       setError('Failed to send code. Please try again.')
     }
   }
   
   const handleVerifyCode = async (code: string) => {
     const cleaned = phoneNumber.replace(/\D/g, '')
     try {
       const response = await fetch(`${API_BASE_URL}/v1/auth/otp/verify`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ phone: `+1${cleaned}`, code })
       })
       if (!response.ok) throw new Error('Invalid code')
       const data = await response.json()
       localStorage.setItem('access_token', data.access_token)
       if (data.refresh_token) {
         localStorage.setItem('refresh_token', data.refresh_token)
       }
       onSuccess()
     } catch (err) {
       setError('Incorrect code. Please try again.')
     }
   }
   ```

3. **Wire Intent Capture:**
   ```typescript
   // In DriverHome.tsx
   const { lat, lng, accuracy, loading: geoLoading } = useGeolocation()
   const intentQuery = useIntentCapture(
     lat && lng ? { lat, lng, accuracy_m: accuracy || undefined } : null
   )
   
   useEffect(() => {
     if (intentQuery.data) {
       // Use intentQuery.data.merchants to populate carousel
       // Store intentQuery.data.session_id
     }
   }, [intentQuery.data])
   ```

---

## 🚨 Production Deployment Considerations

1. **Environment Variables:**
   - `VITE_API_BASE_URL` - Backend API URL (production)
   - `VITE_UI_MODE` - Set to `production` (not `figma_mock`)

2. **CORS:**
   - Ensure frontend production URL is in backend CORS allowlist
   - Backend: `app/main.py:87-104`

3. **Authentication:**
   - Backend requires Bearer token for all `/v1/*` endpoints
   - Ensure OTP service is configured (Twilio/SMS provider)
   - Test OTP flow end-to-end

4. **Geolocation:**
   - Requires HTTPS in production (browser security)
   - Handle permission denied gracefully
   - Consider fallback for users who deny location

5. **Error Monitoring:**
   - Add error tracking (Sentry, etc.)
   - Monitor API error rates
   - Set up alerts for auth failures

---

## 📊 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Mock mode still enabled | 🔴 Critical | Remove immediately |
| OTP flow broken | 🔴 Critical | Test with real phone numbers |
| Geolocation fails | 🟡 High | Add fallback/retry |
| Token expiration | 🟡 High | Implement refresh logic |
| CORS issues | 🟡 High | Test in staging first |
| API rate limits | 🟢 Medium | Monitor and handle 429 errors |

---

## 🎯 Success Criteria

✅ **Production Ready When:**
1. Mock mode disabled
2. OTP authentication works end-to-end
3. Intent capture called on app load
4. Merchant carousel populated from API
5. Wallet activation works
6. All API calls authenticated
7. Error handling in place
8. Tested with real backend

---

## 📝 Notes

- Backend APIs are well-structured and match frontend expectations
- Main blocker is mock mode being hardcoded ON
- OTP flow UI is complete, just needs API integration
- Intent capture hook exists but is never called
- Estimated time to basic integration: **4-6 hours**
- Estimated time to production-ready: **1-2 days**




