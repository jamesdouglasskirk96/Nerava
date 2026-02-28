# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Nerava

Nerava is an EV charging rewards platform that connects drivers at charging stations with nearby merchants offering exclusive deals. Drivers charge their EV, earn rewards (Nova points + cash via Stripe), and redeem at participating merchants. Sponsors create campaigns that pay drivers for charging at specific locations/times. The system has a driver-facing app, merchant portal, admin dashboard, sponsor console, landing page, iOS native shell, and a FastAPI backend.

## Repository Structure

This is a monorepo with independently deployed apps:

- **`apps/driver`** — Driver mobile/web app (React 19, Vite 7, Tailwind 4, React Router 7, React Query)
- **`apps/merchant`** — Merchant portal + acquisition funnel (React 18, Vite 5, Radix UI, React Hook Form)
- **`apps/admin`** — Admin dashboard (React 18, Vite 5, Radix UI, Recharts)
- **`apps/console`** — Sponsor campaign management portal (React 18, Vite 5, Radix UI, React Router 6)
- **`apps/landing`** — Marketing site (Next.js 14, static export for S3)
- **`apps/link`** — Link redirect app (React 18, Vite 5, minimal)
- **`backend/`** — FastAPI monolith (Python, SQLAlchemy 2, Alembic, Pydantic 2)
- **`packages/analytics`** — Shared PostHog analytics wrapper (`@nerava/analytics`)
- **`Nerava/`** — iOS Xcode project (WKWebView shell wrapping the driver web app)
- **`Nerava-Campaign-Portal/`** — Newer iteration of sponsor campaign portal (React Router 7, may supersede `apps/console`)
- **`e2e/`** — Cross-app Playwright E2E tests
- **`infra/terraform/`** — AWS infrastructure (Terraform configs for ECS, RDS, ALB, Route53, CloudWatch)
- **`infra/setup_monitoring.sh`** — AWS CLI script to bootstrap CloudWatch alarms + SNS alerting
- **`infra/nginx/`** — Nginx reverse proxy config for Docker Compose

## Build & Dev Commands

### Backend (FastAPI)

```bash
# Run locally (from repo root or backend/)
cd backend && uvicorn app.main_simple:app --reload --port 8001

# Run tests (uses in-memory SQLite automatically)
cd backend && pytest
cd backend && pytest tests/test_checkin.py              # single file
cd backend && pytest tests/test_checkin.py::test_name   # single test
cd backend && pytest -k "keyword"                       # by keyword

# Database migrations
cd backend && python -m alembic upgrade head            # apply all
cd backend && python -m alembic revision --autogenerate -m "description"  # create new
```

### Driver App

```bash
cd apps/driver && npm install && npm run dev     # localhost:5173, uses VITE_API_BASE_URL (no proxy)
cd apps/driver && npm run build                  # TypeScript check + Vite build
cd apps/driver && npm run lint
cd apps/driver && npm run test                   # Vitest
cd apps/driver && npx vitest run                 # Vitest single run (no watch)
```

### Merchant Portal

```bash
cd apps/merchant && npm install && npm run dev   # localhost:5174, proxies /v1 to :8001
cd apps/merchant && npm run build
cd apps/merchant && npm run lint
```

### Admin Dashboard

```bash
cd apps/admin && npm install && npm run dev      # localhost:3001
cd apps/admin && npm run build
cd apps/admin && npm run lint
```

### Landing Page

```bash
cd apps/landing && npm install && npm run dev
cd apps/landing && npm run build                 # Next.js static export
cd apps/landing && npm run lint
```

### Console (Sponsor Portal)

```bash
cd apps/console && npm install && npm run dev    # localhost:5176, proxies /v1 to :8001
cd apps/console && npm run build
cd apps/console && npm run lint
```

### E2E Tests

```bash
cd e2e && npm install && npx playwright test
cd e2e && npx playwright test --ui               # interactive mode
```

### Full Stack (Docker Compose)

```bash
docker-compose up                               # all services
# Backend :8001, Landing :80/, Driver :80/app/, Merchant :80/merchant/, Admin :80/admin/, PostHog :8081
```

## Backend Architecture

### Entry Point

- **`app/main_simple.py`** — Production entry point used by App Runner, Docker, and tests. Initializes Sentry (when `SENTRY_DSN` is set), registers all routers, and mounts middleware.

