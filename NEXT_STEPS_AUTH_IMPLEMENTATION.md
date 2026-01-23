# Next Steps: Production Auth Implementation

## Status Overview

✅ **Backend Core Implementation**: Complete  
⏳ **Backend Integration**: Needs testing with real credentials  
⏳ **Frontend Updates**: Not started  
⏳ **Production Deployment**: Pending

---

## What's Currently Mocked/Stubbed

### 1. OTP Provider (Currently: `stub`)
**Location**: `backend/app/core/config.py` → `OTP_PROVIDER=stub`

**Current Behavior**:
- Accepts code `000000` for any phone number (or allowlisted phones if `OTP_DEV_ALLOWLIST` is set)
- No actual SMS sent
- Logs code to console: `[OTP][Stub] Code for +14155551234: 000000`

**To Enable Production**:
- Set `OTP_PROVIDER=twilio_verify` (recommended) or `OTP_PROVIDER=twilio_sms`
- Configure Twilio credentials (see API Keys section)

### 2. Google Business Profile Access Check (Currently: Mock Mode)
**Location**: `backend/app/routers/auth_domain.py` → `MOCK_GBP_MODE` env var

**Current Behavior**:
- If `MOCK_GBP_MODE=true`: Accepts any Google ID token, skips GBP API check
- Creates mock merchant user with email `merchant-{place_id}@example.com`

**To Enable Production**:
- Set `MOCK_GBP_MODE=false` (or remove env var)
- Set `GOOGLE_GBP_REQUIRED=true`
- Ensure Google OAuth includes `business.manage` scope
- User must have access to at least one GBP location

### 3. Google OAuth Access Token (Currently: Not Used)
**Location**: `backend/app/services/auth/google_oauth.py`

**Current Behavior**:
- Only verifies ID token (from frontend Google Sign-In)
- Does NOT use OAuth code exchange flow
- GBP access check is skipped if `access_token` is None

**Note**: The current implementation uses Google Identity Services (GIS) on frontend, which provides ID tokens directly. For full GBP API access, you may need to implement OAuth code exchange flow.

---

## Required API Keys & Configuration

### Twilio (For OTP)

#### Option A: Twilio Verify (Recommended)
```bash
# Required
OTP_PROVIDER=twilio_verify
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional (for dev/staging)
OTP_DEV_ALLOWLIST=+14155551234,+14155555678  # Comma-separated
```

**Setup Steps**:
1. Sign up at https://www.twilio.com/
2. Get Account SID and Auth Token from Twilio Console dashboard
3. Create Verify Service:
   - Go to Verify > Services in Twilio Console
   - Click "Create new Verify Service"
   - Copy the Service SID (starts with `VA`)
4. Add to `.env` file or environment variables

#### Option B: Direct SMS (Fallback)
```bash
# Required
OTP_PROVIDER=twilio_sms
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
OTP_FROM_NUMBER=+14155551234  # Your Twilio phone number (E.164 format)
```

**Setup Steps**:
1. Get Account SID and Auth Token (same as above)
2. Purchase a phone number in Twilio Console
3. Copy phone number in E.164 format (e.g., `+14155551234`)

### Google OAuth (For Merchant SSO)

```bash
# Required
GOOGLE_OAUTH_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_REDIRECT_URI=https://yourdomain.com/merchant/auth/google/callback

# Optional (only if using code exchange flow)
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret

# Configuration
GOOGLE_GBP_REQUIRED=true  # Set to false to skip GBP access check
MOCK_GBP_MODE=false  # Set to true to skip GBP API calls (dev only)
```

**Setup Steps**:
1. Go to https://console.cloud.google.com/
2. Create project or select existing
3. Enable APIs:
   - Google Identity Services API
   - Google Business Profile API (formerly My Business API)
4. Create OAuth 2.0 Credentials:
   - APIs & Services > Credentials > Create Credentials > OAuth client ID
   - Application type: Web application
   - Authorized JavaScript origins:
     - `http://localhost:8001` (dev)
     - `https://staging.yourdomain.com` (staging)
     - `https://yourdomain.com` (prod)
   - Authorized redirect URIs:
     - `http://localhost:8001/merchant/auth/google/callback` (dev)
     - `https://staging.yourdomain.com/merchant/auth/google/callback` (staging)
     - `https://yourdomain.com/merchant/auth/google/callback` (prod)
   - Scopes: Add `https://www.googleapis.com/auth/business.manage`
5. Copy Client ID and Client Secret

### PostHog (For Analytics)

```bash
# Required (if analytics enabled)
ANALYTICS_ENABLED=true
POSTHOG_KEY=phc_your_project_api_key_here
POSTHOG_HOST=https://app.posthog.com  # or your self-hosted instance
```

**Setup Steps**:
1. Sign up at https://posthog.com/ or use self-hosted instance
2. Get Project API Key from PostHog dashboard
3. Add to environment variables

### Environment Configuration

```bash
# Required
ENV=prod  # or dev, staging

# Optional
ANALYTICS_ENABLED=true
POSTHOG_KEY=...
POSTHOG_HOST=https://app.posthog.com
```

