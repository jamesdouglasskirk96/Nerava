# Nerava Production Readiness Report
## Comprehensive Technical Analysis for AWS Deployment

**Report Date**: 2025-01-XX  
**Target**: AWS Production Deployment  
**Components Analyzed**: 5 (Backend, Driver App, Merchant Portal, Admin Portal, Landing Page)  
**Audience**: ChatGPT Code Review System

---

## Executive Summary

This report identifies **all API keys required**, **all mocked code locations**, **hardcoded values**, and **production configuration gaps** across all 5 components. Each issue includes **specific file paths**, **line numbers**, **code examples**, and **exact remediation steps**.

### Critical Production Blockers

1. **OTP Provider**: Currently defaults to `stub` mode - **MUST** be set to `twilio_verify` or `twilio_sms` in production
2. **Mock Mode Flags**: Multiple components have mock modes that **MUST** be disabled
3. **API Keys**: 15+ API keys missing from production configuration
4. **Environment Variables**: 30+ environment variables need production values
5. **CORS Configuration**: Currently allows `*` - **MUST** be restricted to production domains
6. **Database**: SQLite default - **MUST** use PostgreSQL in production
7. **Demo Mode**: Enabled by default - **MUST** be disabled

---

## Component 1: Backend API (`backend/`)

### Architecture
- **Framework**: FastAPI (Python 3.9+)
- **Entry Point**: `backend/app/main_simple.py`
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Deployment**: Docker container on port 8001

### API Keys Required (From You)

#### 1. Twilio OTP Service
**Location**: `backend/app/core/config.py:91-96`

**Required Variables**:
```python
TWILIO_ACCOUNT_SID=<your_twilio_account_sid>
TWILIO_AUTH_TOKEN=<your_twilio_auth_token>
TWILIO_VERIFY_SERVICE_SID=<your_twilio_verify_service_sid>  # If using twilio_verify
OTP_FROM_NUMBER=<your_twilio_phone_number>  # If using twilio_sms
OTP_PROVIDER=twilio_verify  # OR twilio_sms (NOT stub)
```

**Current Code**:
```python
# backend/app/core/config.py:91-96
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_VERIFY_SERVICE_SID: str = os.getenv("TWILIO_VERIFY_SERVICE_SID", "")
OTP_FROM_NUMBER: str = os.getenv("OTP_FROM_NUMBER", "")
OTP_PROVIDER: str = os.getenv("OTP_PROVIDER", "stub")  # ⚠️ DEFAULT IS STUB
```

**Action Required**: Set `OTP_PROVIDER=twilio_verify` or `twilio_sms` and provide all Twilio credentials.

**Validation**: `backend/app/core/config.py:223-248` validates OTP config in production and will **fail startup** if `OTP_PROVIDER=stub` in production.

---

#### 2. Google OAuth (Merchant Onboarding)
**Location**: `backend/app/core/config.py:50`, `backend/app/services/google_business_profile.py:18-20`

**Required Variables**:
```python
GOOGLE_CLIENT_ID=<your_google_oauth_client_id>
GOOGLE_CLIENT_SECRET=<your_google_oauth_client_secret>
MERCHANT_AUTH_MOCK=false  # ⚠️ MUST BE FALSE IN PRODUCTION
```

**Current Code**:
```python
# backend/app/core/config.py:50
MERCHANT_AUTH_MOCK: bool = os.getenv("MERCHANT_AUTH_MOCK", "false").lower() == "true"

# backend/app/services/google_business_profile.py:18-20
import os
MERCHANT_AUTH_MOCK = os.getenv("MERCHANT_AUTH_MOCK", "false").lower() == "true"
```

**Mock Implementation**:
```python
# backend/app/services/google_business_profile.py:40-42
if MERCHANT_AUTH_MOCK:
    # In mock mode, return a fake URL
    return f"http://localhost:8001/mock-oauth-callback?state={state}"

# backend/app/services/google_business_profile.py:70-77
if MERCHANT_AUTH_MOCK:
    # In mock mode, return fake tokens
    return {
        "access_token": f"mock_access_token_{secrets.token_urlsafe(16)}",
        "refresh_token": f"mock_refresh_token_{secrets.token_urlsafe(16)}",
        "expires_in": "3600",
        "token_type": "Bearer",
    }
```

**Action Required**: 
1. Set `MERCHANT_AUTH_MOCK=false` in production
2. Provide `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` from Google Cloud Console
3. Configure OAuth redirect URI: `https://<your-merchant-domain>/merchant/auth/google/callback`

