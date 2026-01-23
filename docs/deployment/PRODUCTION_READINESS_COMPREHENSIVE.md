# Nerava Production Readiness Document
## Comprehensive Technical Analysis for Product Launch

**Generated:** 2025-01-27  
**Target Launch Date:** 1 week  
**Purpose:** Complete inventory of all components, dependencies, API integrations, and production requirements  
**Audience:** ChatGPT Code Review System / Technical Team

---

## EXECUTIVE SUMMARY

This document provides a complete technical inventory of the Nerava platform across 5 major components:
1. **Backend API** (FastAPI/Python)
2. **Driver App** (React/Vite)
3. **Admin Console** (React/Vite)
4. **Merchant Dashboard** (React/Vite)
5. **Landing Page** (Next.js)

**Critical Status:**
- **Total External API Integrations:** 12
- **Total Environment Variables Required:** 50+
- **API Keys Missing:** 8+ need production credentials
- **Mock Modes Active:** 3 must be disabled
- **Production Blockers:** 5 critical issues

---

## COMPONENT 1: BACKEND API

### Architecture
- **Framework:** FastAPI (Python 3.9+)
- **Entry Point:** `backend/app/main_simple.py`
- **Database:** SQLite (dev) → PostgreSQL (prod) - **MUST CHANGE**
- **Cache:** Redis (required in prod)
- **Deployment:** Docker container, port 8001
- **WSGI Server:** Gunicorn + Uvicorn workers (production)

### External API Integrations

#### 1. Twilio (OTP/SMS)
**Status:** ⚠️ **REQUIRES PRODUCTION CREDENTIALS**
- **Purpose:** Phone number verification via OTP
- **Location:** `backend/app/services/auth/otp_factory.py`
- **Provider Options:** `twilio_verify`, `twilio_sms`, `stub` (dev only)
- **Required Environment Variables:**
  - `TWILIO_ACCOUNT_SID` - **MISSING** (get from Twilio Console)
  - `TWILIO_AUTH_TOKEN` - **MISSING** (get from Twilio Console)
  - `TWILIO_VERIFY_SERVICE_SID` - **MISSING** (if using `twilio_verify`)
  - `OTP_FROM_NUMBER` - **MISSING** (if using `twilio_sms`, e.g., +1234567890)
  - `OTP_PROVIDER` - **MUST SET** to `twilio_verify` or `twilio_sms` (NOT `stub` in prod)
- **Current Status:** Defaults to `stub` mode (accepts code `000000` for any phone)
- **Production Validation:** `backend/app/core/config.py:242-267` - Will fail startup if `stub` in prod
- **Files:**
  - `backend/app/services/auth/twilio_verify.py`
  - `backend/app/services/auth/twilio_sms.py`
  - `backend/app/services/auth/stub_provider.py` (dev only)

#### 2. Google OAuth (Merchant Onboarding)
**Status:** ⚠️ **REQUIRES PRODUCTION CREDENTIALS**
- **Purpose:** Merchant authentication via Google Business Profile
- **Location:** `backend/app/services/google_business_profile.py`
- **Required Environment Variables:**
  - `GOOGLE_CLIENT_ID` - **MISSING** (OAuth client ID from Google Cloud Console)
  - `GOOGLE_CLIENT_SECRET` - **MISSING** (OAuth client secret)
  - `GOOGLE_OAUTH_CLIENT_ID` - **MISSING** (alias for GOOGLE_CLIENT_ID)
  - `GOOGLE_OAUTH_CLIENT_SECRET` - **MISSING** (alias for GOOGLE_CLIENT_SECRET)
  - `GOOGLE_OAUTH_REDIRECT_URI` - **MUST SET** to `https://api.nerava.network/v1/merchants/google/callback`
  - `MERCHANT_AUTH_MOCK` - **MUST SET** to `false` in production
- **Current Status:** Mock mode enabled by default (`MERCHANT_AUTH_MOCK=true`)
- **Mock Implementation:** `backend/app/services/google_business_profile.py:40-42, 70-77, 113-137`
- **Production Validation:** `backend/app/core/config.py:285-289` - Will fail startup if mock enabled in prod
- **Files:**
  - `backend/app/services/google_business_profile.py`
  - `backend/app/services/auth/google_oauth.py`

#### 3. Google Places API
**Status:** ⚠️ **REQUIRES API KEY**
- **Purpose:** Merchant discovery, place details, distance calculations
- **Location:** `backend/app/services/google_places_new.py`
- **Required Environment Variables:**
  - `GOOGLE_PLACES_API_KEY` - **MISSING** (get from Google Cloud Console)
  - **API Requirements:** Enable "Places API" and "Distance Matrix API" in Google Cloud Console
- **Current Status:** No validation if missing (fails silently)
- **Usage:** Used by `/v1/drivers/merchants/nearby`, `/v1/merchants/{id}`, charger-merchant mapping
- **Files:**
  - `backend/app/services/google_places_new.py`
  - `backend/app/services/merchants_google.py`
- **Note:** Hardcoded API key found in `backend/app/scripts/analyze_texas_chargers.py:33` - **MUST REMOVE**

