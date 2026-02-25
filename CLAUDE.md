# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Nerava

Nerava is an EV charging rewards platform that connects drivers at charging stations with nearby merchants offering exclusive deals. The system has a driver-facing app, merchant portal, admin dashboard, landing page, and a FastAPI backend.

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

### Two Entry Points

- **`app/main.py`** — Full-featured app with all routers and middleware (dev/legacy)
- **`app/main_simple.py`** — Simplified production entry point used by App Runner and Docker. This is the one used in tests and deployments.

### Key Layers

- **`app/routers/`** — FastAPI route handlers. Routes use `/v1` prefix in production.
- **`app/services/`** — Business logic layer (arrival, checkin, checkout, payments, notifications, etc.)
- **`app/models/`** — SQLAlchemy ORM models. `domain.py` has core models (Zone, EnergyEvent, DomainMerchant, DomainChargingSession, NovaTransaction). Other key models: `user.py`, `arrival_session.py`, `exclusive_session.py`, `tesla_connection.py`, `campaign.py` (sponsor campaigns), `session_event.py` (SessionEvent + IncentiveGrant).
- **`app/schemas/`** — Pydantic request/response schemas
- **`app/dependencies/`** — FastAPI dependency injection (`get_db`, auth, feature flags)
- **`app/middleware/`** — Auth (JWT), rate limiting, metrics, region routing, audit logging
- **`app/integrations/`** — Third-party clients (legacy Google Places, Google Distance Matrix, NREL, Overpass/OSM)

### Database

- **Dev:** SQLite (`sqlite:///./nerava.db`)
- **Production:** PostgreSQL on RDS
- **Migrations:** Alembic, run from `backend/` directory. 77 migration files in `alembic/versions/`.
- **Lazy engine init:** `app/db.py` creates the engine on first access, not at import time. This matters for container health checks.

### Auth Flow

JWT-based authentication with OTP (Twilio Verify) for phone-first login. Apple Sign-In, Google Sign-In, and Tesla OAuth also supported. The driver app login modal shows Apple/Google buttons above the phone OTP form (buttons hidden if `VITE_APPLE_CLIENT_ID`/`VITE_GOOGLE_CLIENT_ID` env vars not set). The `OTP_PROVIDER=stub` env var enables fake OTP in dev.

### Key Integrations

- **Stripe** — Payments and payouts (`app/services/stripe_service.py`)
- **Twilio** — OTP verification (`app/services/auth/twilio_verify.py`)
- **PostHog** — Analytics across all apps (`packages/analytics`)
- **Tesla Fleet API** — Vehicle charging verification (`app/services/tesla_oauth.py`, `app/routers/tesla_auth.py`)
- **Google Places (New API)** — Merchant enrichment and search (`app/services/google_places_new.py`). Legacy client at `app/integrations/google_places_client.py`.
- **Sentry** — Error tracking (initialized in `main_simple.py` when `SENTRY_DSN` is set)

## Frontend Patterns

### Driver App Specifics

- Uses Tailwind 4 (not 3) — different config format than merchant/admin
- Custom design tokens in `tailwind.config.js`: card/button/pill/modal border radii, figma-card shadows
- Vite config validates that no `localhost` or `/api` URLs leak into production builds
- `src/services/api.ts` is the API client; `src/services/schemas.ts` has Zod schemas
- `src/hooks/` for shared stateful logic (onboarding, arrival polling, EV context, native bridge)
- Components follow feature-folder pattern: `src/components/FeatureName/FeatureName.tsx`

### Merchant Portal Specifics

- Radix UI component primitives + Tailwind 3
- `sonner` for toast notifications
- Proxies `/v1` to backend in dev
- Has a **public acquisition funnel** (no auth required): `/find` → `/preview` → `/claim`. Backend at `/v1/merchant/funnel/*`. Preview URLs are HMAC-signed with 7-day TTL.
- Dashboard routes (auth required): `/dashboard`, `/exclusives`, `/ev-arrivals`, `/visits`, `/settings`

### Admin/Console Specifics

- Both use Radix UI + Tailwind 3
- Admin proxies `/v1` to backend in dev (port 3001)
- Console proxies `/v1` to backend in dev (port 5176)

## Testing

### Backend Tests

- **Framework:** pytest with in-memory SQLite
- **Fixtures:** `backend/tests/conftest.py` provides `db` (isolated session per test, auto-rollback), `client` (FastAPI TestClient with dependency overrides), `test_user`, `test_merchant`
- **Test DB override:** Uses `app.dependency_overrides` to inject test sessions into both `app.db.get_db` and `app.dependencies.get_db`
- **Root `tests/` directory** has security/integration tests that import from `backend/`

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

### Backend Scripts

Key scripts in `backend/scripts/`:

- `prod_api_health_check.py` — comprehensive production API health check (used by `health-check.yml` workflow)
- `daily_prod_report.py` — queries CloudWatch Logs Insights for daily digest, publishes to SNS
- `db_backup.sh` / `db_restore.sh` — database backup and restore
- `seed_chargers_bulk.py` — bulk charger seeding from NREL/Overpass
- `seed_merchants_free.py` — merchant seeding for free tier
- `run_migrations.py` — migration runner

### Docker Architecture: x86_64 (AMD64) Only

All Docker images **must** be built for `linux/amd64`. On Apple Silicon Macs, use `--platform linux/amd64`. Do not add ARM/Graviton support or use `--platform linux/arm64` without updating both the App Runner configuration and the CI build steps in `.github/workflows/deploy-prod.yml`.
