## Real-time Verify: Browser GPS + 1-Minute Dwell

1) Create a verify session link

```bash
curl -s -X POST http://localhost:8001/v1/gpt/create_session_link \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"lat":30.2672,"lng":-97.7431}' | jq
```

2) Open the returned `url` in your browser (prompts for location). The page will start and ping automatically.

Debug flow:

```bash
# Start
curl -s -X POST http://localhost:8001/v1/sessions/verify/start \
  -H 'Content-Type: application/json' \
  -d '{"token":"<JWT>","lat":30.2673,"lng":-97.7430,"accuracy_m":20,"ua":"curl"}' | jq

# Ping (repeat to simulate dwell)
curl -s -X POST http://localhost:8001/v1/sessions/verify/ping \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"<sid>","lat":30.26725,"lng":-97.74305,"accuracy_m":18}' | jq
```

# Nerava Development Guide

## How to Run Server

### Prerequisites
- Python 3.8+
- SQLite (included with Python)

### Environment Variables

Key environment variables (see `ENV.example` for full list):

- `DATABASE_URL` - Database connection string (default: `sqlite:///./nerava.db`)
- `PUBLIC_BASE_URL` - Base URL for verify links (default: `http://127.0.0.1:8001`)
- `ALLOWED_ORIGINS` - CORS allowed origins (default: `*` for dev)
- `JWT_SECRET` - Secret key for JWT tokens (default: `dev-secret`)
- `JWT_ALG` - JWT algorithm (default: `HS256`)
- `VERIFY_REWARD_CENTS` - Reward amount in cents for successful verify (default: `200`)
  - Split: 90% to user wallet, 10% to community pool
  - Idempotent: one reward per session

### Quick Start

1. **Navigate to server directory:**
   ```bash
   cd nerava-backend-v9/server
   ```

2. **Start the FastAPI server:**
   ```bash
   python -m uvicorn main_simple:app --port 8001 --reload
   ```

3. **Verify server is running:**
   ```bash
   curl http://127.0.0.1:8001/health
   ```
   Should return: `{"ok":true}`

### Server Features

- **Health Check**: `GET /health` - Returns server status
- **API Routes**: All `/v1/*` endpoints for wallet, activity, payments
- **Static Files**: Serves frontend from `ui-mobile/` directory
- **Database**: SQLite with automatic migrations
- **CORS**: Enabled for development

### Key Endpoints

- `GET /health` - Server health check
- `GET /version` - Version info (git_sha, build_time)
- `GET /debug` - Environment snapshot
- `GET /v1/wallet/summary` - Wallet balance and transactions
- `GET /v1/activity` - User activity and reputation
- `GET /v1/square/payments/test` - Payment system test
- `POST /v1/square/checkout` - Create payment checkout

### GPT & Verify Endpoints

- `POST /v1/gpt/create_session_link` - Create verify session link
  - Body: `{user_id: int, lat?: float, lng?: float, charger_hint?: string}`
  - Returns: `{session_id, url, expires_at}`
- `GET /verify/{token}` - Public verify page (requests GPS, submits location)
- `POST /v1/sessions/locate` - Verify session location (one-time use token)
  - Auth: `Authorization: Bearer <token>`
  - Body: `{lat, lng, accuracy, ts, ua}`
  - Returns: `{verified: true, session_id, message: "ok"}`

### Geo Search Endpoints

- `GET /v1/gpt/find_merchants?lat=<num>&lng=<num>&category=<string?>&radius_m=<int?>`
  - Returns: Array of merchants with distance, offers, sorted by distance
  - Default radius: 1500m
  - Example: `/v1/gpt/find_merchants?lat=30.2672&lng=-97.7431&category=coffee&radius_m=1200`
  - **Deduplication**: Merchants are deduplicated by:
    - Normalized name (lowercase, accents removed, generic suffixes like "coffee" trimmed)
    - Rounded coordinates (lat/lng rounded to 5 decimal places to handle small jitter)
    - When duplicates exist, keeps the merchant with the smallest `distance_m`
  
- `GET /v1/gpt/find_charger?lat=<num>&lng=<num>&radius_m=<int?>`
  - Returns: Array of chargers with green_window and nearby_merchants
  - Default radius: 2000m
  - Example: `/v1/gpt/find_charger?lat=30.2672&lng=-97.7431&radius_m=2000`

