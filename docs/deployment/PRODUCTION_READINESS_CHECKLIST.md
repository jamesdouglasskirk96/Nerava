# Production Nerava Integration - Implementation Status

## Phase 0: Repo Structure & Normalization ✅ COMPLETE

- [x] Created monorepo structure (`apps/`, `backend/`, `packages/`, `e2e/`)
- [x] Moved `nerava-ui/` → `apps/driver/`
- [x] Moved `landing-page/` → `apps/landing/`
- [x] Extracted `src_merchant.zip` → `apps/merchant/`
- [x] Moved `ui-admin/` → `apps/admin/`
- [x] Moved `nerava-backend-v9/` → `backend/`
- [x] Standardized package.json scripts across all apps
- [x] Created merchant portal config files (vite.config.ts, tsconfig.json, etc.)
- [x] Created docker-compose.yml for local dev orchestration
- [x] Created root README.md with setup instructions
- [x] Environment variable standardization documented

## Phase 1: Landing Page Modernization ✅ COMPLETE

- [x] Updated hero copy: "Nerava — What to do while you charge"
- [x] Updated tagline: "Discover exclusive experiences at charging stations near you"
- [x] Changed primary CTA: "Open Nerava" → routes to driver app
- [x] Changed secondary CTA: "For Businesses" → routes to merchant portal
- [x] Added admin link in footer (hidden/internal, via env var)
- [x] Updated footer links: Privacy, Terms, Contact
- [x] CTAs use environment variables for URLs

## Phase 2: Auth Strategy Implementation ✅ MOSTLY COMPLETE

### Backend ✅
- [x] Enhanced OTP endpoints with rate limiting (per phone + IP)
- [x] Added audit logging to OTP start/verify (`[Auth][OTP]` tags)
- [x] Added merchant Google Business SSO endpoint (`POST /v1/auth/merchant/google`)
- [x] Added admin login endpoint (`POST /v1/auth/admin/login`)
- [x] Added admin Google SSO endpoint (`POST /v1/auth/admin/google`)
- [x] Support for mockable GBP mode via `MOCK_GBP_MODE` env flag

### Frontend ⚠️ PARTIAL
- [x] Driver app: OTP auth already wired (`apps/driver/src/services/auth.ts`)
- [x] Driver app: Token storage in localStorage (documented for future hardening)
- [x] Driver app: Error handling for OTP flows
- [ ] Merchant portal: Google Business SSO wiring (needs frontend implementation)
- [ ] Admin portal: Auth wiring (needs frontend implementation)

## Phase 3: Driver App Production Wiring ⚠️ PARTIAL

### Backend ✅
- [x] Exclusive session endpoints verified (`/v1/exclusive/activate`, `/complete`, `/active`)
- [x] Enhanced exclusive session logging (`[Exclusive][Activate]`, `[Exclusive][Complete]`)
- [x] Added location check endpoint (`GET /v1/drivers/location/check`)
- [x] Location check supports demo static driver mode
- [x] Intent capture endpoint exists (`POST /v1/intent/capture`)
- [x] Merchant detail endpoint exists (`GET /v1/merchants/{merchant_id}`)

### Frontend ⚠️ PARTIAL
- [x] Added build-time check to fail if `VITE_MOCK_MODE=true` in production
- [x] Added exclusive session API functions (`activateExclusive`, `completeExclusive`, `getActiveExclusive`)
- [x] Added location check API function (`checkLocation`)
- [x] Added React Query hooks for exclusive sessions
- [ ] State machine implementation (Pre-charging → Charging → Exclusive Active → Complete)
- [ ] Geolocation hook wired to intent capture API (throttled)
- [ ] Exclusive activation flow wired with charger radius guard
- [ ] Preferences prompt after completion

## Phase 4: Merchant Portal MVP Wiring ⚠️ NOT STARTED

### Backend ⚠️ PARTIAL
- [x] Merchant registration endpoint exists (`POST /v1/merchants/register`)
- [ ] Exclusive management endpoints (create/update/enable/disable)
- [ ] Caps management (daily cap, session cap)
- [ ] Eligibility rules (charging-only, pre-charging routing)
- [ ] Analytics endpoint (`GET /v1/merchants/{merchant_id}/analytics`)

### Frontend ⚠️ NOT STARTED
- [ ] Replace mock data with real API calls
- [ ] Exclusive management forms
- [ ] Caps and eligibility UI
- [ ] Analytics dashboard wiring

## Phase 5: Admin Portal MVP Wiring ⚠️ NOT STARTED

### Backend ⚠️ PARTIAL
- [ ] Admin merchant search endpoint
- [ ] Admin exclusives view endpoint
- [ ] Admin exclusive toggle endpoint
- [x] Demo location override endpoint (via `DEMO_STATIC_DRIVER_ENABLED`)
- [ ] Audit log viewer endpoint

