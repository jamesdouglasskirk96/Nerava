# Nerava Backend v9

FastAPI backend for the Nerava EV charging rewards platform.

## Backend Structure

The backend is a FastAPI application with the following layout:

```text
app/
  main.py / main_simple.py    # entrypoints
  routers/
    ev_smartcar.py            # EV connect, telemetry API
    drivers_domain.py         # driver domain endpoints (nearby merchants, domain views)
    drivers_wallet.py         # driver wallet + nova activity
    merchants.py              # merchant onboarding and management
  services/
    smartcar_service.py       # Smartcar API client (OAuth, vehicle data)
    nova_engine.py            # Nova reward calculation from telemetry
    while_you_charge.py       # charger + merchant aggregation logic
    merchant_onboarding.py    # merchant creation/validation logic
    qr_service.py             # QR token/code resolution
    payments.py               # payment provider integration (Stripe/Square/Toast)
  models/
    user.py                   # User and preferences
    domain.py                 # Domain charge party models (wallet, nova tx, etc.)
    vehicle.py                # Vehicle / Smartcar models
    while_you_charge.py       # charger/merchant models
    extra.py                  # legacy/experimental models
  dependencies/
    __init__.py               # get_db and core deps
    domain.py                 # domain auth deps
    driver.py                 # driver auth deps
```

## Module Structure

The codebase is organized into clear module boundaries:

### Models (`app/models/`)
- `user.py` - User & UserPreferences
- `domain.py` - Domain Charge Party models (Zone, EnergyEvent, DomainMerchant, DriverWallet, NovaTransaction, etc.)
- `vehicle.py` - Smartcar vehicle models (VehicleAccount, VehicleToken, VehicleTelemetry)
- `while_you_charge.py` - WYC models (Charger, Merchant, ChargerMerchant, MerchantPerk)
- `extra.py` - Additional/legacy models (CreditLedger, IncentiveRule, etc.)

**Backward Compatibility:** Old model files (`models.py`, `models_domain.py`, etc.) still work via compatibility imports.

### Dependencies (`app/dependencies/`)
- `__init__.py` - Database session dependency (`get_db`)
- `domain.py` - Domain auth dependencies (get_current_user, require_admin, etc.)
- `driver.py` - Driver-specific dependencies (get_current_driver)

**Backward Compatibility:** Old dependency files (`dependencies.py`, `dependencies_domain.py`, etc.) still work via compatibility imports.

### Routers (`app/routers/`)
Core v1 API routers:
- `ev_smartcar.py` - Smartcar OAuth: `/v1/ev/connect`, `/oauth/smartcar/callback`, `/v1/ev/me/telemetry/latest`
- `drivers_domain.py` - Driver endpoints: join charge events, nearby merchants, redeem nova
- `merchants_domain.py` - Merchant registration/dashboard/redemption
- `nova_domain.py` - Nova grant endpoint
- `auth_domain.py` - Authentication endpoints
- `admin_domain.py` - Admin endpoints

Newly organized routers:
- `drivers_wallet.py` - Driver wallet endpoints (balance, history, redemption)
- `merchants.py` - Merchant onboarding/management endpoints + Square OAuth + reporting
- `checkout.py` - Checkout endpoints (QR scan + Nova redemption)

Legacy routers are preserved for backward compatibility.

### Services (`app/services/`)
Core services:
- `smartcar_service.py` - Smartcar API client (OAuth, token refresh, vehicle/telemetry calls)
- `nova_service.py` - Domain Nova service (DriverWallet, NovaTransaction management)
- `nova_engine.py` - **Pure reward calculation logic** (off-peak vs peak, Nova amount calculation)
- `ev_telemetry.py` - Telemetry polling
- `while_you_charge.py` - Charger ↔ merchant pairing and ranking
- `merchant_onboarding.py` - Merchant creation/validation logic + Square onboarding
- `qr_service.py` - QR/code logic (token → merchant/campaign resolution, status checks) + merchant QR tokens
- `square_service.py` - Square OAuth and merchant data fetching (AOV calculation)
- `square_orders.py` - Square Orders API integration (order lookup, creation, payment for demo)
- `merchant_fee.py` - Merchant fee ledger management (15% fee on Nova redeemed)
- `merchant_signs.py` - PDF sign generation for merchant QR codes
- `merchant_reporting.py` - Merchant summary statistics and shareable social content
- `payments.py` - Payment provider wrapper (Stripe/Square/Toast)

