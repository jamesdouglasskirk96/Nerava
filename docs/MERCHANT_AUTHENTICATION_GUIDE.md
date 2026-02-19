# Merchant Portal Authentication Guide

## Current Status

The merchant portal uses **Google OAuth** for authentication. The authentication flow is **partially implemented** - the backend endpoints exist, but the frontend "Continue with Google" button currently just navigates without performing OAuth.

## Authentication Methods

### Method 1: Google OAuth Flow (Recommended)

The backend provides OAuth endpoints:

**Step 1: Start OAuth Flow**
```
GET /v1/merchant/auth/google/start
```

**Step 2: Google Redirects to Callback**
```
GET /v1/merchant/auth/google/callback?code=...
```

**Step 3: Backend Returns Token**
The callback endpoint will redirect with an `access_token` parameter or set a cookie.

### Method 2: Direct Token Authentication (For Testing)

If you have a JWT token from another source, you can manually authenticate:

**In Browser Console (on merchant.nerava.network):**
```javascript
// Set your JWT token
localStorage.setItem('access_token', 'YOUR_JWT_TOKEN_HERE');

// Set merchant ID (if you know it)
localStorage.setItem('merchant_id', 'YOUR_MERCHANT_ID');

// Mark business as claimed
localStorage.setItem('businessClaimed', 'true');

// Refresh the page
window.location.href = '/overview';
```

### Method 3: Admin Preview Mode

Use URL parameters to skip authentication (for admin/testing):

```
https://merchant.nerava.network/?merchant_id=YOUR_MERCHANT_ID&admin_preview=true
```

This will:
- Set `merchant_id` in localStorage
- Mark business as claimed (`businessClaimed = true`)
- Skip the claim flow and show dashboard

### Method 4: Mock Mode (Development Only)

If `MERCHANT_AUTH_MOCK=true` is enabled in backend, you can use mock authentication.

**Backend Endpoint (if mock mode enabled):**
```
POST /v1/auth/merchant/google
Content-Type: application/json

{
  "id_token": "any_value",
  "place_id": "optional_place_id"
}
```

## How Authentication Works

### Token Storage

The merchant portal stores authentication tokens in `localStorage`:

- `access_token` - JWT token for API authentication
- `merchant_id` - Current merchant ID
- `businessClaimed` - Whether business onboarding is complete

### API Calls

All API calls automatically include the token:

```typescript
// From apps/merchant/app/services/api.ts
const token = localStorage.getItem('access_token')
if (token) {
  headers.set('Authorization', `Bearer ${token}`)
}
```

## Quick Start: Manual Authentication

**For immediate testing, use this method:**

1. **Get a token** (one of these methods):
   - From admin panel if you have access
   - From backend logs if you're testing locally
   - Create via API if mock mode is enabled

2. **Open browser console** on merchant portal:
   ```javascript
   // Replace with your actual token
   localStorage.setItem('access_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...');
   localStorage.setItem('businessClaimed', 'true');
   window.location.href = '/overview';
   ```

3. **You should now be authenticated** and see the dashboard

## Current Frontend Implementation

**File:** `apps/merchant/app/components/ClaimBusiness.tsx`

**Current behavior:**
- "Continue with Google" button just navigates to `/claim/location`
- No actual Google OAuth implementation
- No API call to authentication endpoints

**What needs to be implemented:**
1. Integrate Google Sign-In JavaScript SDK or use OAuth redirect flow
2. Handle OAuth callback
3. Store `access_token` in localStorage
4. Navigate to dashboard

## Backend Endpoints

### OAuth Flow Endpoints

- `GET /v1/merchant/auth/google/start` - Initiate OAuth flow
- `GET /v1/merchant/auth/google/callback` - OAuth callback handler

### Direct Auth Endpoint (if enabled)

- `POST /v1/auth/merchant/google` - Direct token exchange (requires `id_token`)

## Troubleshooting

**Issue:** API calls return 401 Unauthorized
- **Solution:** Check if `access_token` exists in localStorage
- **Solution:** Verify token hasn't expired (JWT tokens expire after 24h by default)
- **Solution:** Check browser console for errors

**Issue:** "Business not claimed" - can't access dashboard
- **Solution:** Set `localStorage.setItem('businessClaimed', 'true')`
- **Solution:** Or use admin preview mode: `?admin_preview=true`

**Issue:** Token not being sent in API calls
- **Solution:** Check `apps/merchant/app/services/api.ts` - token should be read from localStorage
- **Solution:** Verify `Authorization` header is being set in network tab

**Issue:** OAuth endpoints return 404 or 410
- **Solution:** Check if Google OAuth is enabled in backend (`ENABLE_GOOGLE_OAUTH=true`)
- **Solution:** Check backend logs for feature flag status

## Testing Checklist

- [ ] Token exists in localStorage (`access_token`)
- [ ] Token is included in API request headers (`Authorization: Bearer ...`)
- [ ] Business is marked as claimed (`businessClaimed = true`)
- [ ] Merchant ID is set (if needed)
- [ ] API calls return 200 (not 401)

## Next Steps

To complete authentication implementation:

1. **Implement OAuth flow in frontend:**
   - Add Google Sign-In button handler
   - Redirect to `/v1/merchant/auth/google/start`
   - Handle callback and store token

2. **Or use manual token method** for development/testing:
   - Get token from backend/admin
   - Set in localStorage
   - Portal will use token for all API calls

3. **Or use admin preview mode** for quick testing:
   - Add `?merchant_id=XXX&admin_preview=true` to URL
   - Portal skips auth and shows dashboard
