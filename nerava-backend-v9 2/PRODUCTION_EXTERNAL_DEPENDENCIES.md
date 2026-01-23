# Production External Dependencies Analysis
**Generated:** 2026-01-22  
**Purpose:** Complete inventory of all external API keys, services, and dependencies required before production deployment

---

## 🔴 CRITICAL - Required for Production

### 1. **Twilio (OTP/SMS Verification)**
**Status:** ⚠️ **CONFIGURED BUT NEEDS VERIFICATION**
- **Purpose:** Phone number verification via OTP codes
- **Current State:** Configured with credentials in App Runner
- **Required Environment Variables:**
  - `TWILIO_ACCOUNT_SID` ✅ Set
  - `TWILIO_AUTH_TOKEN` ✅ Set
  - `TWILIO_VERIFY_SERVICE_SID` ✅ Set
  - `OTP_PROVIDER` ✅ Set to `twilio_verify`
- **Action Required:** Verify SMS delivery works in production
- **Cost:** Pay-per-SMS (~$0.0075 per SMS)

---

### 2. **PostgreSQL Database**
**Status:** ✅ **CONFIGURED**
- **Purpose:** Primary database (replaces SQLite)
- **Current State:** RDS PostgreSQL configured
- **Required Environment Variables:**
  - `DATABASE_URL` ✅ Set (postgresql+psycopg2://...)
- **Action Required:** None - already configured
- **Cost:** AWS RDS pricing

---

### 3. **Redis Cache**
**Status:** ✅ **CONFIGURED**
- **Purpose:** Rate limiting, caching, session storage
- **Current State:** ElastiCache Redis configured
- **Required Environment Variables:**
  - `REDIS_URL` ✅ Set (redis://nerava-redis...)
- **Action Required:** None - already configured
- **Cost:** AWS ElastiCache pricing

---

### 4. **JWT Secret**
**Status:** ✅ **CONFIGURED**
- **Purpose:** JWT token signing
- **Current State:** Set in App Runner
- **Required Environment Variables:**
  - `JWT_SECRET` ✅ Set
- **Action Required:** Ensure secret is strong (32+ random bytes)
- **Security:** Must be unique and never exposed

---

### 5. **Token Encryption Key**
**Status:** ✅ **CONFIGURED**
- **Purpose:** Encrypts Square access tokens, vehicle tokens
- **Current State:** Set in App Runner
- **Required Environment Variables:**
  - `TOKEN_ENCRYPTION_KEY` ✅ Set (Fernet key, 44 chars)
- **Action Required:** Verify key format is valid Fernet key
- **Security:** Critical - if lost, encrypted tokens cannot be decrypted

---

## 🟡 IMPORTANT - Required for Core Features

### 6. **Google Places API**
**Status:** ⚠️ **PARTIALLY CONFIGURED**
- **Purpose:** Merchant discovery, place details, photo URLs
- **Current State:** API key referenced in code but may not be set in production
- **Required Environment Variables:**
  - `GOOGLE_PLACES_API_KEY` ❓ **NEEDS VERIFICATION**
- **Code Locations:**
  - `app/services/google_places_new.py`
  - `app/utils/pwa_responses.py` (hardcoded key: `AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg`)
- **Action Required:**
  1. Set `GOOGLE_PLACES_API_KEY` in App Runner environment variables
  2. Remove hardcoded API key from `app/utils/pwa_responses.py:27`
  3. Enable Places API (New) in Google Cloud Console
  4. Set up billing quota limits
- **Cost:** Pay-per-request (~$0.017 per request)
- **Quotas:** Set daily limits to prevent unexpected charges

---

### 7. **Stripe**
**Status:** ⚠️ **NEEDS PRODUCTION CREDENTIALS**
- **Purpose:** Driver payouts (wallet → bank account)
- **Current State:** May be using test keys
- **Required Environment Variables:**
  - `STRIPE_SECRET_KEY` ❓ **NEEDS PRODUCTION KEY**
  - `STRIPE_WEBHOOK_SECRET` ❓ **NEEDS PRODUCTION SECRET**
- **Code Locations:**
  - `app/routers/stripe_api.py`
  - `app/clients/stripe_client.py`
- **Action Required:**
  1. Create production Stripe account
  2. Get live API keys from Stripe Dashboard
  3. Set up webhook endpoint: `https://api.nerava.network/v1/stripe/webhook`
  4. Configure webhook secret
  5. Test payout flow in production
- **Cost:** 2.9% + $0.30 per transaction
- **Security:** Webhook signature verification required

---

### 8. **Square**
**Status:** ⚠️ **NEEDS PRODUCTION CREDENTIALS**
- **Purpose:** Merchant payment processing, OAuth onboarding
- **Current State:** Likely using sandbox credentials
- **Required Environment Variables:**
  - `SQUARE_APPLICATION_ID` ❓ **NEEDS PRODUCTION APP ID**
  - `SQUARE_ACCESS_TOKEN` ❓ **NEEDS PRODUCTION TOKEN** (per merchant)
  - `SQUARE_LOCATION_ID` ❓ **NEEDS PRODUCTION LOCATION**
  - `SQUARE_WEBHOOK_SIGNATURE_KEY` ❓ **NEEDS PRODUCTION KEY**
  - `SQUARE_ENV` ❓ **MUST BE `production`** (not `sandbox`)
- **Code Locations:**
  - `app/routers/square.py`
  - `app/routers/merchants_domain.py`
  - `app/services/square_service.py`
- **Action Required:**
  1. Create production Square application
  2. Set up OAuth redirect: `https://api.nerava.network/v1/merchants/square/callback`
  3. Configure webhook endpoint: `https://api.nerava.network/v1/webhooks/square`
  4. Test merchant onboarding flow
- **Cost:** 2.6% + $0.10 per transaction
- **Security:** OAuth tokens encrypted with `TOKEN_ENCRYPTION_KEY`

---

### 9. **Smartcar (EV Telemetry)**
**Status:** ⚠️ **OPTIONAL BUT NEEDS CONFIGURATION IF ENABLED**
- **Purpose:** EV battery status, charging state, location
- **Current State:** Disabled by default (`SMARTCAR_ENABLED=false`)
- **Required Environment Variables:**
  - `SMARTCAR_CLIENT_ID` ❓ **NEEDS PRODUCTION CLIENT ID**
  - `SMARTCAR_CLIENT_SECRET` ❓ **NEEDS PRODUCTION SECRET**
  - `SMARTCAR_REDIRECT_URI` ❓ **MUST BE HTTPS** (e.g., `https://api.nerava.network/oauth/smartcar/callback`)
  - `SMARTCAR_MODE` ❓ **MUST BE `live`** (not `sandbox`)
  - `SMARTCAR_STATE_SECRET` ❓ **NEEDS RANDOM SECRET** (CSRF protection)
  - `SMARTCAR_ENABLED` ❓ **SET TO `true`** to enable
- **Code Locations:**
  - `app/routers/ev_smartcar.py`
  - `app/services/smartcar_service.py`
- **Action Required:**
  1. Create production Smartcar application
  2. Set redirect URI in Smartcar dashboard
  3. Generate `SMARTCAR_STATE_SECRET`: `openssl rand -hex 16`
  4. Test OAuth flow in production
- **Cost:** Per-vehicle pricing (check Smartcar pricing)
- **Note:** Feature can remain disabled if not needed initially

---

## 🟢 OPTIONAL - Analytics & Monitoring

### 10. **PostHog Analytics**
**Status:** ❌ **NOT CONFIGURED**
- **Purpose:** User analytics, event tracking
- **Current State:** Referenced in code comments but not implemented
- **Code References:**
  - `app/services/auth/audit.py:8-9` (comment mentions PostHog)
- **Action Required:**
  1. Create PostHog account
  2. Get API key
  3. Add `POSTHOG_API_KEY` environment variable
  4. Implement PostHog client in route handlers
  5. Send events for key actions (signup, login, transactions)
- **Cost:** Free tier available, then usage-based
- **Priority:** Low - can be added post-launch

---

### 11. **Sentry (Error Tracking)**
**Status:** ❌ **NOT CONFIGURED**
- **Purpose:** Error tracking and monitoring
- **Current State:** Mentioned in `ENV.example` but not configured
- **Required Environment Variables:**
  - `SENTRY_DSN` ❓ **NEEDS SENTRY DSN**
- **Action Required:**
  1. Create Sentry account
  2. Create project for Nerava backend
  3. Get DSN from Sentry dashboard
  4. Set `SENTRY_DSN` in App Runner
  5. Install Sentry SDK (may need to add to requirements.txt)
- **Cost:** Free tier available
- **Priority:** Medium - recommended for production monitoring

---

### 12. **HubSpot**
**Status:** ⚠️ **CONFIGURED BUT DISABLED**
- **Purpose:** CRM integration, lead tracking
- **Current State:** Configuration exists but `HUBSPOT_ENABLED=false`
- **Required Environment Variables:**
  - `HUBSPOT_ENABLED` ❓ **SET TO `true`** to enable
  - `HUBSPOT_SEND_LIVE` ❓ **SET TO `true`** for production
  - `HUBSPOT_PRIVATE_APP_TOKEN` ❓ **NEEDS TOKEN**
  - `HUBSPOT_PORTAL_ID` ❓ **NEEDS PORTAL ID**
- **Code Locations:**
  - `app/core/config.py:124-128`
  - `app/core/config.py:206-221` (validation)
- **Action Required:**
  1. Create HubSpot private app
  2. Get private app token
  3. Get portal ID
  4. Configure if CRM integration needed
- **Cost:** HubSpot pricing
- **Priority:** Low - only if CRM integration needed

---

## 🔵 INFRASTRUCTURE - AWS Services

### 13. **AWS S3 (Photo Storage)**
**Status:** ⚠️ **CONFIGURED BUT NOT USED**
- **Purpose:** Vehicle onboarding photos, merchant photos
- **Current State:** Code exists but uses mock URLs
- **Required Environment Variables:**
  - `AWS_S3_BUCKET` ❓ **NEEDS BUCKET NAME**
  - `AWS_S3_REGION` ✅ Default: `us-east-1`
  - `AWS_ACCESS_KEY_ID` ❓ **NEEDS ACCESS KEY**
  - `AWS_SECRET_ACCESS_KEY` ❓ **NEEDS SECRET KEY**
- **Code Locations:**
  - `app/services/s3_storage.py` (mock implementation)
- **Action Required:**
  1. Create S3 bucket for photos
  2. Set up IAM user with S3 permissions
  3. Configure bucket CORS for photo access
  4. Implement real S3 upload/download (currently mocked)
  5. Set up CloudFront distribution for CDN (optional)
- **Cost:** S3 storage + transfer costs
- **Priority:** Medium - photos currently served from static files

---

### 14. **AWS App Runner**
**Status:** ✅ **CONFIGURED**
- **Purpose:** Container hosting
- **Current State:** Running and configured
- **Action Required:** None
- **Cost:** AWS App Runner pricing

---

### 15. **AWS ECR (Container Registry)**
**Status:** ✅ **CONFIGURED**
- **Purpose:** Docker image storage
- **Current State:** Configured and working
- **Action Required:** None
- **Cost:** AWS ECR pricing

---

## 🟣 APPLE WALLET - Optional Feature

### 16. **Apple Wallet Pass Signing**
**Status:** ⚠️ **DISABLED BY DEFAULT**
- **Purpose:** Apple Wallet pass generation and push notifications
- **Current State:** `APPLE_WALLET_SIGNING_ENABLED=false`
- **Required Environment Variables:**
  - `APPLE_WALLET_SIGNING_ENABLED` ❓ **SET TO `true`** to enable
  - `APPLE_WALLET_PASS_TYPE_ID` ✅ Default: `pass.com.nerava.wallet`
  - `APPLE_WALLET_TEAM_ID` ❓ **NEEDS APPLE TEAM ID**
  - `APPLE_WALLET_CERT_P12_PATH` ❓ **NEEDS CERT PATH** (or PEM cert/key)
  - `APPLE_WALLET_CERT_P12_PASSWORD` ❓ **NEEDS CERT PASSWORD**
  - `APPLE_WALLET_APNS_KEY_ID` ❓ **NEEDS APNS KEY ID**
  - `APPLE_WALLET_APNS_TEAM_ID` ❓ **NEEDS APNS TEAM ID**
  - `APPLE_WALLET_APNS_AUTH_KEY_PATH` ❓ **NEEDS APNS KEY PATH**
- **Code Locations:**
  - `app/services/apple_wallet_pass.py`
  - `app/routers/wallet_pass.py`
- **Action Required:**
  1. Enroll in Apple Developer Program ($99/year)
  2. Create Pass Type ID certificate
  3. Create APNS key for push notifications
  4. Upload certificates to secure storage (AWS Secrets Manager or similar)
  5. Configure certificate paths in App Runner
- **Cost:** Apple Developer Program: $99/year
- **Priority:** Low - can be added post-launch

---

## 📧 EMAIL SERVICE - Currently Console-Based

### 17. **Email Service (Production)**
**Status:** ❌ **NOT CONFIGURED - USES CONSOLE LOGGING**
- **Purpose:** Magic link emails, notifications
- **Current State:** `ConsoleEmailSender` logs to console (dev only)
- **Code Locations:**
  - `app/core/email_sender.py` (abstraction exists)
  - `app/routers/auth_domain.py:280-297` (magic link emails)
- **Action Required:**
  1. Choose email service (SendGrid, Mailgun, AWS SES, etc.)
  2. Implement email sender class (e.g., `SendGridEmailSender`)
  3. Add API key to environment variables
  4. Update `get_email_sender()` to use production sender
  5. Test email delivery
- **Options:**
  - **SendGrid:** Easy integration, free tier (100 emails/day)
  - **Mailgun:** Good deliverability, free tier (5,000 emails/month)
  - **AWS SES:** Cost-effective, requires domain verification
- **Cost:** Varies by provider
- **Priority:** **HIGH** - Magic links won't work without email service

---

## 🔐 AUTHENTICATION PROVIDERS - Optional

### 18. **Google OAuth**
**Status:** ⚠️ **PARTIALLY CONFIGURED**
- **Purpose:** Google sign-in
- **Current State:** `GOOGLE_CLIENT_ID` exists in config
- **Required Environment Variables:**
  - `GOOGLE_CLIENT_ID` ❓ **NEEDS PRODUCTION CLIENT ID**
- **Code Locations:**
  - `app/core/config.py:87`
  - `app/routers/merchant_onboarding.py` (merchant Google auth)
- **Action Required:**
  1. Create Google OAuth credentials in Google Cloud Console
  2. Set authorized redirect URIs
  3. Configure if Google sign-in needed
- **Priority:** Low - OTP is primary auth method

---

### 19. **Apple Sign-In**
**Status:** ⚠️ **PARTIALLY CONFIGURED**
- **Purpose:** Apple sign-in
- **Current State:** Config exists but may not be fully implemented
- **Required Environment Variables:**
  - `APPLE_CLIENT_ID` ❓ **NEEDS APPLE CLIENT ID**
  - `APPLE_TEAM_ID` ❓ **NEEDS APPLE TEAM ID**
  - `APPLE_KEY_ID` ❓ **NEEDS APPLE KEY ID**
  - `APPLE_PRIVATE_KEY` ❓ **NEEDS APPLE PRIVATE KEY**
- **Code Locations:**
  - `app/core/config.py:88-91`
- **Action Required:**
  1. Create Apple Services ID
  2. Configure Sign in with Apple
  3. Generate private key
  4. Configure if Apple sign-in needed
- **Priority:** Low - OTP is primary auth method

---

## 📊 SUMMARY

### ✅ Already Configured (7)
1. Twilio (OTP/SMS)
2. PostgreSQL Database
3. Redis Cache
4. JWT Secret
5. Token Encryption Key
6. AWS App Runner
7. AWS ECR

### ⚠️ Needs Production Credentials (6)
1. **Google Places API** - Set API key, remove hardcoded key
2. **Stripe** - Get live API keys, configure webhooks
3. **Square** - Get production app credentials, set `SQUARE_ENV=production`
4. **Smartcar** - Optional, configure if EV features needed
5. **Email Service** - **CRITICAL** - Implement production email sender
6. **AWS S3** - Configure if using photo uploads

### ❌ Not Configured (5)
1. **PostHog Analytics** - Optional, can add post-launch
2. **Sentry** - Recommended for error tracking
3. **HubSpot** - Optional CRM integration
4. **Apple Wallet** - Optional feature
5. **Google/Apple OAuth** - Optional auth methods

### 🔴 Critical Blockers for Production
1. **Email Service** - Magic links won't work without production email
2. **Google Places API Key** - Merchant discovery will fail
3. **Stripe Production Keys** - Payouts won't work
4. **Square Production Keys** - Merchant payments won't work

---

## 📝 ACTION ITEMS CHECKLIST

### Before Production Launch:
- [ ] Set `GOOGLE_PLACES_API_KEY` in App Runner
- [ ] Remove hardcoded Google API key from `app/utils/pwa_responses.py:27`
- [ ] Implement production email sender (SendGrid/Mailgun/SES)
- [ ] Configure Stripe production keys and webhooks
- [ ] Configure Square production credentials
- [ ] Set `SQUARE_ENV=production` (not `sandbox`)
- [ ] Set `SMARTCAR_MODE=live` if using Smartcar
- [ ] Test OTP SMS delivery in production
- [ ] Test magic link email delivery
- [ ] Set up Sentry for error tracking (recommended)
- [ ] Configure S3 bucket if using photo uploads
- [ ] Review and set all feature flags appropriately
- [ ] Verify `DEMO_MODE=false` in production
- [ ] Verify `OTP_PROVIDER=twilio_verify` (not `stub`)

### Post-Launch (Optional):
- [ ] Set up PostHog analytics
- [ ] Configure HubSpot if CRM needed
- [ ] Set up Apple Wallet if needed
- [ ] Configure Google/Apple OAuth if needed

---

## 💰 ESTIMATED MONTHLY COSTS

| Service | Estimated Cost |
|---------|---------------|
| Twilio (SMS) | $50-200 (depends on usage) |
| Google Places API | $100-500 (depends on requests) |
| Stripe | 2.9% + $0.30 per transaction |
| Square | 2.6% + $0.10 per transaction |
| Email Service | $0-50 (free tiers available) |
| AWS RDS | $50-200 |
| AWS ElastiCache | $20-100 |
| AWS App Runner | $50-300 |
| AWS S3 | $10-50 |
| **Total** | **$280-1,500/month** (excluding transaction fees) |

---

## 🔒 SECURITY CHECKLIST

- [ ] All API keys stored in AWS Secrets Manager or App Runner env vars (not in code)
- [ ] `JWT_SECRET` is strong random value (32+ bytes)
- [ ] `TOKEN_ENCRYPTION_KEY` is valid Fernet key (44 chars)
- [ ] `DEMO_MODE=false` in production
- [ ] `OTP_PROVIDER=twilio_verify` (not `stub`)
- [ ] `NERAVA_DEV_ALLOW_ANON_USER=false`
- [ ] `NERAVA_DEV_ALLOW_ANON_DRIVER=false`
- [ ] CORS origins are explicit (not wildcard `*`)
- [ ] Database URL is PostgreSQL (not SQLite)
- [ ] Redis URL is configured (not localhost)
- [ ] All webhook endpoints verify signatures
- [ ] HTTPS enforced (App Runner default)

---

**Last Updated:** 2026-01-22  
**Next Review:** Before production launch