---

## Next Steps Checklist

### Phase 1: Backend Testing (Priority: High)

- [ ] **Configure Twilio Verify**
  - [ ] Create Twilio account
  - [ ] Create Verify Service
  - [ ] Add credentials to `.env`
  - [ ] Set `OTP_PROVIDER=twilio_verify`
  - [ ] Test OTP send with real phone number
  - [ ] Test OTP verify with received code
  - [ ] Verify rate limiting works (try 4+ requests)
  - [ ] Verify lockout works (6+ failed attempts)

- [ ] **Configure Google OAuth**
  - [ ] Create Google Cloud project
  - [ ] Enable required APIs
  - [ ] Create OAuth credentials
  - [ ] Add redirect URIs for all environments
  - [ ] Add credentials to `.env`
  - [ ] Test Google SSO login
  - [ ] Verify GBP access check (if `GOOGLE_GBP_REQUIRED=true`)

- [ ] **Test Production Safety**
  - [ ] Set `ENV=prod`
  - [ ] Verify startup fails if `OTP_PROVIDER=stub`
  - [ ] Verify startup fails if Twilio credentials missing
  - [ ] Verify startup fails if Google OAuth missing (if merchant SSO enabled)

- [ ] **Test Rate Limiting**
  - [ ] Send 3 OTP start requests → 4th should be rate limited
  - [ ] Send 6 OTP verify attempts with wrong code → 7th should lockout
  - [ ] Verify cooldown after successful verify (30s)

- [ ] **Test Audit Logging**
  - [ ] Check logs for structured audit events
  - [ ] Verify no full phone numbers or codes in logs
  - [ ] Verify request_id is included

- [ ] **Test PostHog Events**
  - [ ] Verify `server.driver.otp.start` events appear
  - [ ] Verify `server.driver.otp.verify.success` events appear
  - [ ] Verify `server.merchant.sso.login.success` events appear

### Phase 2: Frontend Updates (Priority: High)

#### Driver App (`apps/driver`)

- [ ] **OTP UI Improvements**
  - [ ] Add resend cooldown timer (30s countdown)
    - Location: `apps/driver/src/components/` (find OTP input component)
    - Show "Resend code in X seconds" message
    - Disable resend button during cooldown
  - [ ] Show generic error messages
    - Replace technical errors with: "Unable to send code. Try again later."
    - Replace verification errors with: "Invalid code."
  - [ ] Disable submit while request in-flight
    - Show loading state
    - Disable submit button
  - [ ] PostHog client events
    - Add `driver.otp.start` event on OTP request
    - Add `driver.otp.verify.success` event on success
    - Add `driver.otp.verify.fail` event on failure
  - [ ] Verify API base is `/api` in nginx/docker config

#### Merchant Portal (`apps/merchant`)

- [ ] **Google Login Integration**
  - [ ] Add "Sign in with Google" button
    - Location: `apps/merchant/app/components/` (login/auth component)
    - Use Google Identity Services (GIS) or standard OAuth
  - [ ] Complete OAuth flow
    - Handle ID token from Google
    - Send to `/api/v1/auth/merchant/google`
    - Store returned token
  - [ ] User state hydration
    - Call `/api/v1/auth/me` or `/api/v1/merchant/me` on app boot
    - Store user data in app state
  - [ ] PostHog events
    - Add `merchant.login.success` event
    - Add `merchant.login.fail` event

### Phase 3: Role Enforcement (Priority: Medium)

- [ ] **Add Role Checks to Endpoints**
  - [ ] Merchant endpoints: Add `require_role("merchant")` dependency
    - Example: `@router.get("/merchant/dashboard", dependencies=[Depends(require_role("merchant"))])`
  - [ ] Admin endpoints: Add `require_role("admin")` dependency
  - [ ] Driver endpoints: Add `require_role("driver")` dependency (if not already protected)

- [ ] **Update Middleware** (if needed)
  - [ ] Ensure `backend/app/middleware/auth.py` extracts role from token
  - [ ] Verify role is available in `request.state.user_role`

### Phase 4: Production Deployment (Priority: High)

- [ ] **Environment Variables**
  - [ ] Add all required env vars to production environment
  - [ ] Verify secrets are stored securely (not in code)
  - [ ] Set `ENV=prod`

- [ ] **Startup Validation**
  - [ ] Verify startup validation passes
  - [ ] Check logs for config summary (secrets should be redacted)

- [ ] **Monitoring**
  - [ ] Set up alerts for OTP failures
  - [ ] Set up alerts for rate limit violations
  - [ ] Monitor PostHog events for auth issues

- [ ] **Documentation**
  - [ ] Update README with auth setup instructions
  - [ ] Document troubleshooting steps
  - [ ] Create runbook for common issues

---

## Testing Commands

### Test OTP Flow (Stub Mode)
```bash
# Set stub provider
export OTP_PROVIDER=stub
export ENV=dev

# Start backend
cd backend && python -m uvicorn app.main:app --reload

# Test OTP start
curl -X POST http://localhost:8000/v1/auth/otp/start \
  -H "Content-Type: application/json" \
  -d '{"phone": "4155551234"}'

# Test OTP verify (use code 000000)
curl -X POST http://localhost:8000/v1/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone": "4155551234", "code": "000000"}'
```

