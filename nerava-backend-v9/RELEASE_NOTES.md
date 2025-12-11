# Nerava Backend Release Notes

## v0.2.1-merchant-hardening – Security Hardening & Production Readiness

**Date:** 2025-01-24  
**Tag:** v0.2.1-merchant-hardening

### Security Enhancements

#### Token Encryption
- **Square access tokens are now encrypted at rest** using Fernet symmetric encryption
- New service: `app/services/token_encryption.py` handles encryption/decryption
- Environment variable `TOKEN_ENCRYPTION_KEY` required in production (auto-generated in dev)
- All Square tokens stored in database are encrypted; decryption happens automatically when needed

#### OAuth State Management
- **CSRF protection for Square OAuth flow** via state parameter validation
- New table: `square_oauth_states` tracks OAuth state tokens with expiration (15 minutes)
- States are single-use and validated before processing OAuth callbacks
- Invalid/expired states return `OAUTH_STATE_MISMATCH` error

#### Environment Separation
- **Sandbox vs Production Square credentials** now fully separated
- New environment variables:
  - `SQUARE_APPLICATION_ID_SANDBOX` / `SQUARE_APPLICATION_ID_PRODUCTION`
  - `SQUARE_APPLICATION_SECRET_SANDBOX` / `SQUARE_APPLICATION_SECRET_PRODUCTION`
  - `SQUARE_REDIRECT_URL_SANDBOX` / `SQUARE_REDIRECT_URL_PRODUCTION`
- `SQUARE_ENV` controls which credentials are used (default: "sandbox")

#### Token Logging Redaction
- All Square tokens are redacted in logs (replaced with `[REDACTED_SQUARE_TOKEN]`)
- Error messages no longer leak tokens to clients

### New Database Migration

**Migration:** `022_add_square_and_merchant_redemptions.py`

Adds:
- Square fields to `domain_merchants` (if not already present)
- QR token fields to `domain_merchants` (if not already present)
- Perk configuration fields (if not already present)
- `merchant_redemptions` table (if not already present)
- `square_oauth_states` table for OAuth CSRF protection
- `zone_slug` field (migrated from `domain_zone`)

**To run migration:**
```bash
alembic upgrade head
```

**Backward compatibility:** All new fields are nullable; existing merchants continue to work without Square integration.

### Merchant Web UI

New static HTML pages for merchant onboarding and management:
- `/app/merchant/onboard.html` - Square connection landing page
- `/app/merchant/onboard_success.html` - Post-onboarding success page with QR sign download
- `/app/merchant/dashboard.html` - Merchant dashboard with redemption stats and shareable lines

### Driver Checkout Web UI

New checkout page for drivers:
- `/app/checkout.html?token=XYZ` - QR-based checkout interface
- Shows merchant info, Nova balance, order total input
- Handles redemption and displays success confirmation

### Standardized Error Responses

All merchant and checkout endpoints now return consistent JSON error format:
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable message"
}
```

New error codes:
- `OAUTH_STATE_MISMATCH` - Invalid/expired OAuth state
- `SQUARE_AUTH_FAILED` - Square OAuth exchange failed
- `INVALID_QR_TOKEN` - QR token not found or invalid
- `INSUFFICIENT_NOVA` - Driver doesn't have enough Nova
- `INVALID_MERCHANT_ID` - Invalid merchant ID format
- `MERCHANT_NOT_FOUND` - Merchant doesn't exist
- `INVALID_ORDER_TOTAL` - Order total must be > 0
- `NO_DISCOUNT_AVAILABLE` - No discount configured for merchant
- `WALLET_NOT_FOUND` - Driver wallet not found

### New Tests

#### Security Tests
- `tests/unit/test_token_encryption.py` - Token encryption/decryption roundtrip, invalid cipher handling
- `tests/integration/test_square_oauth_security.py` - OAuth state creation, validation, and mismatch handling

#### UI Smoke Tests
- `tests/integration/test_merchant_ui_flow.py` - Merchant UI pages are accessible

### Updated Tests

- `tests/integration/test_merchant_square_onboarding_flow.py` - Updated to account for token encryption

### New Dependencies

- `cryptography>=41.0.0` - For Fernet token encryption

### Environment Variables

**Required for production:**
- `TOKEN_ENCRYPTION_KEY` - Base64-encoded 32-byte Fernet key (44 characters)
  - Generate with: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`

**Square credentials (sandbox or production based on SQUARE_ENV):**
- `SQUARE_APPLICATION_ID_SANDBOX` / `SQUARE_APPLICATION_ID_PRODUCTION`
- `SQUARE_APPLICATION_SECRET_SANDBOX` / `SQUARE_APPLICATION_SECRET_PRODUCTION`
- `SQUARE_REDIRECT_URL_SANDBOX` / `SQUARE_REDIRECT_URL_PRODUCTION`
- `SQUARE_ENV` - "sandbox" (default) or "production"

