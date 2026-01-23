# Quick Integration Guide: nerava-ui → nerava-backend-v9

**Goal:** Get real users in production this week  
**Time Estimate:** 4-6 hours for basic integration

---

## 🚨 Critical Blockers (Fix First)

### 1. Remove Mock Mode (5 min)

**File:** `nerava-ui/src/services/api.ts`

**Change:**
```typescript
// BEFORE (line 19-22):
function isMockMode(): boolean {
  // Always use mock mode for Figma visual parity
  // TODO: Wire to backend when ready
  return true
}

// AFTER:
function isMockMode(): boolean {
  // Check environment variable
  return import.meta.env.VITE_UI_MODE === 'figma_mock'
}
```

**Test:** Set `VITE_UI_MODE=production` in `.env.local` and verify API calls go to backend.

---

### 2. Wire OTP Authentication (30 min)

**File:** `nerava-ui/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx`

**Add API_BASE_URL constant:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
```

**Update `handleSendCode`:**
```typescript
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
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to send OTP' }))
      throw new Error(error.detail || 'Failed to send OTP')
    }
    
    setStep('code')
    setError('')
    setResendTimer(30)
    setCanResend(false)
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to send code. Please try again.')
  }
}
```

**Update `handleVerifyCode`:**
```typescript
const handleVerifyCode = async (code?: string) => {
  const codeToVerify = code || otp.join('')
  
  if (codeToVerify.length !== 6) {
    setError('Please enter the complete 6-digit code')
    return
  }

  const cleaned = phoneNumber.replace(/\D/g, '')
  
  try {
    const response = await fetch(`${API_BASE_URL}/v1/auth/otp/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: `+1${cleaned}`, code: codeToVerify })
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Invalid code' }))
      throw new Error(error.detail || 'Invalid code')
    }
    
    const data = await response.json()
    
    // Store tokens
    localStorage.setItem('access_token', data.access_token)
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token)
    }
    
    // Store auth state
    localStorage.setItem('neravaAuth', JSON.stringify({
      phone: phoneNumber,
      authenticated: true,
      timestamp: Date.now()
    }))

    onSuccess()
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Incorrect code. Please try again.')
    setOtp(['', '', '', '', '', ''])
    inputRefs.current[0]?.focus()
  }
}
```

**Update `handleResend`:**
```typescript
const handleResend = async () => {
  if (!canResend) return
  
  const cleaned = phoneNumber.replace(/\D/g, '')
  
  try {
    const response = await fetch(`${API_BASE_URL}/v1/auth/otp/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: `+1${cleaned}` })
    })
    
    if (!response.ok) throw new Error('Failed to resend OTP')
    
    setCanResend(false)
    setResendTimer(30)
    setError('')
    setOtp(['', '', '', '', '', ''])
    inputRefs.current[0]?.focus()
  } catch (err) {
    setError('Failed to resend code. Please try again.')
  }
}
```

---

### 3. Wire Intent Capture (45 min)

**File:** `nerava-ui/src/components/DriverHome/DriverHome.tsx`

**Add imports:**
```typescript
import { useGeolocation } from '../../hooks/useGeolocation'
import { useIntentCapture } from '../../services/api'
```

**Add intent capture logic:**
```typescript
export function DriverHome() {
  // ... existing state ...
  
  // Get geolocation
  const { lat, lng, accuracy, loading: geoLoading, error: geoError } = useGeolocation()
  
  // Capture intent when location is available
  const intentRequest = lat && lng ? {
    lat,
    lng,
    accuracy_m: accuracy || undefined,
    client_ts: new Date().toISOString()
  } : null
  
  const intentQuery = useIntentCapture(intentRequest)
  const [sessionId, setSessionId] = useState<string | null>(null)
  
  // Store session_id when intent is captured
  useEffect(() => {
    if (intentQuery.data?.session_id) {
      setSessionId(intentQuery.data.session_id)
    }
  }, [intentQuery.data])
  
  // Use merchants from intent capture instead of mock data
  const merchantsFromIntent = intentQuery.data?.merchants || []
  
  // ... rest of component ...
}
```

**Update merchant carousel to use real data:**
```typescript
// Replace mockMerchants with merchantsFromIntent
// Transform MerchantSummary to MockMerchant format if needed
```

**Handle confidence tiers:**
```typescript
useEffect(() => {
  if (intentQuery.data) {
    if (intentQuery.data.confidence_tier === 'C') {
      // Show fallback message
      console.log('Fallback:', intentQuery.data.fallback_message)
    }
  }
}, [intentQuery.data])
```

---

### 4. Pass Session ID to Merchant Details (10 min)

**File:** `nerava-ui/src/components/MerchantDetail/MerchantDetailModal.tsx`

**Update to accept and use sessionId:**
```typescript
interface MerchantDetailModalProps {
  // ... existing props ...
  sessionId?: string | null
}