### Key Layers

- **`app/routers/`** — FastAPI route handlers. All routes use `/v1` prefix.
- **`app/services/`** — Business logic layer (arrival, checkin, checkout, payments, notifications, etc.)
- **`app/models/`** — SQLAlchemy ORM models. `domain.py` has core models (Zone, EnergyEvent, DomainMerchant, DomainChargingSession, NovaTransaction). Other key models: `user.py`, `arrival_session.py`, `exclusive_session.py`, `tesla_connection.py`, `campaign.py` (sponsor campaigns), `session_event.py` (SessionEvent + IncentiveGrant).
- **`app/schemas/`** — Pydantic request/response schemas
- **`app/dependencies/`** — FastAPI dependency injection (`get_db`, auth, feature flags)
- **`app/middleware/`** — Auth (JWT), rate limiting, metrics, region routing, audit logging, security headers, request size limits
- **`app/integrations/`** — Third-party clients (legacy Google Places, Google Distance Matrix, NREL, Overpass/OSM)
- **`app/cache/`** — Two-layer caching (L1 in-memory + L2 Redis) with TTL support

### Middleware Stack

| Middleware | Purpose |
|-----------|---------|
| `auth.py` | JWT verification, extract current user from token |
| `audit.py` | Audit logging (user actions, resource changes) |
| `logging.py` | Structured request/response logging (request_id, method, path, status, duration_ms, user_id) |
| `metrics.py` | Prometheus metrics collection |
| `ratelimit.py` | Rate limiting per user/IP (Redis-backed, configurable) |
| `region.py` | Region routing and context injection |
| `request_id.py` | Generate/track X-Request-ID for distributed tracing |
| `request_size.py` | Enforce max request body size limits |
| `security_headers.py` | HSTS, X-Content-Type-Options, CSP, etc. |

### Database

- **Dev:** SQLite (`sqlite:///./nerava.db`)
- **Production:** PostgreSQL on RDS (`nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com`)
- **Migrations:** Alembic, run from `backend/` directory. ~90 migration files in `alembic/versions/`.
- **Lazy engine init:** `app/db.py` creates the engine on first access, not at import time. This matters for container health checks.

### Key Database Tables

| Table | Purpose |
|-------|---------|
| `users` | Drivers, merchants, admins with roles |
| `session_events` | Verified EV charging sessions (30 columns: timing, energy, location, telemetry, anti-fraud) |
| `incentive_grants` | Links sessions to campaign rewards (one grant per session max) |
| `campaigns` | Sponsor campaigns with budget, targeting rules (JSON), status lifecycle |
| `driver_wallets` | Driver reward balances, pending funds, Stripe Express account links |
| `wallet_ledger` | Double-entry transaction ledger for wallet credits/debits |
| `payouts` | Driver withdrawal records (pending → processing → paid/failed) |
| `nova_transactions` | Double-entry Nova points ledger (grants, redemptions, transfers) |
| `chargers` | EV charger locations, network, connector type, power rating (indexed lat/lng) |
| `domain_merchants` | Merchant records with perk config, QR tokens, Square integration |
| `zones` | Geographic zones (center lat/lng + radius) |
| `exclusive_sessions` | Active exclusive offer sessions (charger arrival + merchant unlock, countdown) |
| `tesla_connections` | Tesla OAuth tokens per driver (access_token, refresh_token, vehicle_id, vin) |
| `ev_verification_codes` | EV-XXXX codes, valid for 2 hours |
| `device_tokens` | APNs/FCM push notification tokens |

### Auth Flow

JWT-based authentication with OTP (Twilio Verify) for phone-first login. Apple Sign-In, Google Sign-In, and Tesla OAuth also supported. The driver app login modal shows Apple/Google buttons above the phone OTP form (buttons hidden if `VITE_APPLE_CLIENT_ID`/`VITE_GOOGLE_CLIENT_ID` env vars not set). The `OTP_PROVIDER=stub` env var enables fake OTP in dev.

### Key Integrations