Legacy services (`smartcar_client.py`, `nova.py`, etc.) still work via compatibility imports.

### Legacy (`app/legacy/`)
Unused/experimental code that has been moved here for safe isolation. Safe to delete after manual review.

## Merchant Onboarding & Checkout

### Square Integration

Merchants can connect their Square account to enable Nova rewards for EV drivers:

1. **Square OAuth Flow:**
   - `GET /v1/merchants/square/connect` - Returns Square OAuth authorization URL with CSRF state
   - Merchant authorizes in Square
   - `GET /v1/merchants/square/callback?code=...&state=...` - Completes OAuth and onboards merchant

### Square Order Lookup & Redemption

When a merchant is connected to Square, drivers can select their recent Square orders during checkout:

1. **Order Lookup:**
   - `GET /v1/checkout/orders?token=<qr_token>&minutes=10` - Lists recent Square orders (last 10 minutes)
   - Returns normalized order list with `order_id`, `total_cents`, `display` string
   - If merchant not connected, returns empty orders list (fallback to manual entry)

2. **Redemption with Square Order:**
   - `POST /v1/checkout/redeem` accepts optional `square_order_id`
   - When provided:
     - Fetches order total from Square API
     - Validates order location matches merchant location
     - Prevents duplicate redemption (409 if already redeemed)
     - Records merchant fee (15% of Nova redeemed)
   - Response includes `square_order_id` and `merchant_fee_cents`

3. **Merchant Fee Ledger:**
   - Fees are tracked per merchant per month in `merchant_fee_ledger` table
   - Fee = 15% of total Nova redeemed in the period
   - Status: `accruing` → `invoiced` → `paid`
   - `GET /v1/merchants/{merchant_id}/billing/summary` returns current month's ledger

4. **Demo Endpoints (Swagger):**
   - `POST /v1/demo/square/orders/create` - Create Square sandbox order
   - `POST /v1/demo/square/payments/create` - Create payment for order
   - Requires `DEMO_MODE=true` and `X-Demo-Admin-Key` header
   - Only works in `SQUARE_ENV=sandbox` mode
   - OAuth state is validated to prevent CSRF attacks

2. **Merchant Onboarding:**
   - Square merchant ID and location ID are stored
   - Average order value (AOV) is calculated from Square transaction data
   - Recommended perk is calculated (15% of AOV, rounded to nearest $0.50, capped at $5)
   - QR token is generated for checkout

3. **QR Sign PDF:**
   - `GET /v1/merchants/{merchant_id}/sign.pdf` - Download printable QR sign
   - Merchants can print and display at their counter

4. **Merchant Dashboard:**
   - `GET /v1/merchants/{merchant_id}/summary` - Get redemption statistics
   - `GET /v1/merchants/{merchant_id}/shareables` - Get shareable social media stats

### Driver Checkout Flow

Drivers can redeem Nova at merchant locations:

1. **QR Checkout:**
   - Driver scans merchant QR code
   - `GET /v1/checkout/qr/{token}` - Returns merchant info and driver Nova balance
   - Driver enters order total
   - `POST /v1/checkout/redeem` - Redeems Nova and applies discount
   - Merchant applies discount in Square POS

2. **Web UI:**
   - `/app/checkout.html?token=XYZ` - Checkout interface for drivers
   - Shows merchant name, perk, Nova balance
   - Handles redemption and displays confirmation

### Security Features