### Go-Live Checklist

Before deploying to production:

- [ ] Square sandbox app configured with correct redirect URLs
- [ ] Production Square app created and configured with production redirect URLs
- [ ] `TOKEN_ENCRYPTION_KEY` generated and set in production environment
- [ ] Alembic migrations applied (`alembic upgrade head`)
- [ ] 2+ merchants successfully onboarded via Square sandbox
- [ ] 3+ driver checkouts tested via QR + web UI
- [ ] Database shows encrypted tokens only (verify `square_access_token` values are encrypted)
- [ ] OAuth state mismatch tested manually (should return 400 with `OAUTH_STATE_MISMATCH`)
- [ ] Logs contain no raw tokens (search logs for "sq_" or "access_token")
- [ ] All tests pass: `pytest tests/unit/ -q && pytest tests/integration/ -q`
- [ ] Driver flows still work: Smartcar connect, telemetry → Nova, wallet, discovery

### Breaking Changes

**None** - All changes are backward compatible. Existing merchants without Square continue to work.

---

## v0.2.0-merchant-onboarding – National Merchant Onboarding & Checkout

**Date:** 2025-01-XX  
**Tag:** v0.2.0-merchant-onboarding

### What's New

#### Self-Serve Merchant Onboarding via Square
- Square OAuth integration for merchant account connection
- Automatic average order value (AOV) calculation from Square transaction data
- Automatic perk suggestion based on AOV (15% of AOV, rounded to nearest $0.50, capped at $5)
- Auto-generated merchant QR code for checkout
- Printable QR sign PDF generation

#### Nerava Checkout
- QR-based checkout flow for drivers at merchant locations
- Discovery-based checkout (future: merchants visible in app)
- Nova redemption with automatic wallet debiting
- MerchantRedemption records for tracking

#### Merchant Reporting
- Summary statistics (total redemptions, discount amounts, unique drivers, time-period stats)
- Shareable social media stat lines for merchant marketing

### New Endpoints

#### Merchant Onboarding
- `GET /v1/merchants/square/connect` - Get Square OAuth authorization URL
- `GET /v1/merchants/square/callback` - Complete Square OAuth and onboard merchant
- `GET /v1/merchants/{merchant_id}/sign.pdf` - Download printable QR sign PDF

#### Checkout
- `GET /v1/checkout/qr/{token}` - Look up merchant and driver balance via QR token
- `POST /v1/checkout/redeem` - Redeem Nova at checkout

#### Merchant Reports
- `GET /v1/merchants/{merchant_id}/summary` - Get merchant summary statistics
- `GET /v1/merchants/{merchant_id}/shareables` - Get shareable social media stats

### Database Changes

#### New Columns on `domain_merchants`:
- Square sync: `square_merchant_id`, `square_location_id`, `square_access_token`, `square_connected_at`
- Perk config: `avg_order_value_cents`, `recommended_perk_cents`, `custom_perk_cents`, `perk_label`
- QR fields: `qr_token` (unique, indexed), `qr_created_at`, `qr_last_used_at`

All new columns are nullable for backward compatibility.

#### New Table: `merchant_redemptions`
Tracks Nova redemptions at merchants:
- `id` (UUID string, PK)
- `merchant_id` (FK → domain_merchants.id)
- `driver_user_id` (FK → users.id)
- `qr_token` (optional, for tracking redemption method)
- `order_total_cents` (order total amount)
- `discount_cents` (discount applied)
- `nova_spent_cents` (Nova amount debited)
- `created_at` (timestamp, indexed)

### New Services

- `app/services/square_service.py` - Square OAuth and merchant data fetching (fully mockable)
- `app/services/merchant_signs.py` - PDF sign generation with QR codes
- `app/services/merchant_reporting.py` - Merchant statistics aggregation

### Extended Services

- `app/services/merchant_onboarding.py` - Added `onboard_merchant_via_square()` function
- `app/services/qr_service.py` - Added `create_or_get_merchant_qr()` and merchant QR token resolution

### New Dependencies

- `reportlab>=4.0.0` - PDF generation
- `qrcode[pil]>=7.4.2` - QR code generation

### Environment Variables

New Square configuration variables:
- `SQUARE_APPLICATION_ID` - Square application ID
- `SQUARE_APPLICATION_SECRET` - Square application secret
- `SQUARE_REDIRECT_URL` - OAuth redirect URL (must match Square app config)
- `SQUARE_ENV` - Environment: "sandbox" or "production"

### Testing

#### New Unit Tests
- `tests/unit/test_square_service.py` - Square OAuth and AOV fetching (mocked)
- `tests/unit/test_qr_service_merchant.py` - Merchant QR token creation and resolution
- `tests/unit/test_merchant_reporting.py` - Merchant summary and shareable stats