---

#### 3. Google Places API
**Location**: `ENV.example:85`

**Required Variables**:
```python
GOOGLE_PLACES_API_KEY=<your_google_places_api_key>
```

**Current Code**: Referenced in `backend/app/services/google_places_new.py` but not validated in config.

**Action Required**: Get API key from Google Cloud Console with Places API and Distance Matrix API enabled.

---

#### 4. NREL API (Charger Data)
**Location**: `ENV.example:82`

**Required Variables**:
```python
NREL_API_KEY=<your_nrel_api_key>
```

**Action Required**: Get free API key from https://developer.nrel.gov/signup/

---

#### 5. Square API (Merchant Payments)
**Location**: `backend/app/core/config.py:66-84`

**Required Variables**:
```python
SQUARE_ENV=production  # NOT sandbox
SQUARE_APPLICATION_ID_PRODUCTION=<your_square_app_id>
SQUARE_APPLICATION_SECRET_PRODUCTION=<your_square_app_secret>
SQUARE_REDIRECT_URL_PRODUCTION=https://<your-backend-domain>/v1/merchants/square/callback
SQUARE_WEBHOOK_SIGNATURE_KEY=<your_square_webhook_signature_key>
```

**Current Code**:
```python
# backend/app/core/config.py:66-84
square_env: str = os.getenv("SQUARE_ENV", "sandbox")  # ⚠️ DEFAULT IS SANDBOX
square_application_id_production: str = os.getenv("SQUARE_APPLICATION_ID_PRODUCTION", "")
square_application_secret_production: str = os.getenv("SQUARE_APPLICATION_SECRET_PRODUCTION", "")
square_redirect_url_production: str = os.getenv("SQUARE_REDIRECT_URL_PRODUCTION", "")
square_webhook_signature_key: str = os.getenv("SQUARE_WEBHOOK_SIGNATURE_KEY", "")
```

**Action Required**: 
1. Set `SQUARE_ENV=production`
2. Get production credentials from Square Developer Dashboard
3. Configure webhook endpoint in Square Dashboard

---

#### 6. Stripe (Payouts)
**Location**: `backend/app/core/config.py:60-63`

**Required Variables**:
```python
STRIPE_SECRET_KEY=sk_live_<your_stripe_live_secret_key>  # NOT sk_test_
STRIPE_WEBHOOK_SECRET=whsec_<your_stripe_webhook_secret>
STRIPE_CONNECT_CLIENT_ID=ca_<your_stripe_connect_client_id>  # Optional
```

**Current Code**:
```python
# backend/app/core/config.py:60-63
stripe_secret: str = os.getenv("STRIPE_SECRET", "")
stripe_connect_client_id: str = os.getenv("STRIPE_CONNECT_CLIENT_ID", "")
stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
```

**Action Required**: Get live Stripe keys from Stripe Dashboard (not test keys).

---

#### 7. Smartcar (EV Telemetry)
**Location**: `backend/app/core/config.py:136-143`

**Required Variables**:
```python
SMARTCAR_CLIENT_ID=<your_smartcar_client_id>
SMARTCAR_CLIENT_SECRET=<your_smartcar_client_secret>
SMARTCAR_REDIRECT_URI=https://<your-backend-domain>/oauth/smartcar/callback
SMARTCAR_MODE=live  # NOT sandbox
```

**Current Code**:
```python
# backend/app/core/config.py:136-143
smartcar_client_id: str = os.getenv("SMARTCAR_CLIENT_ID", "")
smartcar_client_secret: str = os.getenv("SMARTCAR_CLIENT_SECRET", "")
smartcar_redirect_uri: str = os.getenv("SMARTCAR_REDIRECT_URI", "")
smartcar_mode: str = os.getenv("SMARTCAR_MODE", "sandbox")  # ⚠️ DEFAULT IS SANDBOX
```

**Action Required**: Get live Smartcar credentials and set `SMARTCAR_MODE=live`.

---

#### 8. PostHog Analytics (Backend Events)
**Location**: Not currently configured in backend

**Required Variables**:
```python
POSTHOG_API_KEY=<your_posthog_api_key>
POSTHOG_HOST=https://app.posthog.com
```

**Action Required**: Add PostHog backend SDK if backend events need tracking.

---

### Mocked Code Locations

#### 1. OTP Stub Provider
**Location**: `backend/app/services/auth/stub_provider.py`