- **Token Encryption:** Square access tokens are encrypted at rest using Fernet
- **OAuth State Validation:** CSRF protection via state parameter validation
- **Environment Separation:** Sandbox vs Production Square credentials
- **Token Logging Redaction:** Tokens are redacted in logs

See `RELEASE_NOTES.md` for detailed security enhancements.

## Running Locally

```bash
# from nerava-backend-v9/
# Activate virtual environment (if using one)
source .venv/bin/activate

# Start development server
uvicorn app.main_simple:app --reload --port 8001

# Or using the run script
./run.sh
```

The app will be available at `http://localhost:8001`. Migrations run automatically on startup.

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Structure

#### Unit Tests (`tests/unit/`)
Pure business logic tests with no external dependencies:

- `test_nova_engine.py` - Tests Nova calculation logic (off-peak vs peak, edge cases)
- `test_while_you_charge.py` - Tests merchant ranking/selection logic
- `test_smartcar_service.py` - Tests Smartcar API calls (all HTTP calls mocked)
- `test_merchant_onboarding.py` - Tests merchant creation/validation
- `test_qr_service.py` - Tests QR token resolution and status checks

**All external services are mocked** (Smartcar, Stripe, Google Places, etc.) - no real network calls.

#### Integration Tests (`tests/integration/`)
End-to-end flow tests using FastAPI TestClient:

- `test_ev_connect_flow.py` - EV/Smartcar OAuth connect flow
  - GET `/v1/ev/connect` → Smartcar auth URL
  - OAuth callback → VehicleAccount creation
  
- `test_nova_issuance_flow.py` - Nova issuance from telemetry/sessions
  - Telemetry/session → NovaTransaction creation
  - DriverWallet balance updates
  
- `test_merchant_qr_redemption.py` - QR code redemption flow
  - QR token → Nova debit from driver wallet
  - Redemption record creation

**All external services are mocked** - tests use test database with transaction rollback.

### Test Database

Tests use an in-memory SQLite database (`sqlite:///:memory:`) for complete isolation. Each test gets a fresh database session, and transactions are rolled back after each test.

### What's Mocked in Tests

To keep tests fast and deterministic:

- **Smartcar** is mocked: token exchange, vehicle listing, telemetry responses
- **Stripe / POS providers** are mocked via `payments.py` (no real network calls)
- **Google Places / Distance APIs** are mocked via test doubles for integrations

Integration tests validate:
- EV connect + callback flow
- Telemetry → Nova issuance
- QR redemption + wallet updates
- Edge cases: no vehicle connected, no merchants found, token errors

without hitting real external APIs.

## Key Services Documentation

### nova_engine.py
Pure business logic for calculating Nova rewards.

**Inputs:**
- `kwh`: Energy charged (float, optional)
- `duration_minutes`: Session duration (int, optional)
- `session_time`: When the session occurred (datetime)
- `rules`: List of incentive rules from IncentiveRule model

**Returns:**
- Nova amount (int) - returns 0 if missing data or not in off-peak window

**Behavior:**
- Off-peak sessions (within configured time window) → grant Nova
- Peak sessions → zero Nova
- Missing kWh/duration → returns zero (no crash)

### smartcar_service.py
Wraps Smartcar API endpoints.

**Functions:**
- `exchange_code_for_tokens(code)` - OAuth token exchange
- `refresh_tokens(db, vehicle_account)` - Refresh access token
- `list_vehicles(access_token)` - List user's vehicles
- `get_vehicle_location(access_token, vehicle_id)` - Get vehicle location
- `get_vehicle_charge(access_token, vehicle_id)` - Get charge state

**Error Handling:**
- 401/500 errors raise `httpx.HTTPStatusError` (as per current implementation)
- Token refresh handles expiration automatically

### qr_service.py
QR token → merchant/campaign mapping.

**Functions:**
- `resolve_qr_token(db, token)` - Resolve token to merchant/campaign info (legacy pilot codes)
- `resolve_qr_token(db, token)` - Resolve merchant QR token to DomainMerchant (new national checkout)
- `check_code_status(db, code)` - Check if code is valid/redeemed/expired
- `create_or_get_merchant_qr(db, merchant)` - Create or retrieve QR token for merchant

