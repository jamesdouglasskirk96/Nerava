# Production Deployment Checklist

This document provides a production environment checklist to ensure safe deployment to AWS.

## Production Safety Gates

The application includes fail-fast validation that prevents startup if production blockers are detected:

- ❌ OTP_PROVIDER=stub
- ❌ MERCHANT_AUTH_MOCK=true
- ❌ DEMO_MODE=true
- ❌ ALLOWED_ORIGINS=*
- ❌ DATABASE_URL starting with sqlite://
- ❌ PUBLIC_BASE_URL containing localhost
- ❌ FRONTEND_URL containing localhost
- ❌ JWT_SECRET using default value
- ❌ TOKEN_ENCRYPTION_KEY missing or invalid

## Required Environment Variables

### Backend (`backend/`)

#### Database (REQUIRED)
```bash
DATABASE_URL=postgresql://user:password@host:5432/nerava
```
**Note:** SQLite is rejected in production. Must use PostgreSQL.

#### Security (REQUIRED)
```bash
# Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
JWT_SECRET=<secure_random_value>

# Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
TOKEN_ENCRYPTION_KEY=<44_char_fernet_key>
```

#### URLs (REQUIRED: No localhost)
```bash
PUBLIC_BASE_URL=https://api.nerava.network
FRONTEND_URL=https://app.nerava.network
```

#### CORS (REQUIRED: Explicit origins only)
```bash
ALLOWED_ORIGINS=https://app.nerava.network,https://www.nerava.network,https://merchant.nerava.network,https://admin.nerava.network
```
**Note:** Wildcard `*` is rejected in production.

#### Host Security (REQUIRED)
```bash
ALLOWED_HOSTS=api.nerava.network,*.nerava.network
```

#### OTP Provider (REQUIRED: Must NOT be stub)
```bash
OTP_PROVIDER=twilio_verify
# OR: OTP_PROVIDER=twilio_sms

TWILIO_ACCOUNT_SID=<your_twilio_account_sid>
TWILIO_AUTH_TOKEN=<your_twilio_auth_token>
TWILIO_VERIFY_SERVICE_SID=<your_twilio_verify_service_sid>
# OTP_FROM_NUMBER required only if using twilio_sms
```

#### Feature Flags (REQUIRED: Must be disabled)
```bash
MERCHANT_AUTH_MOCK=false
DEMO_MODE=false
```

#### Redis (REQUIRED)
```bash
REDIS_URL=redis://host:6379/0
```

#### Google OAuth (if using merchant SSO)
```bash
GOOGLE_CLIENT_ID=<your_google_client_id>
GOOGLE_OAUTH_CLIENT_ID=<your_google_oauth_client_id>
GOOGLE_OAUTH_CLIENT_SECRET=<your_google_oauth_client_secret>
GOOGLE_OAUTH_REDIRECT_URI=https://api.nerava.network/v1/merchants/google/callback
```

#### Google Places API
```bash
GOOGLE_PLACES_API_KEY=<your_google_places_api_key>
```

#### Square API (Production)
```bash
SQUARE_ENV=production
SQUARE_APPLICATION_ID_PRODUCTION=<your_square_app_id>
SQUARE_APPLICATION_SECRET_PRODUCTION=<your_square_app_secret>
SQUARE_REDIRECT_URL_PRODUCTION=https://api.nerava.network/v1/merchants/square/callback
SQUARE_WEBHOOK_SIGNATURE_KEY=<your_square_webhook_signature_key>
```

#### Stripe (Production)
```bash
STRIPE_SECRET_KEY=sk_live_<your_live_secret_key>
STRIPE_WEBHOOK_SECRET=whsec_<your_webhook_secret>
STRIPE_CONNECT_CLIENT_ID=ca_<your_connect_client_id>
```

#### Smartcar (Production)
```bash
SMARTCAR_CLIENT_ID=<your_smartcar_client_id>
SMARTCAR_CLIENT_SECRET=<your_smartcar_client_secret>
SMARTCAR_REDIRECT_URI=https://api.nerava.network/oauth/smartcar/callback
SMARTCAR_MODE=live
SMARTCAR_STATE_SECRET=<secure_random_secret>
```