**Code**:
```python
# backend/app/services/auth/stub_provider.py:21
STUB_CODE = "000000"

# backend/app/services/auth/stub_provider.py:75
is_valid = code == self.STUB_CODE
```

**Impact**: Accepts code `000000` for any phone number if `OTP_PROVIDER=stub`.

**Action Required**: **MUST** set `OTP_PROVIDER=twilio_verify` or `twilio_sms` in production. Validation in `backend/app/core/config.py:225` will prevent startup if stub is used in production.

---

#### 2. Google Business Profile Mock
**Location**: `backend/app/services/google_business_profile.py:40-42, 70-77, 113-137`

**Code**:
```python
# backend/app/services/google_business_profile.py:40-42
if MERCHANT_AUTH_MOCK:
    return f"http://localhost:8001/mock-oauth-callback?state={state}"

# backend/app/services/google_business_profile.py:70-77
if MERCHANT_AUTH_MOCK:
    return {
        "access_token": f"mock_access_token_{secrets.token_urlsafe(16)}",
        "refresh_token": f"mock_refresh_token_{secrets.token_urlsafe(16)}",
        ...
    }

# backend/app/services/google_business_profile.py:113-137
if MERCHANT_AUTH_MOCK:
    # Returns seeded fake locations
    return [
        {
            "locationId": "mock_location_1",
            "storeName": "Mock Business 1",
            ...
        }
    ]
```

**Impact**: Returns fake OAuth URLs, tokens, and business locations if `MERCHANT_AUTH_MOCK=true`.

**Action Required**: Set `MERCHANT_AUTH_MOCK=false` in production.

---

#### 3. Demo Mode
**Location**: `backend/app/core/config.py:103-104`

**Code**:
```python
# backend/app/core/config.py:103-104
DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
DEMO_ADMIN_KEY: str = os.getenv("DEMO_ADMIN_KEY", "")
```

**Impact**: Relaxes time window restrictions for testing if enabled.

**Action Required**: Set `DEMO_MODE=false` in production.

---

### Hardcoded Values That Need Environment Variables

#### 1. Database URL
**Location**: `backend/app/core/config.py:9`

**Current Code**:
```python
database_url: str = "sqlite:///./nerava.db"  # ⚠️ SQLITE DEFAULT
```

**Action Required**: Set `DATABASE_URL=postgresql://user:password@host:5432/nerava` in production.

---

#### 2. CORS Origins
**Location**: `backend/app/core/config.py:27`

**Current Code**:
```python
cors_allow_origins: str = os.getenv("ALLOWED_ORIGINS", "*")  # ⚠️ ALLOWS ALL
```

**Action Required**: Set `ALLOWED_ORIGINS=https://app.nerava.com,https://www.nerava.com,https://merchant.nerava.com,https://admin.nerava.com` (comma-separated, no spaces).

---

#### 3. Public Base URL
**Location**: `backend/app/core/config.py:30`

**Current Code**:
```python
public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8001")  # ⚠️ LOCALHOST
```

**Action Required**: Set `PUBLIC_BASE_URL=https://api.nerava.com` (your production API domain).

---

#### 4. Frontend URL
**Location**: `backend/app/core/config.py:33`

**Current Code**:
```python
frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:8001/app")  # ⚠️ LOCALHOST
```

**Action Required**: Set `FRONTEND_URL=https://app.nerava.com` (your production driver app domain).

---

#### 5. JWT Secret
**Location**: `backend/app/core/config.py:53`

**Current Code**:
```python
jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret")  # ⚠️ INSECURE DEFAULT
```

**Action Required**: Generate secure secret:
```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```
Set `JWT_SECRET=<generated_secret>`.

---

#### 6. Token Encryption Key
**Location**: `ENV.example:66`

**Current Code**:
```python
TOKEN_ENCRYPTION_KEY=TaHJDO442DD22r5y-jQYw_ig0MUouqbA0LjCS7e9C2M=  # ⚠️ EXAMPLE KEY
```

**Action Required**: Generate new key:
```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```
Set `TOKEN_ENCRYPTION_KEY=<generated_key>`.

---

### Production Environment Variables Summary