**Behavior:**
- Valid codes → returns merchant/campaign info
- Expired codes → returns `{"status": "expired", "valid": False}`
- Redeemed codes → returns `{"status": "redeemed", "valid": False}`
- Unknown codes → returns `{"status": "not_found", "valid": False}`

### square_service.py
Square OAuth and merchant data fetching for national merchant onboarding.

**Functions:**
- `get_square_oauth_authorize_url(state)` - Build Square OAuth authorization URL
- `exchange_square_oauth_code(code)` - Exchange OAuth code for access token
- `fetch_square_location_stats(access_token, location_id)` - Fetch AOV from Square orders

**Configuration:**
Requires environment variables:
- `SQUARE_APPLICATION_ID`
- `SQUARE_APPLICATION_SECRET`
- `SQUARE_REDIRECT_URL`
- `SQUARE_ENV` (sandbox or production)

### merchant_onboarding.py
Merchant onboarding logic including Square sync.

**Functions:**
- `onboard_merchant_via_square(db, user_id, square_result)` - Onboard merchant via Square OAuth
- `validate_merchant_location(db, zone_slug, lat, lng)` - Validate merchant location within zone
- `check_duplicate_merchant(db, ...)` - Check for duplicate merchants

**Square Onboarding Flow:**
1. Merchant connects Square account via OAuth
2. System fetches merchant location stats (AOV)
3. Calculates recommended perk (15% of AOV, rounded to nearest $0.50, capped at $5)
4. Generates QR token for checkout
5. Returns merchant info with perk and QR details

### merchant_reporting.py
Merchant summary statistics and shareable social content.

**Functions:**
- `get_merchant_summary(db, merchant_id)` - Aggregate redemption statistics
- `get_shareable_stats(db, merchant_id)` - Generate shareable social media stat lines

### checkout.py Router
Nerava Checkout endpoints for QR-based and discovery-based redemption.

**Endpoints:**
- `GET /v1/checkout/qr/{token}` - Look up merchant and driver balance via QR token
- `POST /v1/checkout/redeem` - Redeem Nova at checkout (debits driver wallet, creates MerchantRedemption)
- `GET /v1/checkout/redemption/{redemption_id}` - Get redemption detail for present screen

## Wallet & Apple Wallet Pass

### Wallet Endpoints

The wallet system provides a complete end-to-end experience for drivers to view their Nova balance, transaction history, and add their wallet to Apple Wallet.

**Endpoints:**
- `GET /v1/wallet` - Get wallet balance (existing endpoint)
- `GET /v1/wallet/timeline?limit=20` - Get unified timeline of earned/spent events
- `GET /v1/wallet/pass/status` - Get Apple Wallet pass refresh status
- `GET /v1/wallet/pass/apple/eligibility` - Check if driver is eligible for Apple Wallet pass
- `POST /v1/wallet/pass/apple/create` - Create Apple Wallet pass (returns signed .pkpass file)
- `POST /v1/wallet/pass/apple/refresh` - Refresh existing Apple Wallet pass (signed only)
- `GET /v1/wallet/pass/apple/preview` - Dev-only unsigned preview (requires `x-nerava-pass-preview=true`)
- `GET /v1/wallet/pass/google/eligibility` - Check if driver is eligible for Google Wallet
- `POST /v1/wallet/pass/google/create` - Create Google Wallet pass/object
- `POST /v1/wallet/pass/google/refresh` - Refresh Google Wallet pass/object

**Timeline Rules:**
- EARNED events come from `NovaTransaction` rows where `type == "driver_earn"`
- SPENT events come from `MerchantRedemption` rows ONLY
- `NovaTransaction` rows with `type == "driver_redeem"` are explicitly excluded to prevent duplicates
- Timeline is ordered newest first