#### New Integration Tests
- `tests/integration/test_merchant_square_onboarding_flow.py` - End-to-end Square onboarding

All existing tests continue to pass. New tests mock Square API calls.

### Migration Notes

For local/dev databases:
1. Run Alembic migrations (if configured) or manually add new columns/tables
2. All new fields are nullable - existing merchants are unaffected
3. Square fields are only populated when merchants connect via Square OAuth

### Backward Compatibility

- All existing APIs and routes remain unchanged
- New endpoints are additive only
- Legacy QR/code flows (pilot system) remain intact
- Existing merchant records continue to work without Square fields

### Usage Example

**Merchant Onboarding:**
```
1. GET /v1/merchants/square/connect → Returns OAuth URL
2. Merchant authorizes in Square
3. GET /v1/merchants/square/callback?code=... → Creates merchant, calculates perk, generates QR
4. GET /v1/merchants/{merchant_id}/sign.pdf → Download printable sign
```

**Driver Checkout:**
```
1. Driver scans QR code → GET /v1/checkout/qr/{token}
2. Driver confirms order → POST /v1/checkout/redeem with order_total_cents
3. Nova debited, discount applied, redemption recorded
```

---

## v0.1.0-backend-baseline – Initial Refactored Backend

**Date:** 2025-12-11  
**Tag:** v0.1.0-backend-baseline

### What's Included

#### Refactored Module Structure
- **app/models/** with organized model files:
  - `user.py` - User and UserPreferences
  - `domain.py` - Domain Charge Party MVP models (Zone, EnergyEvent, DomainMerchant, DriverWallet, NovaTransaction, etc.)
  - `vehicle.py` - Smartcar integration models (VehicleAccount, VehicleToken, VehicleTelemetry)
  - `while_you_charge.py` - "While You Charge" feature models (Charger, Merchant, ChargerMerchant, MerchantPerk, etc.)
  - `extra.py` - Legacy/experimental models
- **app/dependencies/** with organized dependency files:
  - `__init__.py` - Core dependencies (get_db)
  - `domain.py` - Domain-specific auth dependencies
  - `driver.py` - Driver-specific auth dependencies
- **app/services/** with extracted service logic:
  - `smartcar_service.py` - Smartcar API client (OAuth, vehicle data)
  - `nova_engine.py` - Nova reward calculation from telemetry
  - `merchant_onboarding.py` - Merchant creation/validation logic
  - `qr_service.py` - QR token/code resolution
  - `payments.py` - Payment provider integration (Stripe/Square/Toast)
  - `while_you_charge.py` - Charger + merchant aggregation logic
- **app/routers/** including:
  - `ev_smartcar.py` - EV connect, telemetry API
  - `drivers_domain.py` - Driver domain endpoints (nearby merchants, domain views)
  - `drivers_wallet.py` - Driver wallet + nova activity
  - `merchants.py` - Merchant onboarding and management
- Backwards-compatible imports for legacy model/dep files.

### Verified Core Flows (Backed by Tests)

#### EV Connect Flow
- `/v1/ev/connect` → Smartcar OAuth redirect
- Smartcar callback → vehicle account linking (mocked in tests)
- `/v1/ev/me/telemetry/latest` → returns 404 when no vehicle connected

#### Telemetry → Nova Issuance
- Off-peak telemetry → Nova rewards calculated in `nova_engine.py`
- Nova balance and transactions via DriverWallet / NovaTransaction

#### Merchant & QR Flows
- Domain "while you charge" flow: chargers + merchants aggregation
- QR redemption path via `qr_service.py` (mocked POS/payment)
- Driver wallet + activity endpoints (drivers_wallet router)
- Empty merchant list handling (no crashes, returns empty list)

### Tests

#### New Unit Tests (45 tests):
- `tests/unit/test_nova_engine.py` - Nova reward calculation logic
- `tests/unit/test_while_you_charge.py` - Merchant ranking and filtering (including empty lists)
- `tests/unit/test_smartcar_service.py` - Smartcar API client with error handling
- `tests/unit/test_merchant_onboarding.py` - Merchant registration
- `tests/unit/test_qr_service.py` - QR code resolution

#### New Integration Tests (6 tests):
- `tests/integration/test_ev_connect_flow.py` - EV/Smartcar OAuth flow
- `tests/integration/test_nova_issuance_flow.py` - Nova issuance from telemetry
- `tests/integration/test_merchant_qr_redemption.py` - QR redemption flow
- `tests/integration/test_ev_no_vehicle.py` - No vehicle connected edge case

All new tests are currently passing (51 total).

### Notes

- External services (Smartcar, Stripe/POS, Google Places) are mocked in tests.
- Some older/legacy routes and jobs still exist and are not fully covered by tests yet.
- Error handling for Smartcar token errors and edge cases (no vehicle, no merchants) is now explicitly tested.


