# Auth Implementation Status

## Completed Files

### Core Services
- ✅ `backend/app/services/auth/__init__.py` - Package exports
- ✅ `backend/app/services/auth/otp_provider.py` - Abstract provider interface
- ✅ `backend/app/services/auth/twilio_verify.py` - Twilio Verify implementation
- ✅ `backend/app/services/auth/twilio_sms.py` - Direct SMS implementation
- ✅ `backend/app/services/auth/stub_provider.py` - Dev/staging stub provider
- ✅ `backend/app/services/auth/otp_factory.py` - Provider factory
- ✅ `backend/app/services/auth/google_oauth.py` - Google OAuth + GBP service
- ✅ `backend/app/services/auth/tokens.py` - Token creation with roles
- ✅ `backend/app/services/auth/rate_limit.py` - Rate limiting service
- ✅ `backend/app/services/auth/audit.py` - Audit logging service
- ✅ `backend/app/services/otp_service_v2.py` - Production-ready OTP service wrapper
- ✅ `backend/app/utils/phone.py` - Phone normalization utilities
- ✅ `backend/app/dependencies/auth.py` - Role-based access control dependencies

### Configuration
- ✅ `backend/app/core/config.py` - Added OTP and Google OAuth env vars
- ✅ `backend/app/core/security.py` - Added role parameter to create_access_token

## Files Needing Updates

### 1. `backend/app/routers/auth.py`
**Changes needed:**
- Replace `OTPService` import with `OTPServiceV2`
- Update `POST /v1/auth/otp/start` to use new service
- Update `POST /v1/auth/otp/verify` to use new service and create token with role="driver"
- Add PostHog events: `server.driver.otp.start`, `server.driver.otp.verify.success|fail`
- Use safe error messages: "Unable to send code. Try again later." / "Invalid code."

### 2. `backend/app/routers/auth_domain.py`
**Changes needed:**
- Update `POST /v1/auth/merchant/google` to:
  - Use `GoogleOAuthService.verify_and_check_gbp()` 
  - Check GBP access (if `GOOGLE_GBP_REQUIRED=true`)
  - Create token with `role="merchant"`
  - Add audit logging and PostHog events
- Add `GET /v1/merchant/me` endpoint (if not exists)

### 3. Frontend Updates
**Driver App (`apps/driver`):**
- Add resend cooldown timer (30s)
- Show generic error messages
- Disable submit while in-flight
- PostHog client events: `driver.otp.start`, `driver.otp.verify.success|fail`

**Merchant Portal (`apps/merchant`):**
- Add "Sign in with Google" button
- Complete OAuth flow
- Call `/api/v1/auth/me` or `/api/v1/merchant/me` on app boot
- PostHog events: `merchant.login.success|fail`

## Next Steps

1. Update OTP routes in `auth.py`
2. Update merchant Google SSO route in `auth_domain.py`
3. Add role enforcement to merchant/admin endpoints
4. Update frontend OTP UI
5. Update frontend merchant login
6. Add tests
7. Update documentation




