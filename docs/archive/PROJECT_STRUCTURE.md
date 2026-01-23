# Nerava Project Structure Documentation

This document provides a comprehensive overview of the Nerava project structure for AI assistants and developers.

## Project Overview

**Nerava** is an EV charging rewards platform that incentivizes users to charge their electric vehicles at specific locations. The platform combines:
- Real-time location verification (GPS-based)
- Purchase reward matching
- Wallet/payment systems
- Merchant partnerships
- "While You Charge" discovery features
- Social features and activity tracking

## High-Level Architecture

The project follows a **full-stack architecture** with:
- **Backend**: FastAPI (Python) REST API
- **Frontend**: Progressive Web App (PWA) with vanilla JavaScript
- **Database**: SQLite (development) / PostgreSQL (production)
- **Deployment**: Kubernetes-ready with Helm charts

```
┌─────────────────┐
│   UI-Mobile     │  ← Progressive Web App (Frontend)
│  (Vanilla JS)   │
└────────┬────────┘
         │ HTTP/API Calls
         ▼
┌─────────────────┐
│  FastAPI Backend│  ← REST API Server
│  (Python 3.8+)  │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────────┐
    ▼         ▼          ▼              ▼
┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
│SQLite/ │ │Redis │ │  Stripe  │ │  Square  │
│Postgres│ │Cache │ │  Payouts │ │ Payments │
└────────┘ └──────┘ └──────────┘ └──────────┘
```

## Directory Structure

### Root Level (`/`)

```
Nerava/
├── nerava-backend-v9/    # Main backend application
├── ui-mobile/            # Frontend PWA
├── charts/               # Kubernetes Helm charts
├── docs/                 # Documentation
├── e2e/                  # End-to-end tests
├── tests/                # Unit and integration tests
├── scripts/              # Utility scripts
├── tools/                # Development tools
├── postman/              # API collection for testing
└── README_*.md           # Various README files
```

---

## Backend Structure (`nerava-backend-v9/`)

The backend is a **FastAPI application** with modular architecture.

### Entry Points

- **`app/main_simple.py`**: Primary entry point for development (used with `uvicorn`)
  - Includes all routers and middleware
  - Serves static files from `ui-mobile/`
  - Mounts routes at `/app/` for frontend
  
- **`app/main.py`**: Full-featured entry point (alternative)
  - Includes lifespan management
  - More complex middleware stack

### Core Application Structure (`app/`)

```
app/
├── __init__.py
├── main.py                 # Full-featured entry point
├── main_simple.py          # Simplified entry point (dev)
├── config.py               # Settings and environment variables
├── db.py                   # Database connection and base
├── dependencies.py         # FastAPI dependency injection
├── lifespan.py             # Application lifecycle events
│
├── routers/                # API route handlers (73 files)
│   ├── health.py           # Health check endpoints
│   ├── wallet.py           # Wallet operations
│   ├── sessions_verify.py  # Location verification sessions
│   ├── gpt.py              # ChatGPT Actions integration
│   ├── while_you_charge.py # EV charger discovery
│   ├── payouts.py          # Payout processing
│   ├── purchase_webhooks.py # Purchase event ingestion
│   ├── merchant_api.py     # Merchant dashboard API
│   └── [70+ more routers]
│
├── services/               # Business logic layer (69 files)
│   ├── wallet_service.py   # Wallet operations
│   ├── verifier.py         # Location verification logic
│   ├── while_you_charge.py # Charger/merchant discovery
│   ├── rewards_engine.py   # Reward calculation
│   ├── fraud.py            # Anti-fraud detection
│   ├── payouts.py          # Payment processing
│   └── [63+ more services]
│
├── models.py               # SQLAlchemy database models (primary)
├── models_while_you_charge.py # WYC-specific models
├── models_demo.py          # Demo/test models
├── models_extra.py         # Extended models
│
├── schemas/                # Pydantic request/response schemas
├── schemas.py              # Legacy schemas
│
├── middleware/             # HTTP middleware stack
│   ├── logging.py          # Request logging
│   ├── metrics.py          # Performance metrics
│   ├── ratelimit.py        # Rate limiting
│   ├── auth.py             # Authentication
│   ├── region.py           # Multi-region routing
│   └── [7 total files]
│
├── security/               # Security utilities
│   ├── JWT handling
│   ├── Password hashing
│   └── [7 files]
│
├── jobs/                   # Background jobs
│   ├── seed_city.py        # Seed charger/merchant data
│   └── [5 files]
│
├── integrations/           # Third-party integrations
│   ├── Google Places API
│   ├── NREL EV charger API
│   ├── Stripe
│   └── Square
│
├── alembic/                # Database migrations
│   ├── env.py
│   └── versions/           # Migration files (16 files)
│
├── tests/                  # Backend unit tests
├── static/                 # Static assets (verify page JS)
└── templates/              # HTML templates (verify page)
```