### Test OTP Flow (Twilio Verify)
```bash
# Set Twilio Verify provider
export OTP_PROVIDER=twilio_verify
export TWILIO_ACCOUNT_SID=AC...
export TWILIO_AUTH_TOKEN=...
export TWILIO_VERIFY_SERVICE_SID=VA...
export ENV=dev

# Test OTP start (will send real SMS)
curl -X POST http://localhost:8000/v1/auth/otp/start \
  -H "Content-Type: application/json" \
  -d '{"phone": "+14155551234"}'

# Test OTP verify (use code from SMS)
curl -X POST http://localhost:8000/v1/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone": "+14155551234", "code": "123456"}'
```

### Test Rate Limiting
```bash
# Send 4 requests rapidly (4th should be rate limited)
for i in {1..4}; do
  curl -X POST http://localhost:8000/v1/auth/otp/start \
    -H "Content-Type: application/json" \
    -d '{"phone": "+14155551234"}'
  echo ""
done
```

### Test Google SSO (Mock Mode)
```bash
# Set mock mode
export MOCK_GBP_MODE=true
export GOOGLE_OAUTH_CLIENT_ID=your_client_id

# Test merchant Google auth (requires valid Google ID token)
curl -X POST http://localhost:8000/v1/auth/merchant/google \
  -H "Content-Type: application/json" \
  -d '{"id_token": "google_id_token_here"}'
```

---

## Common Issues & Solutions

### Issue: "OTP_PROVIDER=stub is not allowed in production"
**Solution**: Set `OTP_PROVIDER=twilio_verify` or `twilio_sms` and configure Twilio credentials

### Issue: "Invalid audience" (Google OAuth)
**Solution**: Ensure `GOOGLE_OAUTH_CLIENT_ID` matches the Client ID used in frontend

### Issue: "Redirect URI mismatch" (Google OAuth)
**Solution**: Add exact redirect URI to Google Cloud Console (check protocol, domain, trailing slashes)

### Issue: "No GBP locations found"
**Solution**: 
- Ensure user has manager access to Google Business Profile location
- Verify `business.manage` scope is included in OAuth consent
- Check that Google Business Profile API is enabled

### Issue: Rate limiting not working
**Solution**: 
- Verify `RateLimitService` is being used (check imports in routes)
- Check that rate limit service is singleton (should reuse same instance)

### Issue: Tokens don't have role claim
**Solution**: 
- Verify `create_access_token()` is called with `role` parameter
- Check token payload: `jwt.decode(token, SECRET_KEY)["role"]`

---

## File Locations Reference

### Backend
- OTP Providers: `backend/app/services/auth/`
- Rate Limiting: `backend/app/services/auth/rate_limit.py`
- Audit Logging: `backend/app/services/auth/audit.py`
- Google OAuth: `backend/app/services/auth/google_oauth.py`
- OTP Routes: `backend/app/routers/auth.py` (lines 347-557)
- Merchant SSO Route: `backend/app/routers/auth_domain.py` (line 430)
- Config: `backend/app/core/config.py`
- Role Dependencies: `backend/app/dependencies/auth.py`

### Frontend (To Be Updated)
- Driver OTP UI: `apps/driver/src/components/` (find login/OTP component)
- Merchant Login: `apps/merchant/app/components/` (find auth component)

### Documentation
- Production Guide: `backend/AUTH_PRODUCTION.md`
- This Document: `NEXT_STEPS_AUTH_IMPLEMENTATION.md`

---

## Success Criteria

✅ OTP works with real phone numbers  
✅ Rate limiting prevents abuse  
✅ Audit logs capture all auth events  
✅ Google SSO works with GBP access check  
✅ Tokens include role claims  
✅ Role enforcement works on protected endpoints  
✅ Frontend shows proper UX (cooldown, errors, loading states)  
✅ PostHog events are sent for all auth flows  
✅ Production startup validation passes  
✅ No sensitive data in logs  

---

## Questions to Resolve

1. **OAuth Flow**: Do we need OAuth code exchange flow, or is ID token-only sufficient?
   - Current: ID token-only (from Google Identity Services)
   - If GBP API requires access token, may need code exchange flow

2. **Merchant User Model**: Do we need separate `MerchantUser` model, or is `User` with `role_flags` sufficient?
   - Current: Uses `User` model with `role_flags="merchant_admin"`
   - May need to link to `merchant_id` if multiple merchants per user

3. **GBP Location Storage**: Should we store GBP location IDs in user record?
   - Current: Not stored, only checked during login
   - May need to store for merchant dashboard features

4. **Frontend Framework**: What framework is used for driver/merchant apps?
   - Need to identify to provide specific implementation guidance

---

## Contact & Support

For issues or questions:
- Check `backend/AUTH_PRODUCTION.md` for detailed setup
- Review audit logs for debugging
- Check PostHog for event tracking
- Verify environment variables are set correctly