- **Stripe** — Payments and payouts (`app/services/stripe_service.py`, `app/services/payout_service.py`)
- **Twilio** — OTP verification (`app/services/auth/twilio_verify.py`)
- **PostHog** — Analytics across all apps (`packages/analytics`)
- **Tesla Fleet API** — Vehicle charging verification (`app/services/tesla_oauth.py`, `app/routers/tesla_auth.py`)
- **Google Places (New API)** — Merchant enrichment and search (`app/services/google_places_new.py`). Legacy client at `app/integrations/google_places_client.py`.
- **Sentry** — Error tracking (initialized in `main_simple.py` when `SENTRY_DSN` is set)
- **Square** — POS integration for merchant check-in/redemption (`app/services/square_service.py`)
- **Smartcar** — Alternative EV API for non-Tesla vehicles (`app/services/smartcar_service.py`)

## Core Business Logic

### Charging Session Lifecycle

The hot path of the entire system. Managed by `SessionEventService` in `app/services/session_event_service.py`.

**Flow:**
1. Driver app polls `POST /v1/charging-sessions/poll` every **60 seconds** (visibility-aware, pauses when backgrounded)
2. Backend checks Tesla Fleet API for charging state on driver's selected vehicle
3. **Not charging → Charging:** Creates `SessionEvent` row, matches to nearest charger via geolocation (500m radius)
4. **Charging → Charging:** Updates telemetry (kwh, battery %, power_kw), backfills location if missing
5. **Charging → Not charging:** Ends session, computes quality_score (anti-fraud), triggers `IncentiveEngine.evaluate_session()`
6. **Server-side cache:** 30-second dedup per driver to avoid redundant Tesla API calls
7. **Stale cleanup:** Auto-closes sessions not updated in 15 minutes

**Per-session data footprint:** ~500 bytes in `session_events` + ~300 bytes in `incentive_grants` (if matched) + indexes. At 1M drivers averaging 2.5 sessions/week, that's ~10.75M rows/month, ~5.4 GB raw data/month, ~100 GB/year with indexes.

### Incentive Engine

Evaluates sessions against active campaigns when a session ends. Managed by `IncentiveEngine` in `app/services/incentive_engine.py`.

**Matching rules (ALL are AND-ed):**
- Minimum/maximum duration
- Charger IDs or charger networks (Tesla, ChargePoint, etc.)
- Zone IDs or geographic radius (haversine distance)
- Time of day window (handles overnight spans)
- Day of week
- Minimum power (kW) for DC fast charging targeting
- Connector types (CCS, Tesla, CHAdeMO)
- Driver session count bounds (new vs repeat driver rules)
- Driver allowlist (email or user ID)
- Per-driver caps (daily/weekly/total limits per campaign)

**Grant logic:**
- One session = one grant max (highest priority campaign wins, no stacking)
- Grants created only on session END
- Atomic budget decrement prevents overruns
- Idempotent via `session_event_id` uniqueness constraint

### Nova Transaction System

Double-entry points ledger in `app/services/nova_service.py`.

- Every grant/redemption is an atomic Nova transaction
- Idempotent via `idempotency_key` + `payload_hash` (SHA256). Same key + same hash = returns existing transaction. Same key + different hash = 409 Conflict.
- `grant_to_driver()` increments both `nova_balance` and `energy_reputation_score` (1:1 ratio for `driver_earn` type)
- Transaction types: `driver_earn`, `admin_grant`, `driver_redeem`, `transfer`

### Energy Reputation System

Gamified tier system in `app/services/reputation.py`.

| Tier | Points Required | Color |
|------|----------------|-------|
| Bronze | 0 | `#78716c` |
| Silver | 100 | `#64748b` |
| Gold | 300 | `#eab308` |
| Platinum | 700+ | `#06b6d4` |

- Points accrue 1:1 with Nova earned from charging sessions
- Non-incentive sessions (no campaign match) earn 5 base reputation points if quality_score > 30
- Streak days computed from consecutive days with completed sessions (handles PostgreSQL + SQLite dialects)
- API: `GET /v1/charging-sessions/reputation` returns tier, points, progress, streak

### Driver Wallet & Payout Flow

Stripe Express payouts in `app/services/payout_service.py`.

1. Wallet auto-created on first access (`get_or_create_wallet`)
2. Campaign grants credit `balance_cents` + create `wallet_ledger` entry
3. Withdrawal: validates min $20, max 3/day, max $1000/week
4. Moves funds: `balance_cents` → `pending_balance_cents` (atomic)
5. Creates Stripe Transfer to driver's Express account
6. Webhook confirms completion → status `paid`