**Example Timeline Response:**
```json
[
  {
    "id": "earn_abc123",
    "type": "EARNED",
    "amount_cents": 500,
    "title": "Off-Peak Charging",
    "subtitle": "Nova issued",
    "created_at": "2025-01-24T12:00:00Z",
    "merchant_id": null,
    "redemption_id": null
  },
  {
    "id": "spent_def456",
    "type": "SPENT",
    "amount_cents": 200,
    "title": "Coffee Shop",
    "subtitle": "Nova applied",
    "created_at": "2025-01-24T11:00:00Z",
    "merchant_id": "merchant_123",
    "redemption_id": "redemption_456"
  }
]
```

### Apple Wallet Pass Configuration

**Environment Variables:**
- `APPLE_WALLET_SIGNING_ENABLED` - Set to `true` to enable pass signing (default: `false`)
- `APPLE_WALLET_TEAM_ID` - Apple Developer Team ID
- `APPLE_WALLET_PASS_TYPE_ID` - Pass Type Identifier (e.g., `pass.com.nerava.wallet`)
- `APPLE_WALLET_CERT_PATH` - Path to Apple Wallet certificate (.pem)
- `APPLE_WALLET_KEY_PATH` - Path to private key (.pem)
- `APPLE_WALLET_KEY_PASSWORD` - Optional password for private key
- `PUBLIC_BASE_URL` - Base URL for web service endpoints (e.g., `https://my.nerava.network`)

**Signing Behavior:**
- When `APPLE_WALLET_SIGNING_ENABLED=false` or certificates are missing, Apple Wallet endpoints return `501 Not Implemented` with error code `APPLE_WALLET_SIGNING_DISABLED`
- PassKit web service (`/v1/wallet/pass/apple/...`) **never** serves unsigned passes; failures surface as `APPLE_WALLET_SIGNING_DISABLED` or `PASS_GENERATION_FAILED`
- Unsigned passes are only available via the dev-only preview endpoint and are served as `application/zip` so they do not masquerade as installable passes

**Security:**
- Barcode payload uses an opaque `wallet_pass_token` (random, stored in DB)
- Serial number is derived from the opaque token (`nerava-<wallet_pass_token>`), never from `user_id` or merchant identifiers
- PassKit `authenticationToken` is a separate opaque secret, stored encrypted-at-rest on `DriverWallet.apple_authentication_token`
- Tokens are generated using `secrets.token_urlsafe(24)`

### Google Wallet

The backend can mirror the driver wallet into Google Wallet using opaque tokens and immediate object updates.

**Flow:**
- `GET /v1/wallet/pass/google/eligibility` checks configuration and returns why it's disabled if not configured
- `POST /v1/wallet/pass/google/create` creates a Google Wallet object linked to the driver's wallet
- `POST /v1/wallet/pass/google/refresh` re-syncs the object after wallet activity

**Behavior:**
- Google Wallet barcode uses the same opaque `wallet_pass_token` as Apple Wallet barcodes (no PII)
- Google Wallet links always direct to `/app/wallet/` for checkout and activity details
- There is no push channel; objects are updated synchronously on wallet activity and refresh calls

**Configuration:**
- `GOOGLE_WALLET_ENABLED=true` - Enable automatic updates on wallet activity
- `GOOGLE_WALLET_ISSUER_ID` - Google Wallet issuer ID
- `GOOGLE_WALLET_CLASS_ID` - Wallet class ID (e.g., `nerava.wallet`)
- `GOOGLE_WALLET_SERVICE_ACCOUNT_JWT` - Pre-signed JWT for Google Wallet REST API calls

### Wallet Activity Tracking

The wallet tracks activity for pass refresh:
- `wallet_activity_updated_at` - Bumped whenever Nova is earned or spent
- `wallet_pass_last_generated_at` - Set when pass is created/refreshed
- `needs_refresh` = `wallet_activity_updated_at > wallet_pass_last_generated_at` (handles None safely)

Activity is automatically marked when:
- Nova is granted via `NovaService.grant_to_driver()`
- Nova is redeemed via `NovaService.redeem_from_driver()`
- Merchant redemption is created via `POST /v1/checkout/redeem`