#### HTTPS Redirect (Optional)
```bash
# Set to true if behind ALB/load balancer that terminates TLS
SKIP_HTTPS_REDIRECT=false
```

### Frontend Apps (`apps/driver/`, `apps/merchant/`, `apps/admin/`)

#### Build Arguments (REQUIRED)
```bash
VITE_API_BASE_URL=https://api.nerava.network
VITE_ENV=prod
VITE_MOCK_MODE=false
VITE_POSTHOG_KEY=<your_posthog_key>
```

**Note:** Builds will fail if `VITE_API_BASE_URL` is `/api` or `http://localhost:*` in production.

### Landing Page (`apps/landing/`)

#### Build Arguments (REQUIRED)
```bash
NEXT_PUBLIC_DRIVER_APP_URL=https://app.nerava.network
NEXT_PUBLIC_MERCHANT_APP_URL=https://merchant.nerava.network
NEXT_PUBLIC_CHARGER_PORTAL_URL=https://charger.nerava.network
NEXT_PUBLIC_POSTHOG_KEY=<your_posthog_key>
```

**Note:** Builds will fail if ESLint errors exist (eslint.ignoreDuringBuilds=false).

## Validation Commands

### Backend Validation

Test that production safety gates work:

```bash
# Should fail: OTP_PROVIDER=stub
ENV=prod OTP_PROVIDER=stub python -m app.main_simple

# Should fail: MERCHANT_AUTH_MOCK=true
ENV=prod MERCHANT_AUTH_MOCK=true python -m app.main_simple

# Should fail: DEMO_MODE=true
ENV=prod DEMO_MODE=true python -m app.main_simple

# Should fail: ALLOWED_ORIGINS=*
ENV=prod ALLOWED_ORIGINS=* python -m app.main_simple

# Should fail: DATABASE_URL=sqlite://
ENV=prod DATABASE_URL=sqlite:///test.db python -m app.main_simple

# Should fail: PUBLIC_BASE_URL=localhost
ENV=prod PUBLIC_BASE_URL=http://localhost:8001 python -m app.main_simple

# Should fail: FRONTEND_URL=localhost
ENV=prod FRONTEND_URL=http://localhost:8001/app python -m app.main_simple
```

### Frontend Build Validation

Test that frontend builds fail with invalid config:

```bash
# Should fail: VITE_API_BASE_URL=/api
cd apps/driver && VITE_ENV=prod VITE_API_BASE_URL=/api npm run build

# Should fail: VITE_API_BASE_URL=localhost
cd apps/driver && VITE_ENV=prod VITE_API_BASE_URL=http://localhost:8001 npm run build
```

### Landing Page Build Validation

Test that landing page build fails with ESLint errors:

```bash
# Should fail if ESLint errors exist
cd apps/landing && npm run build
```

## Production Deployment Steps

1. **Set all required environment variables** (see above)
2. **Generate secrets:**
   ```bash
   # JWT Secret
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   
   # Token Encryption Key
   python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
   ```
3. **Verify database is PostgreSQL** (not SQLite)
4. **Build frontend apps** with production env vars
5. **Build landing page** with production env vars
6. **Start backend** - it will validate all safety gates on startup
7. **Monitor logs** for any validation failures

## Security Features Enabled in Production

- **TrustedHostMiddleware**: Validates Host header against ALLOWED_HOSTS
- **HTTPSRedirectMiddleware**: Redirects HTTP to HTTPS (unless SKIP_HTTPS_REDIRECT=true)
- **CORS**: Explicit origins only, no wildcard
- **Postgres Pooling**: Configured with pool_size=20, max_overflow=10, pool_pre_ping=True, pool_recycle=3600
- **Security Headers**: HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy

## Troubleshooting

If the application fails to start, check logs for validation errors. Common issues:

- Missing required environment variables
- Using forbidden values (stub, mock, demo, localhost, wildcard)
- Invalid secret formats (JWT_SECRET, TOKEN_ENCRYPTION_KEY)
- SQLite database URL in production

All validation errors include clear error messages indicating what needs to be fixed.