**Required for Backend**:
```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/nerava

# Security
JWT_SECRET=<secure_random_secret>
TOKEN_ENCRYPTION_KEY=<secure_random_key>
OTP_PROVIDER=twilio_verify  # OR twilio_sms

# Twilio
TWILIO_ACCOUNT_SID=<your_twilio_account_sid>
TWILIO_AUTH_TOKEN=<your_twilio_auth_token>
TWILIO_VERIFY_SERVICE_SID=<your_twilio_verify_service_sid>

# Google
GOOGLE_CLIENT_ID=<your_google_oauth_client_id>
GOOGLE_CLIENT_SECRET=<your_google_oauth_client_secret>
GOOGLE_PLACES_API_KEY=<your_google_places_api_key>
MERCHANT_AUTH_MOCK=false

# Square
SQUARE_ENV=production
SQUARE_APPLICATION_ID_PRODUCTION=<your_square_app_id>
SQUARE_APPLICATION_SECRET_PRODUCTION=<your_square_app_secret>
SQUARE_REDIRECT_URL_PRODUCTION=https://api.nerava.com/v1/merchants/square/callback
SQUARE_WEBHOOK_SIGNATURE_KEY=<your_square_webhook_signature_key>

# Stripe
STRIPE_SECRET_KEY=sk_live_<your_stripe_live_secret_key>
STRIPE_WEBHOOK_SECRET=whsec_<your_stripe_webhook_secret>
STRIPE_CONNECT_CLIENT_ID=ca_<your_stripe_connect_client_id>

# Smartcar
SMARTCAR_CLIENT_ID=<your_smartcar_client_id>
SMARTCAR_CLIENT_SECRET=<your_smartcar_client_secret>
SMARTCAR_REDIRECT_URI=https://api.nerava.com/oauth/smartcar/callback
SMARTCAR_MODE=live

# NREL
NREL_API_KEY=<your_nrel_api_key>

# URLs
PUBLIC_BASE_URL=https://api.nerava.com
FRONTEND_URL=https://app.nerava.com
ALLOWED_ORIGINS=https://app.nerava.com,https://www.nerava.com,https://merchant.nerava.com,https://admin.nerava.com

# Feature Flags
DEMO_MODE=false
ENV=prod
```

---

## Component 2: Driver App (`apps/driver/`)

### Architecture
- **Framework**: React 18 + TypeScript + Vite
- **Build Output**: Static files served via Nginx
- **Port**: 3001 (Docker) / 5173 (dev)
- **Deployment**: Docker container with Nginx

### API Keys Required (From You)

#### 1. PostHog Analytics
**Location**: `apps/driver/src/analytics/index.ts:47-48`

**Required Variables**:
```bash
VITE_POSTHOG_KEY=<your_posthog_project_api_key>
VITE_POSTHOG_HOST=https://app.posthog.com  # Optional, defaults to this
VITE_ANALYTICS_ENABLED=true
```

**Current Code**:
```typescript
// apps/driver/src/analytics/index.ts:47-48
const posthogKey = import.meta.env.VITE_POSTHOG_KEY
const posthogHost = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com'
const analyticsEnabled = import.meta.env.VITE_ANALYTICS_ENABLED !== 'false'
```

**Action Required**: Get PostHog project API key from PostHog dashboard and set `VITE_POSTHOG_KEY`.

---

#### 2. Backend API URL
**Location**: `apps/driver/src/services/api.ts:24`

**Required Variables**:
```bash
VITE_API_BASE_URL=https://api.nerava.com  # NOT http://localhost:8001
```

**Current Code**:
```typescript
// apps/driver/src/services/api.ts:24
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'  // ⚠️ LOCALHOST DEFAULT
```

**Action Required**: Set `VITE_API_BASE_URL=https://api.nerava.com` in production build.

---

### Mocked Code Locations

#### 1. Mock Mode Flag
**Location**: `apps/driver/src/services/api.ts:27-29`

**Code**:
```typescript
// apps/driver/src/services/api.ts:27-29
export function isMockMode(): boolean {
  return import.meta.env.VITE_MOCK_MODE === 'true'
}
```

**Usage**: Used throughout driver app to switch between mock and real API:
- `apps/driver/src/services/api.ts:175-178` - Intent capture
- `apps/driver/src/services/api.ts:202-205` - Merchant details
- `apps/driver/src/services/api.ts:219-222` - Wallet activation

**Mock Data Sources**:
- `apps/driver/src/mock/mockApi.ts` - Mock API functions
- `apps/driver/src/mock/mockMerchants.ts` - Mock merchant data
- `apps/driver/src/mock/mockChargers.ts` - Mock charger data
- `apps/driver/src/mock/fixtures.ts` - Mock fixtures

**Action Required**: 
1. Set `VITE_MOCK_MODE=false` in production build
2. Build-time validation in `apps/driver/vite.config.ts:10-14` prevents `VITE_MOCK_MODE=true` in production builds

