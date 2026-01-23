# Nerava - Production System

**Nerava — What to do while you charge.**

A production-ready monorepo integrating landing page, driver app, merchant portal, admin portal, and backend.

## Architecture

```
/nerava/
├── apps/
│   ├── landing/          # Next.js landing page (port 3000)
│   ├── driver/           # React/Vite driver app (port 5173)
│   ├── merchant/         # React/Vite merchant portal (port 5174)
│   └── admin/            # React/Vite admin portal (port 5175)
├── backend/              # FastAPI backend (port 8001)
├── packages/
│   └── shared/           # Shared types, API client, UI primitives
├── e2e/                  # Playwright E2E tests
├── docs/                 # Documentation (see docs/README.md)
└── docker-compose.yml    # Local dev orchestration
```

## Documentation

See [docs/README.md](./docs/README.md) for full documentation including:
- Deployment guides
- Architecture documentation
- API documentation
- Security guidelines

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Docker and Docker Compose (optional, for containerized dev)

### Local Production Demo with Docker

Run the entire stack in production mode with Docker Compose:

```bash
# Build and start all services
make up

# Or use docker-compose directly
docker-compose up --build

# Stop all services and remove volumes
make down

# View logs
make logs

# Run health checks
make health
```

**Access URLs:**
- Landing: http://localhost/
- Driver App: http://localhost/app/
- Merchant Portal: http://localhost/merchant/
- Admin Portal: http://localhost/admin/
- Backend API: http://localhost/api/v1/...
- API Docs: http://localhost/api/docs

**Health Endpoints:**
- Proxy: http://localhost/health
- Backend: http://localhost/api/health
- Landing: http://localhost/landing/health
- Driver: http://localhost/app/health
- Merchant: http://localhost/merchant/health
- Admin: http://localhost/admin/health

The Docker setup includes:
- Production builds (no dev servers)
- Nginx reverse proxy routing
- Health checks for all services
- Proper base path configuration for SPAs
- CORS configuration for API access

### One-Command Local Dev (Non-Docker)

```bash
# Or run individually:
# Terminal 1: Backend
cd backend && python -m uvicorn app.main_simple:app --reload --port 8001

# Terminal 2: Landing
cd apps/landing && npm run dev

# Terminal 3: Driver
cd apps/driver && npm run dev

# Terminal 4: Merchant
cd apps/merchant && npm run dev

# Terminal 5: Admin
cd apps/admin && npm run dev
```

### Environment Variables

#### Frontend Apps

Create `.env.local` in each app directory:

```bash
# apps/driver/.env.local
VITE_API_BASE_URL=http://localhost:8001
VITE_MOCK_MODE=false
VITE_ENV=local

# apps/merchant/.env.local
VITE_API_BASE_URL=http://localhost:8001
VITE_MOCK_MODE=false
VITE_ENV=local

# apps/admin/.env.local
VITE_API_BASE_URL=http://localhost:8001
VITE_MOCK_MODE=false
VITE_ENV=local
```

#### Backend

Create `backend/.env`:

```bash
DATABASE_URL=sqlite:///./nerava.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175
OTP_PROVIDER=stub  # or twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
GOOGLE_API_KEY=
MOCK_GBP_MODE=false
DEMO_STATIC_DRIVER_ENABLED=false
ENV=dev
```

## Development

### Standard Scripts

All frontend apps support:
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Lint code
- `npm run test` - Run tests

Backend supports:
- `python -m uvicorn app.main_simple:app --reload` - Start dev server
- `pytest` - Run tests
- `alembic upgrade head` - Run migrations

### Ports

- Landing: http://localhost:3000
- Driver: http://localhost:5173
- Merchant: http://localhost:5174
- Admin: http://localhost:5175
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## Production Build

```bash
# Build all frontend apps
cd apps/landing && npm run build
cd apps/driver && npm run build
cd apps/merchant && npm run build
cd apps/admin && npm run build

# Backend is ready to deploy (see backend/README.md)
```

## Testing

### E2E Tests

```bash
cd e2e
npm install
npm run test
```

### Backend Tests

```bash
cd backend
pytest
```

## Key Features

- **Driver App**: OTP SMS auth, geolocation-based intent capture, exclusive session activation
- **Merchant Portal**: Google Business SSO, exclusive management, analytics
- **Admin Portal**: Merchant management, demo location override, audit logs
- **Landing Page**: Modern marketing site with CTAs to driver/merchant portals

## Production Readiness

- ✅ Monorepo structure
- ✅ Standardized scripts
- ✅ Environment variable management
- ✅ Mock mode disabled in production builds
- ✅ Real API wiring (no hardcoded mocks)
- ✅ Auth flows (OTP, SSO)
- ✅ E2E tests

## License

See LICENSE file.