### Exclusive Session Flow

Merchant deal activation in `app/routers/exclusive.py`.

1. Driver arrives at charger → app detects via geolocation
2. Driver selects merchant → activates exclusive offer
3. Countdown timer starts (default 60 minutes)
4. Driver visits merchant → verification (QR scan, dwell time, or manual)
5. Redemption code generated for merchant POS

## Frontend Architecture

### Driver App (`apps/driver`)

- **Framework:** React 19, Vite 7, Tailwind 4 (not 3), React Router 7, React Query
- **API client:** `src/services/api.ts` — all API calls, React Query hooks, type-safe responses
- **Validation:** `src/services/schemas.ts` — Zod schemas for API response validation
- **State:** React Query for server state, React Context for local state
- **Pattern:** Feature-folder: `src/components/FeatureName/FeatureName.tsx`

**Key components:**

| Component | Purpose |
|-----------|---------|
| `DriverHome/DriverHome.tsx` | Main home screen — session status, charger list, map/card toggle, merchant carousel |
| `ChargerMap/ChargerMap.tsx` | Leaflet map with charger/merchant/user pins (OpenStreetMap tiles) |
| `PreCharging/PreChargingScreen.tsx` | Charger selection and session start |
| `SessionActivity/SessionActivityScreen.tsx` | Charging history, stats, energy reputation card |
| `SessionActivity/EnergyReputationCard.tsx` | Gamified tier/streak/progress display |
| `SessionActivity/SessionCard.tsx` | Individual charging session display |
| `SessionActivity/ActiveSessionBanner.tsx` | Active charging session banner |
| `MerchantCarousel/MerchantCarousel.tsx` | Horizontal merchant discovery carousel |
| `MerchantDetails/MerchantDetailsScreen.tsx` | Full merchant details (distance, perk, wallet) |
| `MerchantDetail/MerchantDetailModal.tsx` | Merchant detail modal overlay |
| `ExclusiveActiveView/ExclusiveActiveView.tsx` | Active exclusive session with countdown |
| `EVArrival/ActiveSession.tsx` | Active EV charging session management |
| `EVOrder/EVOrderFlow.tsx` | EV order creation flow |
| `WhileYouCharge/WhileYouChargeScreen.tsx` | Merchant deals during charging |
| `Wallet/WalletModal.tsx` | Wallet balance and payout management |
| `Earnings/Earnings.tsx` | Driver earnings dashboard |
| `Account/AccountPage.tsx` | Profile, favorites, settings, login/logout |
| `Account/LoginModal.tsx` | Phone OTP + Apple/Google Sign-In |
| `TeslaLogin/VehicleSelectScreen.tsx` | Vehicle selection after Tesla OAuth |
| `shared/PrimaryFilters.tsx` | Category and distance filters |
| `shared/SearchBar.tsx` | Charger/merchant search input |
| `ErrorBoundary.tsx` | React error boundary |
| `SessionExpiredModal.tsx` | Expired session notification |

**Key hooks:**

| Hook | Purpose |
|------|---------|
| `useSessionPolling` | Polls charging state every 60s, visibility-aware, tracks duration/kwh/incentive |
| `usePageVisibility` | Tracks foreground/background, pauses polling when hidden |
| `useExclusiveSessionState` | Manages exclusive deal lifecycle (activation, countdown, completion) |
| `useGeolocation` | Wrapper for navigator.geolocation with error handling |
| `useNativeBridge` | Communication bridge to iOS WKWebView (location, auth, device tokens) |
| `useArrivalLocationPolling` | 5-second GPS polling during arrival confirmation |
| `useDriverSessionState` | Driver session lifecycle (start, active, end) |
| `useEVContext` | EV charging context (charger selection, charging state) |
| `useViewportHeight` | Responsive layout height tracking |
| `useDemoMode` | Toggle demo/mock mode for development |

**Contexts:**

| Context | Purpose |
|---------|---------|
| `DriverSessionContext` | Global session state: charger target, session active/ended, incentive data |
| `FavoritesContext` | User's favorited merchants, persisted to localStorage |

**Design tokens:** Custom values in `tailwind.config.js` — `rounded-card`, `rounded-button`, `rounded-pill`, `rounded-modal`, `shadow-figma-card`.

### Merchant Portal (`apps/merchant`)