**Build Validation**:
```typescript
// apps/driver/vite.config.ts:10-14
if (mockMode && (env === 'prod' || env === 'production')) {
  throw new Error(
    'VITE_MOCK_MODE cannot be true in production builds. ' +
    'Set VITE_MOCK_MODE=false and VITE_ENV=prod for production.'
  )
}
```

---

#### 2. Demo Mode (URL Parameter)
**Location**: `apps/driver/src/hooks/useDemoMode.ts:11`

**Code**:
```typescript
// apps/driver/src/hooks/useDemoMode.ts:11
const isDemoMode = searchParams.get('demo') === '1'
```

**Impact**: Enables demo mode when `?demo=1` is in URL. This is acceptable for production as it's opt-in via URL parameter.

**Action Required**: None - this is intentional for demos.

---

### Hardcoded Values

#### 1. API Base URL Default
**Location**: `apps/driver/src/services/api.ts:24`

**Current Code**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
```

**Action Required**: Set `VITE_API_BASE_URL` build arg in Dockerfile or CI/CD.

---

#### 2. Public Base Path
**Location**: `apps/driver/Dockerfile:16`

**Current Code**:
```dockerfile
ARG VITE_PUBLIC_BASE=/app/
```

**Action Required**: Set to `/app/` if served behind `/app/` path, or `/` if served at root.

---

### Production Build Configuration

**Dockerfile Build Args**:
```dockerfile
# apps/driver/Dockerfile:16-26
ARG VITE_PUBLIC_BASE=/app/
ARG VITE_API_BASE_URL=/api  # ⚠️ RELATIVE PATH - NEEDS ABSOLUTE URL
ARG VITE_POSTHOG_KEY
ARG VITE_POSTHOG_HOST=https://app.posthog.com
ARG VITE_ANALYTICS_ENABLED=true
ENV VITE_MOCK_MODE=false
```

**Action Required**: Update Dockerfile to use absolute URL:
```dockerfile
ARG VITE_API_BASE_URL=https://api.nerava.com
```

---

## Component 3: Merchant Portal (`apps/merchant/`)

### Architecture
- **Framework**: React 18 + TypeScript + Vite
- **Build Output**: Static files served via Nginx
- **Port**: 3002 (Docker) / 5174 (dev)
- **Deployment**: Docker container with Nginx

### API Keys Required (From You)

#### 1. PostHog Analytics
**Location**: `apps/merchant/app/analytics/index.ts:46-48`

**Required Variables**:
```bash
VITE_POSTHOG_KEY=<your_posthog_project_api_key>
VITE_POSTHOG_HOST=https://app.posthog.com
VITE_ANALYTICS_ENABLED=true
```

**Action Required**: Same as driver app - get PostHog API key.

---

#### 2. Backend API URL
**Location**: `apps/merchant/app/services/api.ts:2`

**Required Variables**:
```bash
VITE_API_BASE_URL=https://api.nerava.com
```

**Current Code**:
```typescript
// apps/merchant/app/services/api.ts:2
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'  // ⚠️ LOCALHOST DEFAULT
```

**Action Required**: Set `VITE_API_BASE_URL=https://api.nerava.com` in production build.

---

### Mocked Code Locations

**None Found**: Merchant portal does not have mock mode flag. All API calls go directly to backend.

---

### Hardcoded Values

#### 1. API Base URL Default
**Location**: `apps/merchant/app/services/api.ts:2`

**Current Code**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
```

**Action Required**: Set `VITE_API_BASE_URL` build arg.

---

### Production Build Configuration

**Dockerfile Build Args**:
```dockerfile
# apps/merchant/Dockerfile:16-26
ARG VITE_PUBLIC_BASE=/merchant/
ARG VITE_API_BASE_URL=/api  # ⚠️ RELATIVE PATH
ARG VITE_POSTHOG_KEY
ARG VITE_POSTHOG_HOST=https://app.posthog.com
ARG VITE_ANALYTICS_ENABLED=true
ENV VITE_MOCK_MODE=false
```

**Action Required**: Update Dockerfile:
```dockerfile
ARG VITE_API_BASE_URL=https://api.nerava.com
```

---

## Component 4: Admin Portal (`apps/admin/`)

### Architecture
- **Framework**: React 18 + TypeScript + Vite
- **Build Output**: Static files served via Nginx
- **Port**: 3003 (Docker)
- **Deployment**: Docker container with Nginx

### API Keys Required (From You)

#### 1. PostHog Analytics
**Location**: `apps/admin/src/analytics/index.ts:46-48`

**Required Variables**:
```bash
VITE_POSTHOG_KEY=<your_posthog_project_api_key>
VITE_POSTHOG_HOST=https://app.posthog.com
VITE_ANALYTICS_ENABLED=true
```

**Action Required**: Same as driver/merchant apps.

---

#### 2. Backend API URL
**Location**: `apps/admin/src/services/api.ts:2`

**Required Variables**:
```bash
VITE_API_BASE_URL=https://api.nerava.com
```

**Current Code**:
```typescript
// apps/admin/src/services/api.ts:2
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'  // ⚠️ LOCALHOST DEFAULT
```

**Action Required**: Set `VITE_API_BASE_URL=https://api.nerava.com` in production build.