### Wallet UI

**Web Pages:**
- `/app/wallet/` or `/app/wallet/index.html` - Wallet balance and timeline view
- `/app/wallet/present.html?redemption_id=...` - Redemption present screen
- `/app/checkout.html?token=...` - Checkout flow (updated with wallet links)

**Local Development:**
1. Start backend: `uvicorn app.main_simple:app --reload --port 8001`
2. Open wallet: `http://127.0.0.1:8001/app/wallet/`
3. Open checkout: `http://127.0.0.1:8001/app/checkout.html?token=...`

### Merchant Share Card

**Endpoint:**
- `GET /v1/merchants/{merchant_id}/share-card.png?range=7d` - Generate shareable PNG social card

**Features:**
- Deterministic 1200x630 PNG output
- Uses bundled font (`ui-mobile/assets/fonts/Inter-Regular.ttf`) for CI compatibility
- Works with 0 redemptions (returns valid card)
- Shows merchant name, date range, redemption count, total discount

**Font Setup:**
1. Download Inter-Regular.ttf from https://github.com/rsms/inter/releases
2. Place in `ui-mobile/assets/fonts/Inter-Regular.ttf`
3. Font is licensed under SIL Open Font License (free to use)

## Development

### Environment Setup

#### Production Dependencies

```bash
# Install production dependencies (deterministic, pinned versions)
pip install -r requirements.txt
```

#### Development Dependencies

```bash
# Install development dependencies (includes pytest, freezegun, etc.)
pip install -r requirements-dev.txt

# Or use pip-sync to ensure exact versions match requirements-dev.txt
pip install pip-tools
pip-sync requirements-dev.txt
```

#### Dependency Management

This project uses `pip-tools` for deterministic dependency locking:

- **`requirements.in`** - Direct production dependencies only
- **`requirements-dev.in`** - Development/test dependencies (includes production deps)
- **`requirements.txt`** - Compiled production dependencies with pinned transitive versions (auto-generated)
- **`requirements-dev.txt`** - Compiled dev dependencies with pinned transitive versions (auto-generated)

**To update dependencies:**

1. Edit `requirements.in` or `requirements-dev.in`
2. Regenerate compiled files:
   ```bash
   pip-compile requirements.in
   pip-compile requirements-dev.in
   ```
3. Install updated dependencies:
   ```bash
   pip-sync requirements-dev.txt  # For development
   # OR
   pip install -r requirements.txt  # For production
   ```

**Note:** `httpx` is pinned to `<0.27.0` for compatibility with Starlette's TestClient.

#### Running the Application

```bash
# Run migrations
python -m app.run_migrations

# Start development server
uvicorn app.main_simple:app --reload --port 8001
```

### Code Style

The codebase uses standard Python formatting. Run linters as configured (black, ruff, isort, etc.).

## Merchant Onboarding & Checkout

### Square Sync Flow

Merchants can onboard via Square OAuth:

1. **Initiate Square Connect:**
   ```
   GET /v1/merchants/square/connect?state=optional_state
   ```
   Returns OAuth authorization URL for Square.

2. **Square OAuth Callback:**
   ```
   GET /v1/merchants/square/callback?code=oauth_code&state=state
   ```
   Completes OAuth flow, fetches AOV, calculates perk, generates QR token.

3. **Download QR Sign PDF:**
   ```
   GET /v1/merchants/{merchant_id}/sign.pdf
   ```
   Returns printable PDF with QR code for counter display.

### Nerava Checkout

Drivers can redeem Nova at merchants:

1. **Scan QR / Lookup Merchant:**
   ```
   GET /v1/checkout/qr/{token}
   ```
   Returns merchant info (name, perk) and driver Nova balance.

2. **Redeem Nova:**
   ```
   POST /v1/checkout/redeem
   {
     "qr_token": "merchant_qr_token",
     "order_total_cents": 1200
   }
   ```
   Debits Nova from driver wallet, creates MerchantRedemption record.
   Merchant applies discount manually in Square POS.