- Radix UI + Tailwind 3 + `sonner` for toasts
- **Public acquisition funnel** (no auth): `/find` → `/preview` → `/claim`. Backend at `/v1/merchant/funnel/*`. Preview URLs are HMAC-signed with 7-day TTL.
- **Dashboard routes** (auth required): `/dashboard`, `/exclusives`, `/ev-arrivals`, `/visits`, `/settings`

### Admin/Console

- Both use Radix UI + Tailwind 3
- Admin on port 3001, Console on port 5176, both proxy `/v1` to backend

## iOS App Architecture (`Nerava/`)

WKWebView shell wrapping the driver web app. **No App Store push needed for web-only changes.**

### NeravaApp.swift
- `AppDelegate` for remote notification handling (APNs device token registration)
- Creates singletons: `LocationService`, `SessionEngine`, `GeofenceManager`, `APIClient`
- Handles universal links / deep links via `DeepLinkHandler`

### WebViewContainer.swift
- Wraps `WebViewRepresentable` (WKWebView)
- Overlays: LoadingOverlay, OfflineOverlay, ErrorOverlay
- Error types: network, server (HTTP), SSL, processTerminated, unknown

### NativeBridge.swift
- Bidirectional JS ↔ Swift communication via `window.neravaNative`
- **JS → Swift methods:** `setChargerTarget()`, `setAuthToken()`, `confirmExclusiveActivated()`, `confirmVisitVerified()`, `endSession()`, `requestAlwaysLocation()`, `getLocation()`, `getSessionState()`, `getPermissionStatus()`, `getAuthToken()`, `openExternalUrl()`
- **Swift → JS messages:** `SESSION_STATE_CHANGED`, `PERMISSION_STATUS`, `LOCATION_RESPONSE`, `AUTH_TOKEN_RESPONSE`, `DEVICE_TOKEN_REGISTERED`, `NATIVE_READY`
- Origin whitelisting for security

### NotificationService.swift
- APNs authorization request, local notifications for session/arrival events
- Stores APNs token for forwarding to backend

## Analytics Events

Tracked via PostHog (`packages/analytics`). Key events in `apps/driver/src/analytics/events.ts`:

- **Session:** `SESSION_START`, `PAGE_VIEW`, `HOME_REFRESHED`
- **Auth:** `OTP_START`, `OTP_VERIFY_SUCCESS/FAIL`
- **Charging:** `CHARGING_SESSION_DETECTED`, `CHARGING_SESSION_ENDED`, `CHARGING_INCENTIVE_EARNED`, `CHARGING_ACTIVITY_OPENED`
- **Intent:** `INTENT_CAPTURE_REQUEST/SUCCESS/FAIL`
- **Exclusive:** `EXCLUSIVE_ACTIVATE_CLICK/SUCCESS/FAIL`, `EXCLUSIVE_COMPLETE_CLICK/SUCCESS/FAIL`
- **Merchant:** `MERCHANT_CLICKED`, `MERCHANT_DETAIL_VIEWED`, `MERCHANT_FAVORITED`, `MERCHANT_SHARED`
- **Arrival:** `ARRIVAL_VERIFIED`, `EV_ARRIVAL_CONFIRMED`, `EV_ARRIVAL_GEOFENCE_TRIGGERED`
- **Virtual Key:** `VIRTUAL_KEY_PAIRING_STARTED/COMPLETED/FAILED`, `VIRTUAL_KEY_ARRIVAL_DETECTED`
- **Other:** `SEARCH_QUERY`, `DEVICE_TOKEN_REGISTERED`, `PREFERENCES_SUBMIT`

## Testing

### Backend Tests

- **Framework:** pytest with in-memory SQLite
- **Fixtures:** `backend/tests/conftest.py` provides `db` (isolated session per test, auto-rollback), `client` (FastAPI TestClient with dependency overrides), `test_user`, `test_merchant`
- **Test DB override:** Uses `app.dependency_overrides` to inject test sessions into both `app.db.get_db` and `app.dependencies.get_db`
- **Root `tests/` directory** has security/integration tests that import from `backend/`
- **Key test files:** `test_session_event_service.py`, `test_incentive_engine.py`, `test_payout_service.py`, `test_campaign_service.py`, `test_tesla_oauth.py`, `test_security_headers.py`