#### 4. NREL API (Charger Data)
**Status:** ⚠️ **REQUIRES API KEY**
- **Purpose:** EV charging station data
- **Location:** `backend/app/services/while_you_charge.py`
- **Required Environment Variables:**
  - `NREL_API_KEY` - **MISSING** (free key from https://developer.nrel.gov/signup/)
- **Current Status:** No validation if missing
- **Usage:** Used by `/v1/while-you-charge/chargers/nearby`
- **Files:**
  - `backend/app/services/while_you_charge.py`
  - `backend/app/services/chargers_openmap.py`

#### 5. Square API (Merchant Payments)
**Status:** ⚠️ **REQUIRES PRODUCTION CREDENTIALS**
- **Purpose:** Merchant payment processing, OAuth onboarding, order lookup
- **Location:** `backend/app/routers/square.py`, `backend/app/services/square_service.py`
- **Required Environment Variables:**
  - `SQUARE_ENV` - **MUST SET** to `production` (NOT `sandbox`)
  - `SQUARE_APPLICATION_ID_PRODUCTION` - **MISSING** (get from Square Developer Dashboard)
  - `SQUARE_APPLICATION_SECRET_PRODUCTION` - **MISSING** (get from Square Developer Dashboard)
  - `SQUARE_REDIRECT_URL_PRODUCTION` - **MUST SET** to `https://api.nerava.network/v1/merchants/square/callback`
  - `SQUARE_WEBHOOK_SIGNATURE_KEY` - **MISSING** (get from Square Dashboard → Webhooks)
  - `TOKEN_ENCRYPTION_KEY` - **MUST GENERATE** (Fernet key, 44 chars, for encrypting Square tokens)
- **Current Status:** Defaults to `sandbox` mode
- **Sandbox Config:** `backend/app/config.py:165-184` (get_square_sandbox_config)
- **Production Config:** Uses `SQUARE_APPLICATION_ID_PRODUCTION`, `SQUARE_APPLICATION_SECRET_PRODUCTION`
- **Token Storage:** Encrypted in `domain_merchants.square_access_token` column
- **Files:**
  - `backend/app/routers/square.py`
  - `backend/app/services/square_service.py`
  - `backend/app/services/square_orders.py`
  - `backend/app/services/token_encryption.py`

#### 6. Stripe (Payouts)
**Status:** ⚠️ **REQUIRES LIVE CREDENTIALS**
- **Purpose:** Driver wallet payouts to bank accounts
- **Location:** `backend/app/routers/stripe_api.py`, `backend/app/services/stripe_service.py`
- **Required Environment Variables:**
  - `STRIPE_SECRET_KEY` - **MUST BE LIVE KEY** (`sk_live_...` NOT `sk_test_...`)
  - `STRIPE_WEBHOOK_SECRET` - **MISSING** (get from Stripe Dashboard → Webhooks → Signing secret, format: `whsec_...`)
  - `STRIPE_CONNECT_CLIENT_ID` - **OPTIONAL** (for Stripe Connect, format: `ca_...`)
- **Current Status:** Test keys may be configured
- **Webhook Endpoint:** `/v1/stripe/webhook` - **MUST CONFIGURE** in Stripe Dashboard
- **Webhook Events:** `payment_intent.succeeded`, `transfer.created`, `charge.refunded`
- **Files:**
  - `backend/app/routers/stripe_api.py`
  - `backend/app/services/stripe_service.py`
  - `backend/app/clients/stripe_client.py` (if exists)

#### 7. Smartcar (EV Telemetry)
**Status:** ⚠️ **REQUIRES LIVE CREDENTIALS**
- **Purpose:** EV vehicle connection, battery status, charging state, location
- **Location:** `backend/app/routers/ev_smartcar.py`, `backend/app/services/smartcar_service.py`
- **Required Environment Variables:**
  - `SMARTCAR_CLIENT_ID` - **MISSING** (get from Smartcar Dashboard)
  - `SMARTCAR_CLIENT_SECRET` - **MISSING** (get from Smartcar Dashboard)
  - `SMARTCAR_REDIRECT_URI` - **MUST SET** to `https://api.nerava.network/oauth/smartcar/callback`
  - `SMARTCAR_MODE` - **MUST SET** to `live` (NOT `sandbox`)
  - `SMARTCAR_ENABLED` - **MUST SET** to `true` if using Smartcar
- **Current Status:** Defaults to `sandbox` mode
- **OAuth Flow:** Authorization code flow
- **Token Storage:** Encrypted in `vehicle_tokens` table
- **Files:**
  - `backend/app/routers/ev_smartcar.py`
  - `backend/app/services/smartcar_service.py`
  - `backend/app/services/smartcar_client.py`

#### 8. HubSpot CRM
**Status:** ✅ **OPTIONAL - PRODUCTION READY**
- **Purpose:** Lifecycle event tracking (user signup, redemptions, wallet installs)
- **Location:** `backend/app/services/hubspot.py`, `backend/app/workers/hubspot_sync.py`
- **Required Environment Variables:**
  - `HUBSPOT_ENABLED` - Default: `false` (safe default)
  - `HUBSPOT_SEND_LIVE` - Default: `false` (dry-run mode)
  - `HUBSPOT_PRIVATE_APP_TOKEN` - **MISSING** (if `HUBSPOT_SEND_LIVE=true`)
  - `HUBSPOT_PORTAL_ID` - **MISSING** (if `HUBSPOT_SEND_LIVE=true`)
- **Current Status:** Production ready, all P0 issues fixed
- **Architecture:** Async outbox pattern with retry logic and rate limiting
- **Files:**
  - `backend/app/services/hubspot.py`
  - `backend/app/workers/hubspot_sync.py`
  - `backend/app/events/hubspot_adapter.py`
- **Documentation:** `backend/README_HUBSPOT.md`

#### 9. PostHog Analytics (Backend)
**Status:** ⚠️ **OPTIONAL - REQUIRES API KEY**
- **Purpose:** Backend event tracking
- **Location:** `backend/app/services/analytics.py` (if exists)
- **Required Environment Variables:**
  - `POSTHOG_KEY` - **MISSING** (PostHog project API key)
  - `POSTHOG_HOST` - Default: `https://app.posthog.com`
- **Current Status:** May not be implemented (check `backend/app/services/analytics.py`)
- **Usage:** Referenced in `backend/app/routers/auth.py:17, 358, 374, 391, 410, 445, 494, 527, 544`

#### 10. Apple Wallet (PassKit)
**Status:** ⚠️ **OPTIONAL - REQUIRES CERTIFICATES**
- **Purpose:** Apple Wallet pass generation and push updates
- **Location:** `backend/app/routers/wallet_pass.py`, `backend/app/services/apple_wallet_pass.py`
- **Required Environment Variables:**
  - `APPLE_WALLET_SIGNING_ENABLED` - Default: `false`
  - `APPLE_WALLET_PASS_TYPE_ID` - **MISSING** (format: `pass.com.nerava.wallet`)
  - `APPLE_WALLET_TEAM_ID` - **MISSING** (Apple Developer Team ID)
  - `APPLE_WALLET_CERT_P12_PATH` - **MISSING** (path to .p12 certificate file)
  - `APPLE_WALLET_CERT_P12_PASSWORD` - **MISSING** (certificate password)
  - `APPLE_WALLET_APNS_KEY_ID` - **MISSING** (APNS key ID for push notifications)
  - `APPLE_WALLET_APNS_TEAM_ID` - **MISSING** (APNS team ID)
  - `APPLE_WALLET_APNS_AUTH_KEY_PATH` - **MISSING** (path to APNS auth key .p8 file)
- **Current Status:** Signing disabled by default
- **Validation:** `backend/app/core/config.py:202-223` - Validates config if signing enabled
- **Files:**
  - `backend/app/routers/wallet_pass.py`
  - `backend/app/services/apple_wallet_pass.py`
  - `backend/app/services/apple_pass_push.py`

#### 11. Google Wallet
**Status:** ⚠️ **PARTIAL IMPLEMENTATION**
- **Purpose:** Google Wallet pass generation
- **Location:** `backend/app/services/google_wallet_service.py` (if exists)
- **Status:** Model exists (`GoogleWalletLink` in `backend/app/models/domain.py`), endpoints unknown
- **Required:** Google Wallet API credentials (if implementing)

### Core Configuration

#### Database
- **Development:** SQLite (`sqlite:///./nerava.db`)
- **Production:** **MUST USE** PostgreSQL
- **Environment Variable:** `DATABASE_URL=postgresql://user:password@host:5432/nerava`
- **Validation:** `backend/app/core/config.py:88-110` - Fails startup if SQLite in prod
- **Migrations:** Manual (removed from startup) - **MUST RUN** `alembic upgrade head` before deployment
- **Migration Location:** `backend/alembic/versions/` (45+ migrations)

#### Redis
- **Purpose:** Rate limiting, caching, session storage
- **Environment Variable:** `REDIS_URL=redis://host:6379/0`
- **Required in Production:** Yes
- **Validation:** `backend/app/core/config.py:112-132` - Fails startup if missing in prod
- **Fallback:** In-memory (but fails validation in prod)

#### Security
- **JWT Secret:** `JWT_SECRET` - **MUST GENERATE** secure random value (NOT `dev-secret`)
- **Token Encryption:** `TOKEN_ENCRYPTION_KEY` - **MUST GENERATE** Fernet key (44 chars)
- **Validation:** `backend/app/core/config.py:297-336` - Validates secrets in production
- **CORS:** `ALLOWED_ORIGINS` - **MUST SET** to production domains (comma-separated, NO `*`)
- **Public URLs:** `PUBLIC_BASE_URL`, `FRONTEND_URL` - **MUST SET** to production domains (NOT localhost)

#### Feature Flags
- **DEMO_MODE:** **MUST SET** to `false` in production
- **MERCHANT_AUTH_MOCK:** **MUST SET** to `false` in production
- **OTP_PROVIDER:** **MUST SET** to `twilio_verify` or `twilio_sms` (NOT `stub`)
- **ENV:** **MUST SET** to `prod` in production

### Dependencies
- **Python Version:** 3.9+
- **Key Packages:** FastAPI, SQLAlchemy, Alembic, Pydantic, Stripe, Twilio, google-auth, cryptography
- **File:** `backend/requirements.txt` (200+ lines)
- **Security:** No automated vulnerability scanning found

### Deployment
- **Dockerfile:** `backend/Dockerfile` (multi-stage build)
- **Port:** 8001 (container), configurable via `PORT` env var
- **Health Checks:** `/healthz` (liveness), `/readyz` (readiness)
- **WSGI:** Gunicorn + Uvicorn workers (production)

---

## COMPONENT 2: DRIVER APP

### Architecture
- **Framework:** React 18 + TypeScript + Vite
- **Build Output:** Static files served via Nginx
- **Port:** 3001 (Docker) / 5173 (dev)
- **Deployment:** Docker container with Nginx
- **Base Path:** `/app/` (production)

### External API Integrations

#### 1. Backend API
**Status:** ⚠️ **REQUIRES PRODUCTION URL**
- **Environment Variable:** `VITE_API_BASE_URL`
- **Default:** `http://localhost:8001` (dev only)
- **Production Requirement:** **MUST SET** to `https://api.nerava.network`
- **Location:** `apps/driver/src/services/api.ts:24`
- **Build Validation:** `apps/driver/vite.config.ts:19-28` - Fails build if localhost in prod
- **Dockerfile:** `apps/driver/Dockerfile:17` - Default: `https://api.nerava.network`

#### 2. PostHog Analytics
**Status:** ⚠️ **REQUIRES API KEY**
- **Package:** `posthog-js@^1.314.0`
- **Environment Variables:**
  - `VITE_POSTHOG_KEY` - **MISSING** (PostHog project API key)
  - `VITE_POSTHOG_HOST` - Default: `https://app.posthog.com`
  - `VITE_ANALYTICS_ENABLED` - Default: `true`
- **Location:** `apps/driver/src/analytics/index.ts:47-48`
- **Dockerfile:** `apps/driver/Dockerfile:19-21, 26-28`

### Configuration

#### Mock Mode
**Status:** ✅ **VALIDATED - CANNOT ENABLE IN PROD**
- **Environment Variable:** `VITE_MOCK_MODE`
- **Default:** `false`
- **Build Validation:** `apps/driver/vite.config.ts:10-14` - Fails build if `true` in prod
- **Location:** `apps/driver/src/services/api.ts:27-29`
- **Mock Data:** `apps/driver/src/mock/` (only used if mock enabled)

#### Build Configuration
- **Base Path:** `VITE_PUBLIC_BASE=/app/` (production)
- **Environment:** `VITE_ENV=prod` (production)
- **Dockerfile:** `apps/driver/Dockerfile:16-28`

### Dependencies
- **Key Packages:** React 19, React Router, PostHog, TanStack Query, Zod
- **File:** `apps/driver/package.json`
- **Total Dependencies:** 21 (prod) + 25 (dev)

### Deployment
- **Dockerfile:** `apps/driver/Dockerfile` (multi-stage: Node builder + Nginx)
- **Health Check:** `/health` endpoint
- **Nginx Config:** `apps/driver/nginx.conf`

---

## COMPONENT 3: ADMIN CONSOLE

### Architecture
- **Framework:** React 18 + TypeScript + Vite
- **Build Output:** Static files served via Nginx
- **Port:** 3003 (Docker)
- **Deployment:** Docker container with Nginx
- **Base Path:** `/admin/` (production)

### External API Integrations

#### 1. Backend API
**Status:** ⚠️ **REQUIRES PRODUCTION URL**
- **Environment Variable:** `VITE_API_BASE_URL`
- **Default:** `http://localhost:8001` (dev only)
- **Production Requirement:** **MUST SET** to `https://api.nerava.network`
- **Location:** `apps/admin/src/services/api.ts:2`
- **Dockerfile:** `apps/admin/Dockerfile:17` - Default: `https://api.nerava.network`

#### 2. PostHog Analytics
**Status:** ⚠️ **REQUIRES API KEY**
- **Package:** `posthog-js@^1.314.0`
- **Environment Variables:**
  - `VITE_POSTHOG_KEY` - **MISSING**
  - `VITE_POSTHOG_HOST` - Default: `https://app.posthog.com`
  - `VITE_ANALYTICS_ENABLED` - Default: `true`
- **Location:** `apps/admin/src/analytics/index.ts:46-48`
- **Dockerfile:** `apps/admin/Dockerfile:19-21, 26-28`

### Configuration
- **Base Path:** `VITE_PUBLIC_BASE=/admin/` (production)
- **Environment:** `VITE_ENV=prod` (production)
- **Dockerfile:** `apps/admin/Dockerfile:16-28`

### Dependencies
- **Key Packages:** React 18, React Router, PostHog, Radix UI components, Recharts
- **File:** `apps/admin/package.json`
- **Total Dependencies:** 21 (prod) + 11 (dev)

### Deployment
- **Dockerfile:** `apps/admin/Dockerfile` (multi-stage: Node builder + Nginx)
- **Health Check:** `/health` endpoint
- **Nginx Config:** `apps/admin/nginx.conf`

---

## COMPONENT 4: MERCHANT DASHBOARD

### Architecture
- **Framework:** React 18 + TypeScript + Vite
- **Build Output:** Static files served via Nginx
- **Port:** 3002 (Docker) / 5174 (dev)
- **Deployment:** Docker container with Nginx
- **Base Path:** `/merchant/` (production)

### External API Integrations

#### 1. Backend API
**Status:** ⚠️ **REQUIRES PRODUCTION URL**
- **Environment Variable:** `VITE_API_BASE_URL`
- **Default:** `http://localhost:8001` (dev only)
- **Production Requirement:** **MUST SET** to `https://api.nerava.network`
- **Location:** `apps/merchant/app/services/api.ts:2`
- **Dockerfile:** `apps/merchant/Dockerfile:17` - Default: `https://api.nerava.network`

#### 2. PostHog Analytics
**Status:** ⚠️ **REQUIRES API KEY**
- **Package:** `posthog-js@^1.314.0`
- **Environment Variables:**
  - `VITE_POSTHOG_KEY` - **MISSING**
  - `VITE_POSTHOG_HOST` - Default: `https://app.posthog.com`
  - `VITE_ANALYTICS_ENABLED` - Default: `true`
- **Location:** `apps/merchant/app/analytics/index.ts:46-48`
- **Dockerfile:** `apps/merchant/Dockerfile:19-21, 26-28`

### Configuration
- **Base Path:** `VITE_PUBLIC_BASE=/merchant/` (production)
- **Environment:** `VITE_ENV=prod` (production)
- **Dockerfile:** `apps/merchant/Dockerfile:16-28`

### Dependencies
- **Key Packages:** React 18, React Router, PostHog, Radix UI components, Recharts
- **File:** `apps/merchant/package.json`
- **Total Dependencies:** 21 (prod) + 11 (dev)

### Deployment
- **Dockerfile:** `apps/merchant/Dockerfile` (multi-stage: Node builder + Nginx)
- **Health Check:** `/health` endpoint
- **Nginx Config:** `apps/merchant/nginx.conf`

---

## COMPONENT 5: LANDING PAGE

### Architecture
- **Framework:** Next.js 14+ (App Router)
- **Build Output:** Node.js server + static files
- **Port:** 3000
- **Deployment:** Docker container with Node.js runtime
- **Base Path:** Configurable via `NEXT_PUBLIC_BASE_PATH`

### External API Integrations

#### 1. PostHog Analytics
**Status:** ⚠️ **REQUIRES API KEY**
- **Package:** `posthog-js@^1.314.0`
- **Environment Variables:**
  - `NEXT_PUBLIC_POSTHOG_KEY` - **MISSING**
  - `NEXT_PUBLIC_POSTHOG_HOST` - Default: `https://app.posthog.com`
  - `NEXT_PUBLIC_ANALYTICS_ENABLED` - Default: `true`
- **Location:** Check `apps/landing/app/analytics/` (if exists)
- **Dockerfile:** `apps/landing/Dockerfile:18-20, 25-27`

#### 2. Driver App URL
**Status:** ⚠️ **REQUIRES PRODUCTION URL**
- **Environment Variable:** `NEXT_PUBLIC_DRIVER_APP_URL`
- **Default:** `http://localhost:5173` (dev only)
- **Production Requirement:** **MUST SET** to `https://app.nerava.network`
- **Location:** `apps/landing/app/components/v2/ctaLinks.ts:22-36`
- **Dockerfile:** `apps/landing/Dockerfile:21, 28`

#### 3. Merchant App URL
**Status:** ⚠️ **REQUIRES PRODUCTION URL**
- **Environment Variable:** `NEXT_PUBLIC_MERCHANT_APP_URL`
- **Default:** `http://localhost:5174` (dev only)
- **Production Requirement:** **MUST SET** to `https://merchant.nerava.network`
- **Location:** `apps/landing/app/components/v2/ctaLinks.ts:43-57`
- **Dockerfile:** `apps/landing/Dockerfile:22, 29`

#### 4. Charger Portal URL
**Status:** ⚠️ **OPTIONAL**
- **Environment Variable:** `NEXT_PUBLIC_CHARGER_PORTAL_URL`
- **Default:** Falls back to Google Form
- **Production Requirement:** Set if charger portal exists
- **Location:** `apps/landing/app/components/v2/ctaLinks.ts:63-71`
- **Dockerfile:** `apps/landing/Dockerfile:23, 30`

### Configuration
- **Base Path:** `NEXT_PUBLIC_BASE_PATH` (optional, for subdirectory deployment)
- **Dockerfile:** `apps/landing/Dockerfile:17-30`

### Dependencies
- **Key Packages:** Next.js 14, React 18, PostHog
- **File:** `apps/landing/package.json`
- **Total Dependencies:** 4 (prod) + 6 (dev)

### Deployment
- **Dockerfile:** `apps/landing/Dockerfile` (multi-stage: Node builder + Node runner)
- **Standalone Build:** Next.js standalone output
- **User:** Non-root user (nextjs:nodejs)

---

## COMPLETE API KEYS & CREDENTIALS CHECKLIST

### Critical (Must Have for Launch)

1. **Twilio OTP**
   - [ ] `TWILIO_ACCOUNT_SID`
   - [ ] `TWILIO_AUTH_TOKEN`
   - [ ] `TWILIO_VERIFY_SERVICE_SID` (if using `twilio_verify`)
   - [ ] `OTP_FROM_NUMBER` (if using `twilio_sms`)
   - [ ] `OTP_PROVIDER=twilio_verify` or `twilio_sms`

2. **Google OAuth (Merchant Onboarding)**
   - [ ] `GOOGLE_CLIENT_ID`
   - [ ] `GOOGLE_CLIENT_SECRET`
   - [ ] `GOOGLE_OAUTH_REDIRECT_URI`
   - [ ] `MERCHANT_AUTH_MOCK=false`

3. **Google Places API**
   - [ ] `GOOGLE_PLACES_API_KEY`
   - [ ] Enable "Places API" in Google Cloud Console
   - [ ] Enable "Distance Matrix API" in Google Cloud Console

4. **NREL API**
   - [ ] `NREL_API_KEY` (free from https://developer.nrel.gov/signup/)

5. **Square (Production)**
   - [ ] `SQUARE_ENV=production`
   - [ ] `SQUARE_APPLICATION_ID_PRODUCTION`
   - [ ] `SQUARE_APPLICATION_SECRET_PRODUCTION`
   - [ ] `SQUARE_REDIRECT_URL_PRODUCTION`
   - [ ] `SQUARE_WEBHOOK_SIGNATURE_KEY`
   - [ ] Configure webhook endpoint in Square Dashboard

6. **Stripe (Live)**
   - [ ] `STRIPE_SECRET_KEY` (must be `sk_live_...` NOT `sk_test_...`)
   - [ ] `STRIPE_WEBHOOK_SECRET` (format: `whsec_...`)
   - [ ] Configure webhook endpoint in Stripe Dashboard

7. **Smartcar (Live)**
   - [ ] `SMARTCAR_CLIENT_ID`
   - [ ] `SMARTCAR_CLIENT_SECRET`
   - [ ] `SMARTCAR_REDIRECT_URI`
   - [ ] `SMARTCAR_MODE=live`

8. **PostHog Analytics**
   - [ ] `VITE_POSTHOG_KEY` (for driver, merchant, admin apps)
   - [ ] `NEXT_PUBLIC_POSTHOG_KEY` (for landing page)
   - [ ] `POSTHOG_KEY` (for backend, if implemented)

### Optional (Can Enable Later)

9. **HubSpot CRM**
   - [ ] `HUBSPOT_ENABLED=true` (if using)
   - [ ] `HUBSPOT_SEND_LIVE=true` (if using)
   - [ ] `HUBSPOT_PRIVATE_APP_TOKEN`
   - [ ] `HUBSPOT_PORTAL_ID`

10. **Apple Wallet**
    - [ ] `APPLE_WALLET_SIGNING_ENABLED=true` (if using)
    - [ ] `APPLE_WALLET_PASS_TYPE_ID`
    - [ ] `APPLE_WALLET_TEAM_ID`
    - [ ] `APPLE_WALLET_CERT_P12_PATH`
    - [ ] `APPLE_WALLET_CERT_P12_PASSWORD`
    - [ ] `APPLE_WALLET_APNS_KEY_ID`
    - [ ] `APPLE_WALLET_APNS_TEAM_ID`
    - [ ] `APPLE_WALLET_APNS_AUTH_KEY_PATH`

---

## COMPLETE ENVIRONMENT VARIABLES CHECKLIST

### Backend (50+ variables)

#### Database & Infrastructure
- [ ] `DATABASE_URL=postgresql://user:password@host:5432/nerava` (NOT SQLite)
- [ ] `REDIS_URL=redis://host:6379/0`
- [ ] `ENV=prod`

#### Security
- [ ] `JWT_SECRET=<secure_random_secret>` (generate with Fernet)
- [ ] `TOKEN_ENCRYPTION_KEY=<secure_random_key>` (44-char Fernet key)
- [ ] `ALLOWED_ORIGINS=https://app.nerava.network,https://www.nerava.network,https://merchant.nerava.network,https://admin.nerava.network` (NO `*`)
- [ ] `PUBLIC_BASE_URL=https://api.nerava.network` (NOT localhost)
- [ ] `FRONTEND_URL=https://app.nerava.network` (NOT localhost)

#### Feature Flags
- [ ] `DEMO_MODE=false`
- [ ] `MERCHANT_AUTH_MOCK=false`
- [ ] `OTP_PROVIDER=twilio_verify` or `twilio_sms` (NOT `stub`)

#### Twilio
- [ ] `TWILIO_ACCOUNT_SID`
- [ ] `TWILIO_AUTH_TOKEN`
- [ ] `TWILIO_VERIFY_SERVICE_SID` (if using `twilio_verify`)
- [ ] `OTP_FROM_NUMBER` (if using `twilio_sms`)

#### Google
- [ ] `GOOGLE_CLIENT_ID`
- [ ] `GOOGLE_CLIENT_SECRET`
- [ ] `GOOGLE_OAUTH_REDIRECT_URI`
- [ ] `GOOGLE_PLACES_API_KEY`

#### Square
- [ ] `SQUARE_ENV=production`
- [ ] `SQUARE_APPLICATION_ID_PRODUCTION`
- [ ] `SQUARE_APPLICATION_SECRET_PRODUCTION`
- [ ] `SQUARE_REDIRECT_URL_PRODUCTION`
- [ ] `SQUARE_WEBHOOK_SIGNATURE_KEY`

#### Stripe
- [ ] `STRIPE_SECRET_KEY=sk_live_...`
- [ ] `STRIPE_WEBHOOK_SECRET=whsec_...`
- [ ] `STRIPE_CONNECT_CLIENT_ID` (optional)

#### Smartcar
- [ ] `SMARTCAR_CLIENT_ID`
- [ ] `SMARTCAR_CLIENT_SECRET`
- [ ] `SMARTCAR_REDIRECT_URI`
- [ ] `SMARTCAR_MODE=live`
- [ ] `SMARTCAR_ENABLED=true` (if using)

#### NREL
- [ ] `NREL_API_KEY`

#### PostHog (Backend)
- [ ] `POSTHOG_KEY` (if backend analytics enabled)
- [ ] `POSTHOG_HOST=https://app.posthog.com`

#### HubSpot (Optional)
- [ ] `HUBSPOT_ENABLED=true` (if using)
- [ ] `HUBSPOT_SEND_LIVE=true` (if using)
- [ ] `HUBSPOT_PRIVATE_APP_TOKEN`
- [ ] `HUBSPOT_PORTAL_ID`

#### Apple Wallet (Optional)
- [ ] `APPLE_WALLET_SIGNING_ENABLED=true` (if using)
- [ ] `APPLE_WALLET_PASS_TYPE_ID`
- [ ] `APPLE_WALLET_TEAM_ID`
- [ ] `APPLE_WALLET_CERT_P12_PATH`
- [ ] `APPLE_WALLET_CERT_P12_PASSWORD`
- [ ] `APPLE_WALLET_APNS_KEY_ID`
- [ ] `APPLE_WALLET_APNS_TEAM_ID`
- [ ] `APPLE_WALLET_APNS_AUTH_KEY_PATH`

### Driver App Build Args
- [ ] `VITE_API_BASE_URL=https://api.nerava.network`
- [ ] `VITE_POSTHOG_KEY`
- [ ] `VITE_POSTHOG_HOST=https://app.posthog.com`
- [ ] `VITE_ANALYTICS_ENABLED=true`
- [ ] `VITE_PUBLIC_BASE=/app/`
- [ ] `VITE_ENV=prod`
- [ ] `VITE_MOCK_MODE=false` (enforced by build)

### Admin App Build Args
- [ ] `VITE_API_BASE_URL=https://api.nerava.network`
- [ ] `VITE_POSTHOG_KEY`
- [ ] `VITE_POSTHOG_HOST=https://app.posthog.com`
- [ ] `VITE_ANALYTICS_ENABLED=true`
- [ ] `VITE_PUBLIC_BASE=/admin/`
- [ ] `VITE_ENV=prod`

### Merchant App Build Args
- [ ] `VITE_API_BASE_URL=https://api.nerava.network`
- [ ] `VITE_POSTHOG_KEY`
- [ ] `VITE_POSTHOG_HOST=https://app.posthog.com`
- [ ] `VITE_ANALYTICS_ENABLED=true`
- [ ] `VITE_PUBLIC_BASE=/merchant/`
- [ ] `VITE_ENV=prod`

### Landing Page Build Args
- [ ] `NEXT_PUBLIC_POSTHOG_KEY`
- [ ] `NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com`
- [ ] `NEXT_PUBLIC_ANALYTICS_ENABLED=true`
- [ ] `NEXT_PUBLIC_DRIVER_APP_URL=https://app.nerava.network`
- [ ] `NEXT_PUBLIC_MERCHANT_APP_URL=https://merchant.nerava.network`
- [ ] `NEXT_PUBLIC_CHARGER_PORTAL_URL` (optional)
- [ ] `NEXT_PUBLIC_BASE_PATH` (optional, for subdirectory)

---

## PRODUCTION BLOCKERS

### P0 - Must Fix Before Launch

1. **Database Migration Strategy**
   - **Issue:** Migrations removed from startup (`backend/app/main_simple.py:293-305`)
   - **Risk:** Multi-instance deployments will race on migrations
   - **Fix:** Run migrations in separate init container or job before app starts
   - **Action:** Create migration job/init container

2. **OTP Provider in Stub Mode**
   - **Issue:** Defaults to `stub` mode (accepts `000000` for any phone)
   - **Risk:** No real phone verification
   - **Fix:** Set `OTP_PROVIDER=twilio_verify` or `twilio_sms` + provide credentials
   - **Validation:** Already exists in `backend/app/core/config.py:242-267`

3. **Mock Modes Enabled**
   - **Issue:** `MERCHANT_AUTH_MOCK=true`, `DEMO_MODE=true` by default
   - **Risk:** Fake OAuth flows, relaxed time restrictions
   - **Fix:** Set both to `false` in production
   - **Validation:** Already exists in `backend/app/core/config.py:285-295`

4. **SQLite Database**
   - **Issue:** Defaults to SQLite in development
   - **Risk:** Not suitable for production
   - **Fix:** Set `DATABASE_URL=postgresql://...` in production
   - **Validation:** Already exists in `backend/app/core/config.py:88-110`

5. **CORS Wildcard**
   - **Issue:** Defaults to `ALLOWED_ORIGINS=*`
   - **Risk:** Security vulnerability
   - **Fix:** Set to explicit production domains
   - **Validation:** Already exists in `backend/app/core/config.py:784-802`

### P1 - High Priority (Should Fix)

6. **Hardcoded API Key**
   - **Issue:** Google Places API key hardcoded in `backend/app/scripts/analyze_texas_chargers.py:33`
   - **Risk:** Key exposure in code
   - **Fix:** Remove hardcoded key, use environment variable

7. **Missing Webhook Signature Verification**
   - **Issue:** Square webhooks only check secret header, not signature
   - **Risk:** Webhook spoofing if secret leaked
   - **Fix:** Implement Square signature verification (HMAC-SHA256)

8. **Purchase Webhook Replay Protection**
   - **Issue:** No timestamp validation on purchase webhooks
   - **Risk:** Old webhooks can be replayed indefinitely
   - **Fix:** Add 5-minute replay window (like Stripe webhooks)

9. **Wallet Balance Constraint**
   - **Issue:** No DB constraint preventing negative balances
   - **Risk:** Application bug could create negative balance
   - **Fix:** Add `CHECK (nova_balance >= 0)` constraint

10. **Frontend Config Injection**
    - **Issue:** API URLs hardcoded at build time
    - **Risk:** Requires rebuild for different environments
    - **Fix:** Consider runtime config injection via `/v1/config` endpoint

---

## DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] **Database:** Migrate from SQLite to PostgreSQL
- [ ] **Migrations:** Run `alembic upgrade head` manually (or via init container)
- [ ] **Secrets:** Generate new `JWT_SECRET` and `TOKEN_ENCRYPTION_KEY`
- [ ] **API Keys:** Obtain all 8+ API keys listed above
- [ ] **Environment Variables:** Set all 50+ production env vars
- [ ] **CORS:** Update `ALLOWED_ORIGINS` to production domains
- [ ] **URLs:** Update all `PUBLIC_BASE_URL`, `FRONTEND_URL` to production domains
- [ ] **Mock Flags:** Disable all mock modes (`OTP_PROVIDER`, `MERCHANT_AUTH_MOCK`, `DEMO_MODE`)

### Build Configuration

- [ ] **Driver App:** Set `VITE_API_BASE_URL`, `VITE_POSTHOG_KEY`, `VITE_MOCK_MODE=false`
- [ ] **Merchant App:** Set `VITE_API_BASE_URL`, `VITE_POSTHOG_KEY`
- [ ] **Admin App:** Set `VITE_API_BASE_URL`, `VITE_POSTHOG_KEY`
- [ ] **Landing Page:** Set `NEXT_PUBLIC_DRIVER_APP_URL`, `NEXT_PUBLIC_MERCHANT_APP_URL`, `NEXT_PUBLIC_POSTHOG_KEY`

### Infrastructure

- [ ] **Backend Container:** ECS Fargate / Kubernetes / App Runner
- [ ] **RDS PostgreSQL:** Multi-AZ for high availability
- [ ] **ElastiCache Redis:** For rate limiting and caching
- [ ] **Secrets Manager:** Store all API keys and secrets (AWS Secrets Manager / HashiCorp Vault)
- [ ] **ALB:** Load balancer with TLS termination (ACM certificate)
- [ ] **Route 53:** DNS configuration
- [ ] **CloudWatch:** Logging and monitoring
- [ ] **Frontend CDN:** CloudFront / Cloudflare for static assets

### Post-Deployment Validation

- [ ] **Health Checks:** Verify `/healthz` and `/readyz` endpoints respond
- [ ] **OTP:** Test phone verification with real Twilio
- [ ] **OAuth:** Test Google Business Profile OAuth flow
- [ ] **API:** Verify all frontend apps can connect to backend
- [ ] **Analytics:** Verify PostHog events are tracking
- [ ] **CORS:** Verify CORS headers allow only production domains
- [ ] **Database:** Verify PostgreSQL connection and migrations
- [ ] **Secrets:** Verify no secrets are logged or exposed
- [ ] **Webhooks:** Test Stripe and Square webhook endpoints
- [ ] **Smartcar:** Test vehicle connection flow (if enabled)

---

## SECURITY CHECKLIST

- [ ] **JWT Secret:** Not default value, not equal to `DATABASE_URL`
- [ ] **Token Encryption Key:** Valid Fernet key (44 chars), not example value
- [ ] **CORS:** No wildcard (`*`), explicit production domains only
- [ ] **OTP Provider:** Not `stub` mode
- [ ] **Mock Modes:** All disabled (`MERCHANT_AUTH_MOCK=false`, `DEMO_MODE=false`)
- [ ] **Database:** PostgreSQL (not SQLite)
- [ ] **Redis:** Required and validated in production
- [ ] **Public URLs:** No localhost references
- [ ] **Secrets:** Stored in secrets manager (not plain env vars)
- [ ] **Webhook Signatures:** Stripe verified, Square needs implementation
- [ ] **Rate Limiting:** Redis-backed (not in-memory fallback)
- [ ] **HTTPS:** All endpoints use TLS
- [ ] **Database Backups:** Automated daily backups configured
- [ ] **Logging:** No secrets logged, PII sanitization

---

## MONITORING & OBSERVABILITY

### Current Status
- ✅ **Health Checks:** `/healthz` (liveness), `/readyz` (readiness)
- ✅ **Basic Logging:** Python logging, request/response middleware
- ⚠️ **Metrics:** Prometheus client installed but no endpoints found
- ⚠️ **APM:** No Datadog/New Relic integration found
- ⚠️ **Error Tracking:** No Sentry integration found
- ⚠️ **Correlation IDs:** No request correlation IDs found

### Recommended Additions
- [ ] **Prometheus Metrics:** Expose `/metrics` endpoint
- [ ] **APM Integration:** Datadog or New Relic
- [ ] **Error Tracking:** Sentry for exception tracking
- [ ] **Correlation IDs:** Add `X-Request-ID` middleware
- [ ] **PII Sanitization:** Sanitize email, tokens in logs
- [ ] **Structured Logging:** JSON format for log aggregation
- [ ] **Alerts:** CloudWatch alarms for error rate, latency, availability

---

## DEPENDENCY VULNERABILITIES

### Current Status
- ⚠️ **No automated scanning found:** No Dependabot, Snyk, or npm audit automation
- ⚠️ **Manual audit files exist:** `npm-audit-*.json` files found but not automated

### Recommended Actions
- [ ] **Enable Dependabot:** For GitHub dependency updates
- [ ] **Run npm audit:** For frontend dependencies
- [ ] **Run pip-audit:** For Python dependencies
- [ ] **Review audit results:** Fix high/critical vulnerabilities

---

## SUMMARY STATISTICS

- **Total Components:** 5 (Backend, Driver, Admin, Merchant, Landing)
- **Total External APIs:** 12 (Twilio, Google OAuth, Google Places, NREL, Square, Stripe, Smartcar, HubSpot, PostHog, Apple Wallet, Google Wallet, Backend API)
- **Total Environment Variables:** 50+
- **API Keys Required:** 8+ (Twilio, Google OAuth, Google Places, NREL, Square, Stripe, Smartcar, PostHog)
- **Production Blockers:** 5 (Database, OTP, Mock Modes, CORS, Migrations)
- **High Priority Issues:** 5 (Hardcoded keys, Webhook security, Replay protection, DB constraints, Config injection)
- **Mock Modes to Disable:** 3 (OTP stub, Merchant auth mock, Demo mode)
- **Dockerfiles:** 5 (Backend, Driver, Admin, Merchant, Landing)
- **Database Migrations:** 45+ (manual execution required)

---

## FILES REFERENCE

### Configuration Files
- `ENV.example` - Environment variables template
- `backend/app/core/config.py` - Backend configuration with validation
- `backend/app/config.py` - Legacy backend configuration
- `apps/*/Dockerfile` - Frontend build configurations
- `backend/Dockerfile` - Backend build configuration

### Integration Files
- `backend/app/services/hubspot.py` - HubSpot client
- `backend/app/services/google_places_new.py` - Google Places client
- `backend/app/services/smartcar_service.py` - Smartcar client
- `backend/app/services/square_service.py` - Square client
- `backend/app/services/stripe_service.py` - Stripe client
- `backend/app/services/auth/twilio_verify.py` - Twilio Verify provider
- `backend/app/services/auth/twilio_sms.py` - Twilio SMS provider
- `backend/app/services/auth/stub_provider.py` - Stub OTP provider (dev only)

### Documentation Files
- `PRODUCTION_READINESS_REPORT.md` - Previous production readiness report
- `PROD_QUALITY_GATE.md` - Quality gate analysis
- `HUBSPOT_INTEGRATION_REPORT.md` - HubSpot integration status
- `NERAVA_CURRENT_STATE.md` - Current state analysis

---

**END OF DOCUMENT**