### Key Backend Components

#### 1. **Routers** (`app/routers/`)
73 route handlers organized by domain:
- **Core**: `health.py`, `wallet.py`, `activity.py`
- **Verification**: `sessions_verify.py`, `verify_api.py`
- **GPT Integration**: `gpt.py` (ChatGPT Actions endpoints)
- **While You Charge**: `while_you_charge.py` (charger discovery)
- **Payments**: `payouts.py`, `stripe_api.py`, `square.py`
- **Merchants**: `merchant_api.py`, `merchant_ui.py`, `merchant_analytics.py`
- **Social**: `social.py`, `activity.py`
- **20 Feature Scaffolds**: Future features (e.g., `ai_rewards.py`, `fleet.py`)

#### 2. **Services** (`app/services/`)
Business logic separated from routing:
- **Wallet**: `wallet_service.py`, `async_wallet.py`, `wallet.py`
- **Verification**: `verifier.py`, `verify_dwell.py`, `verify_api.py`
- **Rewards**: `rewards_engine.py`, `rewards.py`
- **Fraud**: `fraud.py` (anti-abuse detection)
- **Discovery**: `while_you_charge.py`, `discover.py`, `merchants_google.py`
- **Payments**: `payouts.py`, `purchases.py`
- **Geospatial**: `geo.py`, `chargers_openmap.py`

#### 3. **Models** (`app/models*.py`)
SQLAlchemy ORM models:
- **`models.py`**: Primary models (users, sessions, rewards, wallet, merchants)
- **`models_while_you_charge.py`**: Chargers, charger_merchants, merchant_perks
- **`models_demo.py`**: Demo/test data models

Key tables:
- `users` - User accounts
- `verify_sessions` - Location verification sessions
- `wallet_ledger` - Wallet transaction history
- `reward_events` - Reward records (90/10 split)
- `community_pool` - Monthly community pool
- `chargers` - EV charging stations
- `merchants` - Merchant locations
- `charger_merchants` - Junction table (walk times)
- `purchases` - Purchase transactions

#### 4. **Middleware Stack**
Executes in order:
1. `LoggingMiddleware` - Request/response logging
2. `MetricsMiddleware` - Performance tracking
3. `RateLimitMiddleware` - Rate limiting (120 req/min)
4. `RegionMiddleware` - Multi-region support
5. `ReadWriteRoutingMiddleware` - DB read/write splitting
6. `CanaryRoutingMiddleware` - Canary deployments
7. `AuthMiddleware` - Authentication
8. `AuditMiddleware` - Audit logging
9. `DemoBannerMiddleware` - Demo mode banner
10. `CORSMiddleware` - CORS handling

#### 5. **Database Migrations** (`alembic/`)
- **16 migration files** tracking schema changes
- Managed via Alembic CLI: `alembic upgrade head`
- Key migrations:
  - `001_add_performance_indexes.py`
  - `013_while_you_charge_tables.py` - Chargers/merchants tables
  - `014_add_merchant_columns.py`
  - `015_merge_heads.py`

---

## Frontend Structure (`ui-mobile/`)

A **Progressive Web App (PWA)** built with vanilla JavaScript (no frameworks).

### Structure

```
ui-mobile/
├── index.html              # Main entry point
├── manifest.json           # PWA manifest
├── manifest.webmanifest    # PWA manifest (alternate)
├── sw.js                   # Service worker (offline support)
├── styles.css              # Global styles
├── app.js                  # Application bootstrap
│
├── js/
│   ├── app.js              # Main app router
│   ├── pages/              # Page controllers
│   │   ├── explore.js      # Explore tab (map + discovery)
│   │   ├── earn.js         # Earn tab (verification flow)
│   │   ├── wallet.js       # Wallet tab
│   │   ├── activity.js     # Activity feed
│   │   ├── me.js           # Profile page
│   │   └── [other pages]
│   │
│   ├── core/               # Core utilities
│   │   ├── api.js          # API client
│   │   ├── map.js          # Leaflet map integration
│   │   ├── utils.js        # Helper functions
│   │   └── chargerPins.js  # Charger pin rendering
│   │
│   ├── components/         # Reusable components
│   │   ├── modal.js
│   │   ├── toast.js
│   │   └── dealChip.js
│   │
│   └── views/              # Complex view components
│       ├── behaviorCloudView.js
│       └── merchantIntelView.js
│
├── css/                    # Stylesheets (7 files)
├── assets/                 # Images, icons (17 files)
└── tests/                  # Playwright E2E tests
```

### Key Frontend Pages

