# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Nerava

Nerava is an EV charging rewards platform that connects drivers at charging stations with nearby merchants offering exclusive deals. The system has a driver-facing app, merchant portal, admin dashboard, landing page, and a FastAPI backend.

## Repository Structure

This is a monorepo with independently deployed apps:

- **`apps/driver`** — Driver mobile/web app (React 19, Vite 7, Tailwind 4, React Router 7, React Query)
- **`apps/merchant`** — Merchant portal (React 18, Vite 5, Radix UI, React Hook Form, Recharts)
- **`apps/admin`** — Admin dashboard (React 18, Vite 5, Radix UI, Recharts)
- **`apps/landing`** — Marketing site (Next.js 14, static export for S3)
- **`apps/link`** — Link redirect app (React 18, Vite 5, minimal)
- **`backend/`** — FastAPI monolith (Python, SQLAlchemy 2, Alembic, Pydantic 2)
- **`packages/analytics`** — Shared PostHog analytics wrapper (`@nerava/analytics`)
- **`Nerava/`** — iOS Xcode project (WKWebView shell wrapping the driver web app)
- **`e2e/`** — Cross-app Playwright E2E tests
- **`infra/terraform/`** — AWS infrastructure (ECS, RDS PostgreSQL, ALB, Route53, CloudWatch)

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
cd apps/driver && npm install && npm run dev     # localhost:5173, proxies /api to :8001
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
cd apps/admin && npm install && npm run dev      # localhost:5175
cd apps/admin && npm run build
cd apps/admin && npm run lint
```

### Landing Page

```bash
cd apps/landing && npm install && npm run dev
cd apps/landing && npm run build                 # Next.js static export
cd apps/landing && npm run lint
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
- **`app/models/`** — SQLAlchemy ORM models. `domain.py` has core models (Zone, EnergyEvent, DomainMerchant, DomainChargingSession, NovaTransaction). Other key models: `user.py`, `arrival_session.py`, `exclusive_session.py`, `tesla_connection.py`.
- **`app/schemas/`** — Pydantic request/response schemas
- **`app/dependencies/`** — FastAPI dependency injection (`get_db`, auth, feature flags)
- **`app/middleware/`** — Auth (JWT), rate limiting, metrics, region routing, audit logging
- **`app/integrations/`** — Third-party clients (Google Places)

### Database

- **Dev:** SQLite (`sqlite:///./nerava.db`)
- **Production:** PostgreSQL on RDS
- **Migrations:** Alembic, run from `backend/` directory. 73+ migration files in `alembic/versions/`.
- **Lazy engine init:** `app/db.py` creates the engine on first access, not at import time. This matters for container health checks.

### Auth Flow

JWT-based authentication with OTP (Twilio Verify) for phone-first login. Apple Sign-In and Tesla OAuth also supported. The `OTP_PROVIDER=stub` env var enables fake OTP in dev.

### Key Integrations

- **Stripe** — Payments and payouts (`app/services/stripe_service.py`)
- **Twilio** — OTP verification (`app/services/auth/twilio_verify.py`)
- **PostHog** — Analytics across all apps (`packages/analytics`)
- **Tesla Fleet API** — Vehicle verification (`app/services/tesla_fleet_api.py`)
- **Google Places** — Merchant enrichment (`app/integrations/google_places_client.py`)
- **Sentry** — Error tracking (initialized in `main_simple.py` when `SENTRY_DSN` is set)

## Frontend Patterns

### Driver App Specifics

- Uses Tailwind 4 (not 3) — different config format than merchant/admin
- Custom design tokens in `tailwind.config.js`: card/button/pill/modal border radii, figma-card shadows
- Vite config validates that no `localhost` or `/api` URLs leak into production builds
- `src/services/api.ts` is the API client; `src/services/schemas.ts` has Zod schemas
- `src/hooks/` for shared stateful logic (onboarding, arrival polling, EV context, native bridge)
- Components follow feature-folder pattern: `src/components/FeatureName/FeatureName.tsx`

### Merchant/Admin Specifics

- Both use Radix UI component primitives + Tailwind 3
- `sonner` for toast notifications in merchant portal
- Merchant portal proxies `/v1` to backend; admin proxies `/api`

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

- **Backend:** `.github/workflows/backend-tests.yml` — pytest on Python 3.10 (triggers on `backend/` changes)
- **Driver app:** `.github/workflows/ci-driver-app.yml` — lint, build, vitest, Playwright (triggers on `apps/driver/` changes)
- **Deploy:** `.github/workflows/deploy-prod.yml` — full production pipeline; `.github/workflows/deploy-driver-app.yml` — Docker build + ECR push
- **Security:** `.github/workflows/codeql-driver-app.yml` — CodeQL scanning

## Infrastructure

- **AWS ECS/Fargate** for container orchestration
- **RDS PostgreSQL** for production database
- **Nginx reverse proxy** routes `/app/` → driver, `/merchant/` → merchant portal, `/admin/` → admin, `/api/` → backend
- **Production startup:** `backend/scripts/start.sh` runs optional Alembic migrations then starts uvicorn on `app.main_simple:app`

### Docker Architecture: x86_64 (AMD64) Only

All Docker images **must** be built for `linux/amd64`. Production Fargate tasks use x86_64 (the default when no `runtime_platform` is specified in ECS task definitions). Do not add ARM/Graviton support or use `--platform linux/arm64` without updating both the ECS task definitions in `infra/terraform/ecs.tf` and the CI build steps in `.github/workflows/deploy-prod.yml`. When writing or modifying Dockerfiles, do not add `--platform` flags that would change the target to ARM.
