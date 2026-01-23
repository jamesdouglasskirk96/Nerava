# Production Analysis & Next Steps

## Current Deployment Status
- **Image**: `v14-merchants-open` deployment IN_PROGRESS
- **Started**: 2026-01-22 08:48:51 CST

---

## Part 1: Missing API Keys & Accounts for Production

### Currently Configured in App Runner ✓
| Variable | Status |
|----------|--------|
| DATABASE_URL | ✓ Configured (PostgreSQL RDS) |
| REDIS_URL | ✓ Configured (ElastiCache) |
| JWT_SECRET | ✓ Configured |
| TOKEN_ENCRYPTION_KEY | ✓ Configured |
| TWILIO_ACCOUNT_SID | ✓ Configured |
| TWILIO_AUTH_TOKEN | ✓ Configured |
| TWILIO_VERIFY_SERVICE_SID | ✓ Configured |
| OTP_PROVIDER | ✓ Configured (twilio_verify) |
| ALLOWED_ORIGINS | ✓ Configured |
| PUBLIC_WEB_BASE_URL | ✓ Configured |

### MISSING - Required for Full Production

#### 1. Stripe (Payments) - HIGH PRIORITY
- **Account needed**: Stripe Dashboard account
- **Keys required**:
  - `STRIPE_SECRET_KEY` - Secret key from Stripe Dashboard
  - `STRIPE_CONNECT_CLIENT_ID` - For merchant onboarding (Connect)
  - `STRIPE_WEBHOOK_SECRET` - For webhook verification
- **Setup URL**: https://dashboard.stripe.com/apikeys

#### 2. Square (Merchant POS Integration) - MEDIUM PRIORITY
- **Account needed**: Square Developer account
- **Keys required**:
  - `SQUARE_APPLICATION_ID_PRODUCTION`
  - `SQUARE_APPLICATION_SECRET_PRODUCTION`
  - `SQUARE_REDIRECT_URL_PRODUCTION`
  - `SQUARE_WEBHOOK_SIGNATURE_KEY`
- **Setup URL**: https://developer.squareup.com/apps

#### 3. Smartcar (EV Vehicle Data) - MEDIUM PRIORITY
- **Account needed**: Smartcar Developer account
- **Keys required**:
  - `SMARTCAR_CLIENT_ID`
  - `SMARTCAR_CLIENT_SECRET`
  - `SMARTCAR_REDIRECT_URI` (e.g., `https://api.nerava.network/oauth/smartcar/callback`)
  - `SMARTCAR_STATE_SECRET` - Random secret for state JWT
  - `SMARTCAR_MODE` = `live` (currently defaults to sandbox)
  - `SMARTCAR_ENABLED` = `true`
- **Setup URL**: https://dashboard.smartcar.com/

#### 4. Google Places API - ALREADY HARDCODED
- **Status**: API key is hardcoded in `app/utils/pwa_responses.py`
- **Key**: `AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg`
- **Recommendation**: Move to environment variable `GOOGLE_PLACES_API_KEY`
- **Setup URL**: https://console.cloud.google.com/apis/credentials

#### 5. Google Sign-In - LOW PRIORITY (Optional)
- **Account needed**: Google Cloud Console
- **Keys required**:
  - `GOOGLE_CLIENT_ID`
- **Setup URL**: https://console.cloud.google.com/apis/credentials

#### 6. Apple Sign-In - LOW PRIORITY (Optional)
- **Account needed**: Apple Developer account ($99/year)
- **Keys required**:
  - `APPLE_CLIENT_ID`
  - `APPLE_TEAM_ID`
  - `APPLE_KEY_ID`
  - `APPLE_PRIVATE_KEY`
- **Setup URL**: https://developer.apple.com/account/resources/authkeys/list

#### 7. SendGrid (Email) - MEDIUM PRIORITY
- **Account needed**: SendGrid account
- **Keys required**:
  - `SENDGRID_API_KEY`
  - `EMAIL_FROM` (e.g., `noreply@nerava.network`)
  - `EMAIL_PROVIDER` = `sendgrid`
- **Setup URL**: https://app.sendgrid.com/settings/api_keys

#### 8. HubSpot (CRM) - LOW PRIORITY (Optional)
- **Account needed**: HubSpot account
- **Keys required**:
  - `HUBSPOT_PRIVATE_APP_TOKEN`
  - `HUBSPOT_PORTAL_ID`
  - `HUBSPOT_ENABLED` = `true`
  - `HUBSPOT_SEND_LIVE` = `true`
- **Setup URL**: https://app.hubspot.com/private-apps/

#### 9. Sentry (Error Tracking) - MEDIUM PRIORITY
- **Account needed**: Sentry account (free tier available)
- **Keys required**:
  - `SENTRY_DSN`
  - `SENTRY_ENVIRONMENT` = `prod`
  - `SENTRY_ENABLED` = `true`
- **Setup URL**: https://sentry.io/settings/projects/