1. **Explore Tab** (`pages/explore.js`)
   - Interactive map with charger pins
   - "While You Charge" search/discovery
   - Category filters (coffee, food, groceries, gym)
   - Recommended perks card

2. **Earn Tab** (`pages/earn.js`)
   - Location verification flow
   - Session creation and GPS pinging
   - Dwell time tracking

3. **Wallet Tab** (`pages/wallet.js`)
   - Balance display
   - Transaction history
   - Payout requests

4. **Activity Tab** (`pages/activity.js`)
   - Social activity feed
   - Reputation tracking

---

## Key Features & Flows

### 1. **Location Verification Flow**
**Purpose**: Verify users are at a charging location and reward them.

**Flow**:
1. User requests verification session via `/v1/gpt/create_session_link`
2. Backend creates session, returns JWT token and verify URL
3. User opens verify page (requires GPS permission)
4. Frontend pings backend with GPS coordinates (`/v1/sessions/verify/ping`)
5. After 60s dwell time, reward is automatically awarded (90% user, 10% pool)

**Key Files**:
- Backend: `routers/sessions_verify.py`, `services/verifier.py`
- Frontend: `pages/earn.js`, `templates/verify.html`

### 2. **While You Charge Discovery**
**Purpose**: Help users discover merchants near EV chargers while charging.

**Flow**:
1. User opens Explore tab, location is detected
2. Frontend calls `/v1/while_you_charge/search` with location + query
3. Backend queries chargers (NREL API) and nearby merchants (Google Places)
4. Returns ranked merchants with walk times and Nova rewards
5. Map displays charger pins; perks card shows top merchants

**Key Files**:
- Backend: `routers/while_you_charge.py`, `services/while_you_charge.py`
- Frontend: `pages/explore.js`

### 3. **Purchase Reward Matching**
**Purpose**: Match purchase transactions to verified sessions and award rewards.

**Flow**:
1. Merchant sends purchase webhook to `/v1/webhooks/purchase`
2. Backend normalizes event, upserts merchant
3. System matches purchase to eligible verify session (time/radius)
4. Awards flat reward (150¢ default) to user wallet
5. Updates merchant analytics

**Key Files**:
- Backend: `routers/purchase_webhooks.py`, `services/purchases.py`

### 4. **Wallet & Payouts**
**Purpose**: Manage user balances and enable payouts.

**Flow**:
1. Rewards accumulate in `wallet_ledger` table
2. User requests payout via `/v1/payouts/create`
3. Backend debits wallet, initiates Stripe transfer
4. Webhook confirms payment completion

**Key Files**:
- Backend: `routers/payouts.py`, `services/payouts.py`, `services/wallet_service.py`

### 5. **ChatGPT Actions Integration**
**Purpose**: Enable ChatGPT to interact with Nerava via OpenAPI spec.

**Endpoints** (exposed via `/openapi-actions.yaml`):
- `GET /v1/gpt/find_merchants` - Find nearby merchants
- `GET /v1/gpt/find_charger` - Find nearby chargers
- `POST /v1/gpt/create_session_link` - Create verify link
- `GET /v1/gpt/me` - Get user profile

**Key Files**:
- Backend: `routers/gpt.py`, `openapi-actions.yaml`

---

## Configuration & Environment

### Environment Variables (`ENV.example`)

**Database**:
- `DATABASE_URL` - SQLite/PostgreSQL connection string

**API Keys**:
- `NREL_API_KEY` - EV charger data (NREL API)
- `GOOGLE_PLACES_API_KEY` - Merchant discovery
- `STRIPE_SECRET` - Payout processing
- `SQUARE_ACCESS_TOKEN` - Payment processing

**Reward Settings**:
- `VERIFY_REWARD_CENTS` - Verification reward (default: 200¢)
- `PURCHASE_REWARD_FLAT_CENTS` - Purchase reward (default: 150¢)

**Security**:
- `JWT_SECRET` - JWT token signing
- `WEBHOOK_SHARED_SECRET` - Webhook authentication

**Anti-Fraud**:
- `MAX_VERIFY_PER_HOUR` - Rate limiting (default: 6)
- `BLOCK_SCORE_THRESHOLD` - Fraud threshold

**Settings** (`app/config.py`):
- Centralized configuration via Pydantic Settings
- Loads from `.env` file or environment variables

---

## Deployment

### Development

**Start Backend**:
```bash
cd nerava-backend-v9
uvicorn app.main_simple:app --port 8001 --reload
```

**Frontend**:
- Served automatically by backend at `/app/`
- Or run standalone: `python3 -m http.server 8080`

**Database Migrations**:
```bash
cd nerava-backend-v9
alembic upgrade head
```

### Production (Kubernetes)