### Merchant Reports

Merchants can view statistics:

- `GET /v1/merchants/{merchant_id}/summary` - Aggregated redemption stats
- `GET /v1/merchants/{merchant_id}/shareables` - Shareable social media stat lines

### Environment Variables

For Square integration:
```bash
SQUARE_APPLICATION_ID=your_app_id
SQUARE_APPLICATION_SECRET=your_secret
SQUARE_REDIRECT_URL=https://your-domain.com/v1/merchants/square/callback
SQUARE_ENV=sandbox  # or "production"
```

### Square Sandbox OAuth Testing

Enable end-to-end Square SANDBOX OAuth testing using a public URL for local development.

**Steps:**

1. **Start backend on port 8001:**
   ```bash
   uvicorn app.main_simple:app --reload --port 8001
   ```

2. **Start public tunnel (choose one):**
   ```bash
   # Option 1: Cloudflare Tunnel
   cloudflared tunnel --url http://localhost:8001
   
   # Option 2: ngrok
   ngrok http 8001
   ```

3. **Set environment variables:**
   ```bash
   # Use the tunnel URL from step 2
   export PUBLIC_BASE_URL=https://<tunnel-url>
   export SQUARE_APPLICATION_ID_SANDBOX=sandbox-sq0idb-mql6xZXEwWYsmpYjqCMOCQ
   export SQUARE_APPLICATION_SECRET_SANDBOX=<your-secret>
   # SQUARE_REDIRECT_URL_SANDBOX will default to PUBLIC_BASE_URL/v1/merchants/square/callback
   ```

4. **Get OAuth URL:**
   ```bash
   # Open in browser or curl:
   GET /v1/merchants/square/sandbox/connect
   ```
   Returns:
   ```json
   {
     "url": "https://connect.squareupsandbox.com/oauth2/authorize?...",
     "redirect_uri": "https://<tunnel-url>/v1/merchants/square/callback"
   }
   ```

5. **Configure Square Sandbox:**
   - Copy the `redirect_uri` from step 4
   - Add it to your Square Sandbox application's OAuth redirect URLs in the Square Developer Dashboard

6. **Complete OAuth flow:**
   - Open the `url` from step 4 in your browser
   - Authorize the application in Square Sandbox
   - You'll be redirected back to your callback endpoint

7. **Verify callback succeeds:**
   The callback endpoint (`/v1/merchants/square/callback`) will return:
   ```json
   {
     "success": true,
     "merchant_id": "...",
     "message": "Square sandbox connected",
     "name": "...",
     "perk": {...},
     "qr": {...}
   }
   ```

**Notes:**
- This is SANDBOX ONLY - no production credentials are used
- The `PUBLIC_BASE_URL` is used for OAuth redirects, wallet pass URLs, and QR URLs
- OAuth state is validated for CSRF protection
- Tokens are encrypted at rest and never logged

### Database Migration

New columns added to `domain_merchants` table:
- Square fields: `square_merchant_id`, `square_location_id`, `square_access_token`, `square_connected_at`
- Perk fields: `avg_order_value_cents`, `recommended_perk_cents`, `custom_perk_cents`, `perk_label`
- QR fields: `qr_token`, `qr_created_at`, `qr_last_used_at`

New table: `merchant_redemptions` - tracks Nova redemptions at merchants.

**Migration:** For local/dev, run migrations manually or let Alembic handle it. All new fields are nullable for backward compatibility.

## Notes

- **No API changes:** All public API paths, request/response schemas, and auth behavior remain unchanged (except new endpoints added).
- **Backward compatibility:** Old import paths still work via compatibility stubs.
- **Pure functions:** `nova_engine.py` contains pure business logic with no DB dependencies - easy to test and reason about.
- **Mocked tests:** All unit and integration tests mock external services (no real network calls).
- **National scale:** Merchant onboarding and checkout work for any Square merchant in the U.S., not just within specific geographic zones.