### Frontend ⚠️ NOT STARTED
- [ ] Admin API wiring
- [ ] Admin-only route guards
- [ ] Demo location override UI

## Phase 6: Google Places + Logo Strategy ⚠️ NOT STARTED

- [ ] Image fallback chain implementation
- [ ] `brand_image_url` field added to Merchant model
- [ ] Brand image upload endpoint
- [ ] Merchant brand image upload UI

## Phase 7: Testing + Playwright E2E ⚠️ NOT STARTED

### Backend Unit Tests
- [ ] Exclusive session activation rules tests
- [ ] Completion flow tests
- [ ] Caps enforcement tests
- [ ] OTP auth happy path tests
- [ ] Rate limiting tests
- [ ] Audit logging tests

### Playwright E2E Tests
- [ ] Landing page loads, CTAs route correctly
- [ ] Driver OTP login flow
- [ ] Driver: intent capture → merchant → activate exclusive → complete
- [ ] Merchant: log in → enable exclusive → visible in driver flow
- [ ] Admin: set static location → driver updates
- [ ] CI pipeline with E2E tests

## Production Readiness Checklist

### Completed ✅
- [x] Monorepo structure
- [x] Landing page CTAs
- [x] Backend OTP auth with rate limiting + logging
- [x] Backend merchant/admin auth endpoints
- [x] Backend exclusive session endpoints with logging
- [x] Backend location check endpoint
- [x] Driver app: OTP auth wired
- [x] Driver app: Exclusive session API functions
- [x] Mock mode disabled in production builds (build-time check)
- [x] Environment variable standardization
- [x] Docker compose for local dev

### In Progress ⚠️
- [ ] Driver app: State machine implementation
- [ ] Driver app: Geolocation → intent capture wiring
- [ ] Driver app: Exclusive activation flow completion
- [ ] Merchant portal: Backend exclusive management endpoints
- [ ] Merchant portal: Frontend API wiring
- [ ] Admin portal: Backend endpoints
- [ ] Admin portal: Frontend wiring

### Deferred (Post-MVP)
- [ ] Payment integration (billing)
- [ ] Advanced analytics
- [ ] WebSocket real-time updates
- [ ] Advanced rate limiting (Redis-backed)
- [ ] Token refresh flow hardening
- [ ] Image upload for merchant brand images
- [ ] Comprehensive E2E test coverage

## Next Steps

1. **Complete Driver App State Machine** (Phase 3)
   - Implement 4-state machine (Pre-charging, Charging, Exclusive Active, Complete)
   - Wire geolocation to intent capture with throttling
   - Complete exclusive activation flow with radius guard

2. **Merchant Portal Backend** (Phase 4)
   - Add exclusive management endpoints
   - Add analytics endpoint
   - Wire to MerchantPerk model or create Exclusive model

3. **Merchant Portal Frontend** (Phase 4)
   - Replace mock data with API calls
   - Build exclusive management UI
   - Wire analytics dashboard

4. **Admin Portal** (Phase 5)
   - Add admin endpoints
   - Build admin UI
   - Add route guards

5. **E2E Tests** (Phase 7)
   - Set up Playwright
   - Write smoke tests for critical flows
   - Add CI pipeline

## Environment Variables

### Frontend (.env.local)
```bash
VITE_API_BASE_URL=http://localhost:8001
VITE_MOCK_MODE=false
VITE_ENV=local
```

### Backend (.env)
```bash
DATABASE_URL=sqlite:///./nerava.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175
OTP_PROVIDER=stub
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
GOOGLE_API_KEY=
MOCK_GBP_MODE=false
DEMO_STATIC_DRIVER_ENABLED=false
ENV=dev
```

## Files Modified/Created

### Backend
- `backend/app/routers/auth.py` - Enhanced OTP with rate limiting + logging
- `backend/app/routers/auth_domain.py` - Added merchant/admin auth endpoints
- `backend/app/routers/drivers_domain.py` - Added location check endpoint
- `backend/app/routers/exclusive.py` - Enhanced logging

### Frontend
- `apps/driver/vite.config.ts` - Added build-time mock mode check
- `apps/driver/src/services/api.ts` - Added exclusive session API functions
- `apps/landing/app/components/v2/Hero.tsx` - Updated copy
- `apps/landing/app/components/v2/ctaLinks.ts` - Updated CTA URLs
- `apps/landing/app/components/SiteFooter.tsx` - Added admin/privacy/terms links

### Infrastructure
- `docker-compose.yml` - Created
- `README.md` - Created
- `apps/merchant/` - Created config files (package.json, vite.config.ts, etc.)