**Helm Charts** (`charts/`):
- `nerava-api/` - Backend deployment
- `nerava-ui/` - Frontend deployment (optional, if separate)

**Deployment Docs**:
- `DEPLOY.md` - Deployment instructions
- `DEPLOYMENT_READY.md` - Production readiness checklist

---

## Testing

### Backend Tests (`tests/`)
- Unit tests: `tests/unit/`
- API tests: `tests/api/`
- E2E tests: `e2e/tests/`
- Load tests: `e2e/load/`

### Frontend Tests (`ui-mobile/tests/`)
- Playwright E2E tests
- Run: `npm run test:ui`

---

## Key Technologies

**Backend**:
- FastAPI - Web framework
- SQLAlchemy - ORM
- Alembic - Database migrations
- Pydantic - Data validation
- JWT - Authentication

**Frontend**:
- Vanilla JavaScript (no frameworks)
- Leaflet - Map rendering
- Service Worker - Offline support
- Progressive Web App (PWA)

**Integrations**:
- NREL API - EV charger data
- Google Places API - Merchant discovery
- Google Distance Matrix - Walk time calculation
- Stripe - Payout processing
- Square - Payment processing

**Database**:
- SQLite (development)
- PostgreSQL (production)

---

## Database Schema Highlights

### Core Tables

**Users & Sessions**:
- `users` - User accounts
- `verify_sessions` - Location verification sessions
- `verify_pings` - GPS ping history

**Wallet & Rewards**:
- `wallet_ledger` - Transaction history
- `reward_events` - Reward records (with 90/10 split metadata)
- `community_pool` - Monthly community pool balances

**While You Charge**:
- `chargers` - EV charging stations (from NREL)
- `merchants` - Merchant locations (from Google Places)
- `charger_merchants` - Junction table with walk times
- `merchant_perks` - Active rewards/offers

**Purchases**:
- `purchases` - Purchase transactions (from webhooks)
- Matched to `verify_sessions` by time/radius

---

## Development Workflow

### Adding a New Feature

1. **Backend Router**: Create `app/routers/feature_name.py`
2. **Backend Service**: Add logic in `app/services/feature_service.py`
3. **Database Model**: Update `app/models.py` or create migration
4. **API Client**: Update `ui-mobile/js/core/api.js`
5. **Frontend Page**: Update or create `ui-mobile/js/pages/feature.js`

### Running Migrations

```bash
cd nerava-backend-v9
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Seeding Data

**Seed chargers/merchants**:
```bash
python3 -m app.jobs.seed_city --city="Austin" --bbox="30.0,-98.0,30.5,-97.5"
```

---

## Key Scripts

**`scripts/`**:
- `investor_demo.sh` - Demo script for investors
- `verify_ui.sh` - UI verification script

**`tools/`**:
- `ui_hotfix.sh` - Quick UI patches
- `fix_hub_card.sh` - Hub card fixes

**`Makefile`**:
- `make run` - Start backend server
- `make test` - Run tests
- `make clean` - Clean temporary files

---

## Documentation Files

- `README_DEV.md` - Development guide
- `README_WHILE_YOU_CHARGE_DEMO.md` - WYC feature demo
- `PROJECT_STRUCTURE.md` - This file
- `docs/` - Additional documentation:
  - `analytics.md` - Analytics overview
  - `dr.md` - Disaster recovery
  - `multi-dc.md` - Multi-datacenter setup
  - `operations.md` - Operations guide

---

## Common Tasks for AI Assistants

### Understanding the Codebase
1. Start with `app/main_simple.py` to see all routes
2. Check `app/config.py` for configuration
3. Review `app/models.py` for data structure
4. Explore `app/routers/` for API endpoints
5. Check `app/services/` for business logic

### Adding an Endpoint
1. Add route handler in `app/routers/`
2. Add business logic in `app/services/`
3. Update `ui-mobile/js/core/api.js` if frontend needs it
4. Test via Postman collection or `curl`

### Debugging
- Check backend logs for `[WhileYouCharge]`, `[Verify]`, `[Reward]` prefixes
- Frontend logs use `[WhileYouCharge]`, `[Explore]` prefixes
- Debug endpoints: `/debug/rewards`, `/debug/abuse` (dev only)

---

## Important Notes

1. **Reward Split**: All rewards use 90/10 split (90% user, 10% community pool)
2. **Idempotency**: Rewards are idempotent (one per session)
3. **Demo Mode**: `DEMO_MODE=true` relaxes time restrictions for testing
4. **Static Files**: Frontend is served at `/app/` by backend
5. **Migrations**: Always run `alembic upgrade head` after pulling changes
6. **API Versioning**: Routes use `/v1/` prefix

---

This structure supports rapid development of an EV charging rewards platform with real-time verification, purchase matching, and merchant discovery features.