---

### Mocked Code Locations

**None Found**: Admin portal does not have mock mode flag.

---

### Hardcoded Values

#### 1. API Base URL Default
**Location**: `apps/admin/src/services/api.ts:2`

**Current Code**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
```

**Action Required**: Set `VITE_API_BASE_URL` build arg.

---

### Production Build Configuration

**Dockerfile Build Args**:
```dockerfile
# apps/admin/Dockerfile:16-26
ARG VITE_PUBLIC_BASE=/admin/
ARG VITE_API_BASE_URL=/api  # ⚠️ RELATIVE PATH
ARG VITE_POSTHOG_KEY
ARG VITE_POSTHOG_HOST=https://app.posthog.com
ARG VITE_ANALYTICS_ENABLED=true
ENV VITE_MOCK_MODE=false
```

**Action Required**: Update Dockerfile:
```dockerfile
ARG VITE_API_BASE_URL=https://api.nerava.com
```

---

## Component 5: Landing Page (`apps/landing/`)

### Architecture
- **Framework**: Next.js 14+ (App Router)
- **Build Output**: Node.js server + static files
- **Port**: 3000
- **Deployment**: Docker container with Node.js runtime

### API Keys Required (From You)

#### 1. PostHog Analytics
**Location**: Not currently implemented (check `apps/landing/app/analytics/` if exists)

**Required Variables**:
```bash
NEXT_PUBLIC_POSTHOG_KEY=<your_posthog_project_api_key>
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
NEXT_PUBLIC_ANALYTICS_ENABLED=true
```

**Action Required**: Implement PostHog if analytics needed on landing page.

---

#### 2. Driver App URL
**Location**: `apps/landing/app/components/v2/ctaLinks.ts:22-36`

**Required Variables**:
```bash
NEXT_PUBLIC_DRIVER_APP_URL=https://app.nerava.com
```

**Current Code**:
```typescript
// apps/landing/app/components/v2/ctaLinks.ts:14-15
const DEFAULT_DRIVER_APP_URL = 'http://localhost:5173'  // ⚠️ LOCALHOST DEFAULT

// apps/landing/app/components/v2/ctaLinks.ts:22-36
export function getDriverCTAHref(): string {
  const driverAppUrl = process.env.NEXT_PUBLIC_DRIVER_APP_URL || DEFAULT_DRIVER_APP_URL
  // ...
}
```

**Action Required**: Set `NEXT_PUBLIC_DRIVER_APP_URL=https://app.nerava.com` in production.

---

#### 3. Merchant App URL
**Location**: `apps/landing/app/components/v2/ctaLinks.ts:43-57`

**Required Variables**:
```bash
NEXT_PUBLIC_MERCHANT_APP_URL=https://merchant.nerava.com
```

**Current Code**:
```typescript
// apps/landing/app/components/v2/ctaLinks.ts:14-15
const DEFAULT_MERCHANT_APP_URL = 'http://localhost:5174'  // ⚠️ LOCALHOST DEFAULT
```

**Action Required**: Set `NEXT_PUBLIC_MERCHANT_APP_URL=https://merchant.nerava.com` in production.

---

#### 4. Charger Portal URL
**Location**: `apps/landing/app/components/v2/ctaLinks.ts:63-71`

**Required Variables**:
```bash
NEXT_PUBLIC_CHARGER_PORTAL_URL=https://charger.nerava.com  # Optional, falls back to Google Form
```

**Action Required**: Set if charger portal exists, otherwise falls back to Google Form.

---

### Mocked Code Locations

**None Found**: Landing page does not have mock mode.

---

### Hardcoded Values

#### 1. CTA Link Defaults
**Location**: `apps/landing/app/components/v2/ctaLinks.ts:14-15`