// In component:
const { data: merchantData } = useMerchantDetails(
  merchant?.id || null,
  sessionId || undefined
)
```

**File:** `nerava-ui/src/components/DriverHome/DriverHome.tsx`

**Pass sessionId:**
```typescript
<MerchantDetailModal
  // ... existing props ...
  sessionId={sessionId}
/>
```

---

### 5. Update API Service to Handle Errors (15 min)

**File:** `nerava-ui/src/services/api.ts`

**Add token refresh logic:**
```typescript
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  let token = localStorage.getItem('access_token')
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options?.headers,
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    // Handle 401 - try to refresh token
    if (response.status === 401 && token) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        // Try to refresh
        const refreshResponse = await fetch(`${API_BASE_URL}/v1/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken })
        })
        
        if (refreshResponse.ok) {
          const refreshData = await refreshResponse.json()
          localStorage.setItem('access_token', refreshData.access_token)
          if (refreshData.refresh_token) {
            localStorage.setItem('refresh_token', refreshData.refresh_token)
          }
          
          // Retry original request
          headers['Authorization'] = `Bearer ${refreshData.access_token}`
          const retryResponse = await fetch(url, {
            ...options,
            headers,
          })
          
          if (!retryResponse.ok) {
            // Refresh failed, clear tokens
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            throw new ApiError(retryResponse.status, 'unauthorized', 'Please sign in again')
          }
          
          return await retryResponse.json()
        } else {
          // Refresh failed, clear tokens
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          throw new ApiError(401, 'unauthorized', 'Please sign in again')
        }
      }
    }
    
    if (!response.ok) {
      // ... existing error handling ...
    }

    return await response.json()
  } catch (error) {
    // ... existing error handling ...
  }
}
```

---

## 🧪 Testing Checklist

### Local Testing
- [ ] Start backend: `cd nerava-backend-v9 && python -m uvicorn app.main:app --reload`
- [ ] Start frontend: `cd nerava-ui && npm run dev`
- [ ] Set `.env.local`: `VITE_API_BASE_URL=http://localhost:8001`
- [ ] Test OTP flow with real phone number
- [ ] Test intent capture (requires geolocation permission)
- [ ] Test merchant details page
- [ ] Test wallet activation

### Production Testing
- [ ] Update `VITE_API_BASE_URL` to production backend URL
- [ ] Verify CORS allows frontend origin
- [ ] Test OTP with production SMS provider
- [ ] Test geolocation on HTTPS (required for production)
- [ ] Monitor error logs

---

## 🚀 Deployment Steps

1. **Build frontend:**
   ```bash
   cd nerava-ui
   npm run build
   ```

2. **Deploy frontend** (Vercel/Netlify/etc.)

3. **Update backend CORS** to include frontend URL:
   ```python
   # nerava-backend-v9/app/main.py
   cors_origins = [
       # ... existing ...
       "https://your-frontend-domain.com",
   ]
   ```

4. **Set environment variables:**
   - Frontend: `VITE_API_BASE_URL=https://your-backend-domain.com`
   - Backend: Ensure OTP service (Twilio) is configured

5. **Test end-to-end** in production

---

## 🐛 Common Issues & Fixes

### Issue: CORS errors
**Fix:** Add frontend URL to backend CORS allowlist

### Issue: 401 Unauthorized
**Fix:** Check that `access_token` is stored and sent in Authorization header

### Issue: OTP not sending
**Fix:** Verify backend OTP service (Twilio) is configured with API keys

### Issue: Geolocation fails
**Fix:** Requires HTTPS in production. Handle permission denied gracefully.

### Issue: Intent capture returns empty merchants
**Fix:** Check backend has Google Places API configured and chargers in database

---

## 📞 Support

If you encounter issues:
1. Check browser console for errors
2. Check backend logs for API errors
3. Verify environment variables are set correctly
4. Test API endpoints directly with curl/Postman

---

## ✅ Success Criteria

You're ready for production when:
- ✅ OTP authentication works end-to-end
- ✅ Intent capture populates merchant carousel
- ✅ Merchant details page loads with real data
- ✅ Wallet activation works
- ✅ No console errors
- ✅ Tested with real phone numbers and locations