#### 10. PostHog (Analytics) - LOW PRIORITY
- **Account needed**: PostHog account
- **Keys required**:
  - `POSTHOG_API_KEY`
  - `POSTHOG_HOST` (default: https://app.posthog.com)
  - `ANALYTICS_ENABLED` = `true`
- **Setup URL**: https://app.posthog.com/project/settings

#### 11. Apple Wallet Pass Signing - LOW PRIORITY
- **Account needed**: Apple Developer account with Pass Type ID
- **Keys required**:
  - `APPLE_WALLET_SIGNING_ENABLED` = `true`
  - `APPLE_WALLET_PASS_TYPE_ID`
  - `APPLE_WALLET_TEAM_ID`
  - `APPLE_WALLET_CERT_P12_PATH`
  - `APPLE_WALLET_CERT_P12_PASSWORD`

---

## Part 2: Validated Cursor Changes

### Change 1: Auth Middleware Update ✓
**File**: `app/middleware/auth.py`
**Lines**: 36-55
**Status**: CORRECT

```python
# Added optional auth path prefixes (lines 37-40)
self.optional_auth_path_prefixes = [
    "/v1/drivers/merchants/open",  # Merchants for charger (optional auth)
    "/v1/chargers/discovery",  # Charger discovery (optional auth)
]

# Added dispatch logic (lines 52-55)
for prefix in getattr(self, 'optional_auth_path_prefixes', []):
    if request.url.path.startswith(prefix):
        return await call_next(request)
```

### Change 2: Merchants Open Endpoint ✓
**File**: `app/routers/drivers_domain.py`
**Lines**: 394-495
**Status**: CORRECT
- Endpoint: `GET /v1/drivers/merchants/open`
- Optional authentication with `get_current_driver_optional`
- Returns merchants linked to charger via `ChargerMerchant`
- Special handling for Asadas Grill (`is_primary: true`)

### Change 3: Seed Script ✓
**File**: `scripts/seed_asadas_grill.py`
**Status**: CORRECT
- Creates Asadas Grill merchant with correct data
- Creates "Free Beverage Exclusive" perk
- Links to Domain chargers

### Change 4: Merchant Details Service ✓
**File**: `app/services/merchant_details.py`
**Lines**: 111-157
**Status**: CORRECT
- Asadas Grill shows "Free Beverage Exclusive" perk
- Badge shows "Exclusive" (not "Happy Hour ⭐️")
- Category shows "Restaurant" (not "Restaurant • Food")

---

## Part 3: Next Steps

### Immediate (After Deployment Completes)

1. **Wait for deployment to complete**
   ```bash
   # Check status
   aws apprunner describe-service \
     --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
     --region us-east-1 | jq '.Service.Status'
   ```

2. **Verify endpoints work**
   ```bash
   # Health check
   curl https://api.nerava.network/healthz

   # Merchants for charger (should return empty - no data yet)
   curl "https://api.nerava.network/v1/drivers/merchants/open?charger_id=ch_domain_tesla_001"

   # Discovery endpoint
   curl "https://api.nerava.network/v1/chargers/discovery?lat=30.38&lng=-97.69"
   ```

3. **Seed production database with Asadas Grill**
   - Option A: Run seed script against production DB
   - Option B: Execute SQL directly (see `cursor-prompt-deploy-and-fix-auth.txt`)

### Short-term (This Week)

4. **Add Stripe integration**
   - Create Stripe account if not exists
   - Add environment variables to App Runner
   - Test payment flows

5. **Add Sentry for error tracking**
   - Create Sentry project
   - Add DSN to environment variables

6. **Add SendGrid for email**
   - Create SendGrid account
   - Configure domain authentication
   - Add API key to environment variables

### Medium-term (Next 2 Weeks)

7. **Set up Smartcar for EV data**
   - Create Smartcar developer account
   - Configure OAuth redirect URI
   - Enable in production

8. **Move Google Places API key to env var**
   - Currently hardcoded - security concern
   - Add `GOOGLE_PLACES_API_KEY` to config

9. **Configure Square for merchant POS**
   - Set up production credentials
   - Test webhook integration

---

## Part 4: Summary for ChatGPT

### What Was Done
1. Auth middleware updated to allow optional authentication for `/v1/drivers/merchants/open` and `/v1/chargers/discovery`
2. New endpoint created: `GET /v1/drivers/merchants/open?charger_id=...`
3. Seed script created for Asadas Grill merchant with "Free Beverage Exclusive" perk
4. Merchant details service updated to show correct data for Asadas Grill
5. Docker image v14-merchants-open pushed to ECR
6. App Runner deployment initiated (currently in progress)

### What Still Needs to Be Done
1. Wait for deployment to complete
2. Seed Asadas Grill data in production database
3. Add missing API keys/accounts (Stripe, Sentry, SendGrid most important)
4. Test end-to-end flow in production

### Key Files Modified
- `app/middleware/auth.py` - Optional auth paths
- `app/routers/drivers_domain.py` - New endpoint
- `app/services/merchant_details.py` - Asadas Grill perk/category
- `scripts/seed_asadas_grill.py` - New seed script

### Production Environment Variables Needed (Priority Order)
1. **HIGH**: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
2. **MEDIUM**: `SENTRY_DSN`, `SENDGRID_API_KEY`
3. **MEDIUM**: `SMARTCAR_CLIENT_ID`, `SMARTCAR_CLIENT_SECRET`
4. **LOW**: `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID`, `POSTHOG_API_KEY`