**Current Code**:
```typescript
const DEFAULT_DRIVER_APP_URL = 'http://localhost:5173'
const DEFAULT_MERCHANT_APP_URL = 'http://localhost:5174'
```

**Action Required**: These are only used if env vars are not set. Ensure env vars are set in production.

---

### Production Build Configuration

**Dockerfile Build Args**:
```dockerfile
# apps/landing/Dockerfile:17-24
ARG NEXT_PUBLIC_BASE_PATH
ARG NEXT_PUBLIC_POSTHOG_KEY
ARG NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
ARG NEXT_PUBLIC_ANALYTICS_ENABLED=true
```

**Action Required**: Add missing env vars:
```dockerfile
ARG NEXT_PUBLIC_DRIVER_APP_URL
ARG NEXT_PUBLIC_MERCHANT_APP_URL
ARG NEXT_PUBLIC_CHARGER_PORTAL_URL
ENV NEXT_PUBLIC_DRIVER_APP_URL=${NEXT_PUBLIC_DRIVER_APP_URL}
ENV NEXT_PUBLIC_MERCHANT_APP_URL=${NEXT_PUBLIC_MERCHANT_APP_URL}
ENV NEXT_PUBLIC_CHARGER_PORTAL_URL=${NEXT_PUBLIC_CHARGER_PORTAL_URL}
```

---

## Complete API Keys Checklist

### From You (Required)

1. **Twilio**
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_VERIFY_SERVICE_SID` (if using twilio_verify)
   - `OTP_FROM_NUMBER` (if using twilio_sms)

2. **Google**
   - `GOOGLE_CLIENT_ID` (OAuth)
   - `GOOGLE_CLIENT_SECRET` (OAuth)
   - `GOOGLE_PLACES_API_KEY`

3. **Square**
   - `SQUARE_APPLICATION_ID_PRODUCTION`
   - `SQUARE_APPLICATION_SECRET_PRODUCTION`
   - `SQUARE_WEBHOOK_SIGNATURE_KEY`

4. **Stripe**
   - `STRIPE_SECRET_KEY` (live key, `sk_live_...`)
   - `STRIPE_WEBHOOK_SECRET` (`whsec_...`)
   - `STRIPE_CONNECT_CLIENT_ID` (optional)

5. **Smartcar**
   - `SMARTCAR_CLIENT_ID`
   - `SMARTCAR_CLIENT_SECRET`

6. **NREL**
   - `NREL_API_KEY` (free from https://developer.nrel.gov/signup/)

7. **PostHog**
   - `VITE_POSTHOG_KEY` (for driver, merchant, admin apps)
   - `NEXT_PUBLIC_POSTHOG_KEY` (for landing page, if implemented)

---

## Complete Mocked Code Checklist

### Backend
1. ✅ **OTP Stub Provider** (`backend/app/services/auth/stub_provider.py`)
   - **Fix**: Set `OTP_PROVIDER=twilio_verify` or `twilio_sms`
   - **Validation**: `backend/app/core/config.py:225` prevents stub in production

2. ✅ **Google Business Profile Mock** (`backend/app/services/google_business_profile.py`)
   - **Fix**: Set `MERCHANT_AUTH_MOCK=false`

3. ✅ **Demo Mode** (`backend/app/core/config.py:103`)
   - **Fix**: Set `DEMO_MODE=false`

### Driver App
1. ✅ **Mock Mode** (`apps/driver/src/services/api.ts:27-29`)
   - **Fix**: Set `VITE_MOCK_MODE=false` (build-time validation prevents true in prod)

2. ✅ **Mock Data Files** (entire `apps/driver/src/mock/` directory)
   - **Impact**: Only used if `VITE_MOCK_MODE=true`, which is prevented in production builds

---

## Production Deployment Checklist

### Pre-Deployment

- [ ] **Database**: Migrate from SQLite to PostgreSQL
- [ ] **Secrets**: Generate new `JWT_SECRET` and `TOKEN_ENCRYPTION_KEY`
- [ ] **API Keys**: Obtain all 15+ API keys listed above
- [ ] **Environment Variables**: Set all 30+ production env vars
- [ ] **CORS**: Update `ALLOWED_ORIGINS` to production domains
- [ ] **URLs**: Update all `PUBLIC_BASE_URL`, `FRONTEND_URL` to production domains
- [ ] **Mock Flags**: Disable all mock modes (`OTP_PROVIDER`, `MERCHANT_AUTH_MOCK`, `VITE_MOCK_MODE`, `DEMO_MODE`)

### Build Configuration

- [ ] **Driver App**: Set `VITE_API_BASE_URL`, `VITE_POSTHOG_KEY`, `VITE_MOCK_MODE=false`
- [ ] **Merchant App**: Set `VITE_API_BASE_URL`, `VITE_POSTHOG_KEY`
- [ ] **Admin App**: Set `VITE_API_BASE_URL`, `VITE_POSTHOG_KEY`
- [ ] **Landing Page**: Set `NEXT_PUBLIC_DRIVER_APP_URL`, `NEXT_PUBLIC_MERCHANT_APP_URL`, `NEXT_PUBLIC_POSTHOG_KEY`

### AWS Infrastructure

- [ ] **ECS Fargate**: Backend API container
- [ ] **RDS PostgreSQL**: Production database
- [ ] **ElastiCache Redis**: Caching (if used)
- [ ] **S3**: Static file storage (if used)
- [ ] **Secrets Manager**: Store all API keys and secrets
- [ ] **ALB**: Load balancer with TLS termination
- [ ] **Route 53**: DNS configuration
- [ ] **CloudWatch**: Logging and monitoring

### Post-Deployment Validation

- [ ] **Health Checks**: Verify `/health` endpoints respond
- [ ] **OTP**: Test phone verification with real Twilio
- [ ] **OAuth**: Test Google Business Profile OAuth flow
- [ ] **API**: Verify all frontend apps can connect to backend
- [ ] **Analytics**: Verify PostHog events are tracking
- [ ] **CORS**: Verify CORS headers allow only production domains
- [ ] **Database**: Verify PostgreSQL connection and migrations
- [ ] **Secrets**: Verify no secrets are logged or exposed

---

## Code Changes Required

### 1. Backend Config Validation Enhancement

**File**: `backend/app/core/config.py`

**Add validation for MERCHANT_AUTH_MOCK in production**:
```python
# Add after line 248 (OTP validation)
# Validate Google Business Profile mock mode in production
if settings.ENV == "prod" and settings.MERCHANT_AUTH_MOCK:
    error_msg = "MERCHANT_AUTH_MOCK=true is not allowed in production"
    logger.error(error_msg)
    raise ValueError(error_msg)