### Frontend Tests

- **Driver app:** Vitest + React Testing Library + jsdom
- **E2E:** Playwright (root `e2e/` and `apps/driver/e2e/`)

## CI/CD

- **Backend tests:** `.github/workflows/backend-tests.yml` — pytest on Python 3.10 (triggers on `backend/` changes)
- **Driver app:** `.github/workflows/ci-driver-app.yml` — lint, build, vitest, Playwright (triggers on `apps/driver/` changes)
- **Deploy:** `.github/workflows/deploy-prod.yml` — full production pipeline (includes Trivy container scan); `.github/workflows/deploy-driver-app.yml` — Docker build + ECR push
- **Security:** `.github/workflows/codeql-driver-app.yml` — CodeQL for JS/TS; `.github/workflows/codeql-backend.yml` — CodeQL for Python; `.github/workflows/backend-security.yml` — pip-audit + bandit SAST (PRs + weekly)
- **Monitoring:** `.github/workflows/health-check.yml` — pings all prod endpoints every 30 min, opens GitHub issues on failure; `.github/workflows/daily-report.yml` — daily 7am ET production report via `backend/scripts/daily_prod_report.py`; `.github/workflows/prod-validation.yml` — live API validation (daily + post-deploy)

## Infrastructure & Production Deployment

### Actual Production Architecture (what's running)

The production architecture does **NOT** match the ECS setup in `deploy-prod.yml`. The actual running services are:

- **Backend:** AWS **App Runner** (not ECS). Service ARN: `arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3`
- **Driver app:** Static site on **S3 + CloudFront** (bucket: `app.nerava.network`)
- **Merchant portal:** S3 + CloudFront
- **Admin dashboard:** S3 + CloudFront
- **Landing page:** S3 + CloudFront
- **Link app:** S3 + CloudFront
- **Database:** RDS PostgreSQL (`nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com`)

### CloudFront Distribution IDs

| App | Domain | Distribution ID |
|-----|--------|-----------------|
| Landing | `nerava.network` | `E29NMGJ14FEJSE` |
| Driver | `app.nerava.network` | `E2UEQFQ3RSEEAR` |
| Merchant | `merchant.nerava.network` | `E2EYO3ZPM3S1S0` |
| Admin | `admin.nerava.network` | `E1WZNEUSEZC1X0` |
| Link | `link.nerava.network` | `E10ZCPA7D2D99W` |

### Deploying the Backend (App Runner)

The backend uses **manual deployment** (`AutoDeploymentsEnabled: false`). The CI workflow (`deploy-prod.yml`) pushes to the `nerava/backend` ECR repo but App Runner reads from the **`nerava-backend`** ECR repo with explicit image tags. To deploy:

```bash
# 1. Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 566287346479.dkr.ecr.us-east-1.amazonaws.com

# 2. Build for amd64 (required even on Apple Silicon)
docker build --platform linux/amd64 -t 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:<TAG> ./backend

# 3. Push to ECR
docker push 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:<TAG>

# 4. Update App Runner to new image tag
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{"ImageRepository":{"ImageIdentifier":"566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:<TAG>","ImageConfiguration":{"Port":"8000"},"ImageRepositoryType":"ECR"},"AutoDeploymentsEnabled":false,"AuthenticationConfiguration":{"AccessRoleArn":"arn:aws:iam::566287346479:role/nerava-apprunner-ecr-access"}}' \
  --region us-east-1

# 5. Wait for deployment (~3-4 minutes)
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --region us-east-1 --query 'OperationSummaryList[0].[Type,Status]' --output text

# 6. Verify health
curl https://api.nerava.network/healthz
```

**Important:** When updating App Runner, only the `ImageIdentifier` needs to change. All environment variables are preserved from the existing service configuration — do NOT pass `RuntimeEnvironmentVariables` in the update or you risk wiping them.

### Rollback Procedure

To roll back the backend to a previous image tag:

```bash
# 1. Find the previous image tag (check ECR or deploy logs)
aws ecr describe-images --repository-name nerava-backend --region us-east-1 \
  --query 'sort_by(imageDetails,&imagePushedAt)[-5:].imageTags' --output text

# 2. Update App Runner to the previous tag
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{"ImageRepository":{"ImageIdentifier":"566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:<PREVIOUS_TAG>","ImageConfiguration":{"Port":"8000"},"ImageRepositoryType":"ECR"},"AutoDeploymentsEnabled":false,"AuthenticationConfiguration":{"AccessRoleArn":"arn:aws:iam::566287346479:role/nerava-apprunner-ecr-access"}}' \
  --region us-east-1

# 3. Verify health after ~3 min
curl https://api.nerava.network/healthz
```