- `GET /v1/gpt/me?user_id=<int>`
  - Returns: User profile with handle, followers, following, wallet_cents, monthly earnings
  - Example: `/v1/gpt/me?user_id=1`

- `POST /v1/payouts/create`
  - Create a payout by debiting wallet and initiating Stripe transfer
  - Body: `{user_id: int, amount_cents: int, method: "wallet"|"card_push", client_token?: string}`
  - Returns: `{ok: true, payment_id, status: "paid"|"pending", provider_ref}`
  - Guardrails: min 100¢, max 10,000¢, daily cap 20,000¢
  - Without Stripe keys: returns `status: "paid"` immediately (simulated)
  
- `POST /v1/stripe/webhook`
  - Handle Stripe webhook events to finalize payouts
  - Verifies signature if `STRIPE_WEBHOOK_SECRET` is set
  - Updates payment status from `pending` → `paid` on transfer success

- `POST /v1/webhooks/purchase`
  - Ingest purchase webhooks from Square, CLO, or other providers
  - Normalizes event, upserts merchant, matches to verified session, awards reward
  - Returns: `{ok: true, payment_id, matched_session, claimed}`
  - Requires `X-Webhook-Secret` header if `WEBHOOK_SHARED_SECRET` is set
  
- `POST /v1/purchases/claim`
  - Manually trigger reconciliation for pending purchases (dev/staging only)
  - Body: `{user_id: int, payment_id: int}`
  - Attempts to match payment to eligible session and award reward

- `POST /v1/dev/mock_purchase` (dev only)
  - Mock a purchase webhook for testing
  - Body: `{provider: "square"|"clo", user_id, merchant_name, merchant_ext_id, amount_cents, ts?, city?}`
  - Transforms and forwards to `/v1/webhooks/purchase`

- `GET /debug/abuse?user_id=<int>&limit=10` (dev only)
  - View fraud/risk data: verify attempts, device fingerprints, abuse events, current risk score
  - Requires `APP_ENV != 'prod'`

- `GET /v1/merchant/summary?merchant_id=<int>` (authenticated)
  - Get merchant analytics: verified sessions, purchase rewards, total paid, hourly distribution
  - Requires `X-Merchant-Key` header OR `merchant_id` query param
  
- `GET /v1/merchant/offers?merchant_id=<int>` (authenticated)
  - Get local and external offers for merchant
  - Requires `X-Merchant-Key` header OR `merchant_id` query param
  
- `GET /m/dashboard?merchant_id=<int>`
  - Server-rendered merchant dashboard (HTML)
  - Shows KPIs, hourly activity chart, recent events
  - Only available if `DASHBOARD_ENABLE=true`

### Development Notes

- Server auto-reloads on code changes (`--reload` flag)
- Database migrations run automatically on startup
- Static files served from `../../ui-mobile` (robust path resolution)
- All routes properly imported and functional

### Reward System

The verify reward flow uses a **90/10 split**:
- **90%** → User wallet (`wallet_ledger`)
- **10%** → Community pool for current month (`community_pool`)

**Runtime Schema Adaptation**: The reward system adapts to the existing `reward_events` table schema (legacy support). It uses columns: `source`, `gross_cents`, `net_cents`, `community_cents`, `meta`.

**Idempotency**: Each session can only receive one reward. The system checks for existing rewards before creating new ones.

**Structured Logging**: Reward events are logged with structured JSON format:
```json
{"at":"reward","step":"commit","sid":"session-id","uid":1,"ok":true,"extra":{"user_delta":180,"pool_delta":20},"ts":"2025-10-29T17:00:00Z"}
```

Look for logs with `"at":"reward"` to track reward flow:
- `step: "start"` - Reward process started
- `step: "idempotency_check"` - Checking if already rewarded
- `step: "compute_split"` - Calculated 90/10 split
- `step: "reward_event_inserted"` - reward_events row created
- `step: "wallet_ledger_inserted"` - Wallet credit recorded
- `step: "pool_inserted"` or `step: "pool_updated"` - Community pool updated
- `step: "commit"` - Transaction committed successfully

**Debug Endpoints** (dev only):
- `GET /debug/rewards?user_id=1&limit=5` - View recent rewards and wallet balance
- Requires `APP_ENV != 'prod'`