```

---

### 2. Frontend Dockerfiles - Absolute API URLs

**Files**: 
- `apps/driver/Dockerfile`
- `apps/merchant/Dockerfile`
- `apps/admin/Dockerfile`

**Change**:
```dockerfile
# FROM:
ARG VITE_API_BASE_URL=/api

# TO:
ARG VITE_API_BASE_URL=https://api.nerava.com
```

---

### 3. Landing Page Dockerfile - Add Missing Env Vars

**File**: `apps/landing/Dockerfile`

**Add**:
```dockerfile
ARG NEXT_PUBLIC_DRIVER_APP_URL
ARG NEXT_PUBLIC_MERCHANT_APP_URL
ARG NEXT_PUBLIC_CHARGER_PORTAL_URL
ENV NEXT_PUBLIC_DRIVER_APP_URL=${NEXT_PUBLIC_DRIVER_APP_URL}
ENV NEXT_PUBLIC_MERCHANT_APP_URL=${NEXT_PUBLIC_MERCHANT_APP_URL}
ENV NEXT_PUBLIC_CHARGER_PORTAL_URL=${NEXT_PUBLIC_CHARGER_PORTAL_URL}
```

---

## Summary

### Critical Issues (Must Fix Before Production)

1. **OTP Provider**: Defaults to `stub` - **MUST** set to `twilio_verify` or `twilio_sms`
2. **Database**: Defaults to SQLite - **MUST** use PostgreSQL
3. **CORS**: Defaults to `*` - **MUST** restrict to production domains
4. **Mock Modes**: Multiple mock flags enabled - **MUST** disable all
5. **API URLs**: Defaults to localhost - **MUST** set production URLs
6. **JWT Secret**: Defaults to `dev-secret` - **MUST** generate secure secret

### API Keys Needed (15+)

- Twilio (4 variables)
- Google (3 variables)
- Square (4 variables)
- Stripe (3 variables)
- Smartcar (3 variables)
- NREL (1 variable)
- PostHog (1-2 variables)

### Mocked Code Locations (5)

- Backend OTP stub provider
- Backend Google Business Profile mock
- Backend demo mode
- Driver app mock mode (build-time validated)
- Driver app mock data files (only used if mock mode enabled)

### Environment Variables Needed (30+)

See complete list in each component section above.

---

**End of Report**