For frontend rollback, redeploy the previous git commit's build to S3.

### Deploying Frontend Apps (S3 + CloudFront)

Frontend apps are static builds deployed to S3 with CloudFront cache invalidation:

```bash
# Driver app example
cd apps/driver && VITE_API_BASE_URL=https://api.nerava.network VITE_ENV=prod npm run build
aws s3 sync dist/ s3://app.nerava.network/ --delete --region us-east-1
aws cloudfront create-invalidation --distribution-id E2UEQFQ3RSEEAR --paths "/*" --region us-east-1
```

CloudFront invalidation takes ~15-20 seconds to complete.

### Production Logs

Backend logs are in CloudWatch under the App Runner application log group:

```bash
# Tail live logs (exclude health checks)
aws logs tail "/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application" --follow --region us-east-1

# Search for errors in last hour
aws logs filter-log-events \
  --log-group-name "/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application" \
  --start-time $(($(date +%s)*1000 - 3600000)) \
  --filter-pattern "ERROR" \
  --region us-east-1 \
  --query 'events[*].message' --output text
```

Log format: `YYYY-MM-DD HH:MM:SS,ms [LEVEL] logger_name: message`
Structured request logs from `app.middleware.logging` include: `request_id`, `method`, `path`, `status_code`, `duration_ms`, `user_id`, `user_agent`.

### Docker Architecture: x86_64 (AMD64) Only

All Docker images **must** be built for `linux/amd64`. On Apple Silicon Macs, use `--platform linux/amd64`. Do not add ARM/Graviton support or use `--platform linux/arm64` without updating both the App Runner configuration and the CI build steps in `.github/workflows/deploy-prod.yml`.

## Key System Details

### Tesla Fleet API Integration

- **OAuth service:** `app/services/tesla_oauth.py` — token management, vehicle data, charging verification
- **Router:** `app/routers/tesla_auth.py` — endpoints under `/v1/auth/tesla/`
- **Models:** `app/models/tesla_connection.py` — TeslaConnection (OAuth tokens), EVVerificationCode (EV-XXXX codes)
- **Charging states accepted:** `{"Charging", "Starting"}` — defined in `TeslaOAuthService.CHARGING_STATES`
- **Multi-vehicle:** `verify_charging_all_vehicles()` checks ALL vehicles on a Tesla account, not just the stored primary
- **Wake retry:** Up to 3 attempts with 5s delays for 408 timeouts or unknown (None) charging states
- **EV codes:** Format `EV-XXXX`, valid for 2 hours, stored in `ev_verification_codes` table

### Campaign / Incentive System

Sponsors create campaigns via the console (`apps/console`) that reward drivers for charging at specific locations.

- **Models:** `Campaign` (budget, targeting rules as JSON, status lifecycle), `SessionEvent` (verified charging session), `IncentiveGrant` (links a campaign reward to a session)
- **Backend:** `app/routers/campaigns.py` (`/v1/campaigns/*`), `app/routers/campaign_sessions.py` (`/v1/charging-sessions/*`)
- **Services:** `campaign_service.py` (CRUD + lifecycle), `incentive_engine.py` (evaluates sessions against campaign rules), `corporate_classifier.py` (corporate vs local targeting), `session_event_service.py` (session + grant CRUD)

### Merchant Enrichment

When a merchant is resolved via the acquisition funnel, the backend enriches it from Google Places:

- **Service:** `app/services/merchant_enrichment.py` — calls `google_places_new.py` for place details, photos, open/closed status
- **Gotchas:** Google Places photo URLs can exceed 500 chars; the `primary_photo_url` and `photo_url` columns are varchar(255), so long URLs are stored only in the `photo_urls` JSON column. The `priceLevel` field is a string enum (e.g. `PRICE_LEVEL_MODERATE`), not an integer.

### Feature Flags

Environment-based flags in `app/routers/flags.py`:
- Checked via `is_feature_enabled(flag_name, environment)`, resolves based on `ENV` env var (dev/staging/prod)
- Endpoints: `GET /v1/flags`, `GET /v1/flags/{flag_name}`, `POST /v1/flags/{flag_name}/toggle` (admin only)

### Backend Scripts

Key scripts in `backend/scripts/`:

- `prod_api_health_check.py` — comprehensive production API health check (used by `health-check.yml` workflow)
- `daily_prod_report.py` — queries CloudWatch Logs Insights for daily digest, publishes to SNS
- `db_backup.sh` / `db_restore.sh` — database backup and restore
- `seed_chargers_bulk.py` — bulk charger seeding from NREL/Overpass
- `seed_merchants_free.py` — merchant seeding for free tier
- `seed_if_needed.py` — auto-seed on first run
- `run_migrations.py` — migration runner

## Environment Variables

### Backend (key vars from `app/core/config.py`)

```
# Auth
JWT_SECRET / NERAVA_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES (default 10080 = 7 days)

# Database
DATABASE_URL (default sqlite:///./nerava.db), REDIS_URL (optional)

# Stripe
STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ENABLE_STRIPE_PAYOUTS
MINIMUM_WITHDRAWAL_CENTS (2000), WEEKLY_WITHDRAWAL_LIMIT_CENTS (100000)

# Tesla
TESLA_CLIENT_ID, TESLA_CLIENT_SECRET, TESLA_MOCK_MODE, TESLA_WEBHOOK_SECRET

# Google / Apple
GOOGLE_PLACES_API_KEY, GOOGLE_CLIENT_ID, APPLE_CLIENT_ID

# Other
ENV (dev/staging/prod), OTP_PROVIDER (stub for dev), SENTRY_DSN
FRONTEND_URL, PUBLIC_BASE_URL, API_BASE_URL, DRIVER_APP_URL
TOKEN_ENCRYPTION_KEY (Fernet), PLATFORM_FEE_BPS (2000 = 20%)
```

### Driver App (VITE_ prefix)

```
VITE_API_BASE_URL, VITE_ENV, VITE_APPLE_CLIENT_ID, VITE_GOOGLE_CLIENT_ID
VITE_SENTRY_DSN, VITE_POSTHOG_KEY
```

## Scaling & Cost Considerations

### Data Volume at Scale

The charging session polling endpoint (`POST /v1/charging-sessions/poll`) is the hot path. Each active driver polls every 60 seconds.

**Per-session storage:** ~500 bytes (`session_events`) + ~300 bytes (`incentive_grants` if matched) + index overhead (~60-80%).

| Scale | Sessions/month | DB storage/year | CloudWatch logs/month | Est. total cost/month |
|-------|---------------|-----------------|----------------------|----------------------|
| 10K drivers | 107K | ~1 GB | ~10.8 GB | ~$135 |
| 100K drivers | 1.07M | ~10 GB | ~108 GB | ~$708 |
| 1M drivers | 10.75M | ~100 GB | ~1.08 TB | ~$3,530 |

**Key cost drivers:** CloudWatch log ingestion ($0.50/GB) exceeds DB cost at scale. Polling compute (App Runner instances) is the largest single cost. App Runner caps at 25 instances — need ECS/EKS migration at ~500K+ drivers.

### Known Scaling Gaps

- **No data retention policy:** Session events accumulate forever. Need TTL-based archival to S3.
- **No CloudWatch log sampling:** Every poll request logged. Should skip 200s on `/poll` or sample 1-in-N.
- **Polling-based architecture:** Push-based (Tesla webhooks) would eliminate majority of compute cost.
- **Tesla API rate limits:** Undocumented limits; at 100K+ concurrent polls/minute, will likely be throttled.
- **App Runner ceiling:** 25-instance cap per service.

### Domain Model Gotcha

There are **two** DriverWallet models:
- `app/models/driver_wallet.py` → `DriverWallet` — Stripe payout wallet (balance_cents, stripe_account_id). PK is `id` (UUID), unique on `driver_id`.
- `app/models_domain.py` → `DriverWallet` (re-exported from driver_wallet.py) — Same model. The `energy_reputation_score` column lives on this model (added via migration 018). The domain.py file re-exports it for backward compatibility.

When querying reputation, use `DriverWallet.user_id` (mapped to `driver_id` column) not `DriverWallet.id`.
