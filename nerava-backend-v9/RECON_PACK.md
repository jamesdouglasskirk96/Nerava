# Nerava Recon Pack

> **Generated**: 2025-12-15
> **Purpose**: Comprehensive system documentation for onboarding engineers without repo access

---

## 1. Repo Map

### Top-Level Directory Structure

```
Nerava/
├── nerava-backend-v9/           # Primary Python/FastAPI backend
│   ├── app/                     # Application code
│   │   ├── routers/             # FastAPI routers (60+ endpoints)
│   │   ├── services/            # Business logic services
│   │   ├── models/              # SQLAlchemy models (domain.py, user.py, extra.py)
│   │   ├── middleware/          # CORS, auth, logging, rate limiting
│   │   ├── dependencies/        # FastAPI dependencies (driver.py, domain.py)
│   │   ├── core/                # Security, config
│   │   └── static/              # Static assets for verify pages
│   ├── tests/                   # Pytest test suite
│   │   ├── unit/                # Unit tests
│   │   └── integration/         # Integration tests
│   ├── alembic/                 # Database migrations
│   └── scripts/                 # Seed scripts, utilities
├── ui-mobile/                   # PWA frontend (vanilla JS)
│   ├── js/pages/                # Page-specific JS (wallet.js, checkout.js)
│   ├── css/                     # Stylesheets
│   └── img/                     # Static images
├── charger-portal/              # Next.js charger management UI
├── mobile/nerava_flutter/       # Flutter mobile app (development)
└── docs/                        # Documentation
```

---

## 2. Entry Points & Routing

### Backend Entry Points

| File | Purpose | When Used |
|------|---------|-----------|
| `app/main_simple.py` | **Production entry point** | Railway deployment, local dev |
| `app/main.py` | Legacy entry point | Not actively used |

### Key Characteristics of `main_simple.py`

1. **Runs migrations on startup** (`run_migrations()` before router imports)
2. **Mounts UI at `/app`** from `ui-mobile/` directory
3. **Registers 60+ routers** including all domain, demo, and feature scaffold routers
4. **Custom exception handlers** normalize errors for pilot/PWA endpoints
5. **Nova accrual service** starts on startup (demo mode)

### Critical Router Registration Order

```python
# Order matters for route matching:
app.include_router(demo_qr.router)      # /qr/eggman-demo-checkout FIRST
app.include_router(checkout.router)      # /qr/{token} SECOND (wildcard)
app.include_router(demo_square.router)   # /v1/demo/square/*
```

---

## 3. Environment Variables by Subsystem

### 3.1 Apple Wallet / PassKit / APNs

| Variable | Purpose | Required |
|----------|---------|----------|
| `APPLE_WALLET_SIGNING_ENABLED` | Enable pkpass signing (`true`/`false`) | For production |
| `APPLE_WALLET_CERT_PATH` | Path to signing certificate (.pem) | For production |
| `APPLE_WALLET_KEY_PATH` | Path to private key (.pem) | For production |
| `APPLE_WALLET_KEY_PASSWORD` | Private key password | Optional |
| `APPLE_WALLET_PASS_TYPE_ID` | Pass type identifier (e.g., `pass.com.nerava.wallet`) | Yes |
| `APPLE_WALLET_TEAM_ID` | Apple Developer Team ID | Yes |
| `APPLE_PASS_PUSH_ENABLED` | Enable APNs push (`true`/`false`) | For live updates |
| `APPLE_WALLET_APNS_KEY_ID` | APNs auth key ID | For push |
| `APPLE_WALLET_APNS_AUTH_KEY_PATH` | Path to APNs auth key (.p8) | For push |
| `APPLE_WALLET_APNS_TOPIC` | APNs topic (pass type ID) | For push |
| `APPLE_WALLET_APNS_ENV` | APNs environment (`sandbox`/`production`) | For push |

### 3.2 Google Wallet

| Variable | Purpose | Required |
|----------|---------|----------|
| `GOOGLE_WALLET_ENABLED` | Enable Google Wallet (`true`/`false`) | No |
| `GOOGLE_WALLET_ISSUER_ID` | Google Wallet issuer ID | For Google Wallet |
| `GOOGLE_WALLET_SERVICE_ACCOUNT_JSON` | Service account credentials | For Google Wallet |

### 3.3 Square

| Variable | Purpose | Required |
|----------|---------|----------|
| `SQUARE_ENV` | Environment (`sandbox`/`production`) | Yes |
| `SQUARE_APPLICATION_ID` | Square application ID | Yes |
| `SQUARE_APPLICATION_SECRET` | Square OAuth client secret | Yes |
| `SQUARE_REDIRECT_URL` | OAuth callback URL | Yes |
| `SQUARE_ACCESS_TOKEN` | (Legacy) Direct token | No |
| `SQUARE_LOCATION_ID` | (Legacy) Default location | No |

### 3.4 Demo Mode

| Variable | Purpose | Default |
|----------|---------|---------|
| `DEMO_MODE` | Enable demo features | `false` |
| `DEMO_ADMIN_KEY` | Header key for demo endpoints | Required if DEMO_MODE |
| `DEMO_QR_ENABLED` | Enable demo QR redirect | `false` |
| `DEMO_EGGMAN_QR_TOKEN` | Demo merchant QR token | Required if demo QR |
| `DEMO_EGGMAN_SQUARE_MERCHANT_ID` | Demo merchant Square ID | Optional |

### 3.5 Token Encryption

| Variable | Purpose | Required |
|----------|---------|----------|
| `TOKEN_ENCRYPTION_KEY` | Fernet key for encrypting tokens (44 chars base64) | **Production** |
| `ENVIRONMENT` | `production`/`prod` triggers key requirement | Yes |

### 3.6 Core Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL or SQLite URL | `sqlite:///./nerava.db` |
| `PUBLIC_BASE_URL` | Public URL for callbacks/QR | `http://127.0.0.1:8001` |
| `FRONTEND_URL` | Frontend URL for redirects | `http://localhost:8001/app` |
| `NERAVA_SECRET_KEY` | JWT signing secret | `dev-secret-change-me` |
| `PLATFORM_FEE_BPS` | Merchant fee in basis points | `1500` (15%) |

### 3.7 Development Flags

| Variable | Purpose | Default |
|----------|---------|---------|
| `NERAVA_DEV_ALLOW_ANON_DRIVER` | Allow unauthenticated drivers | `false` |
| `DEBUG_RETURN_MAGIC_LINK` | Return magic link in response | `false` |

---

## 4. Data Model

### 4.1 DriverWallet

```python
# Primary Key: user_id (FK to users.id)
class DriverWallet:
    user_id: int                        # PK, FK
    nova_balance: int                   # Cents (e.g., 500 = $5.00)
    energy_reputation_score: int        # Unused currently

    # Apple Wallet Pass
    wallet_pass_token: str              # UNIQUE, opaque token for barcode
    wallet_activity_updated_at: datetime # Bumped on earn/spend
    wallet_pass_last_generated_at: datetime # When pkpass was created
    apple_authentication_token: str     # ENCRYPTED PassKit auth token

    # Demo charging
    charging_detected: bool             # Demo: currently charging
    charging_detected_at: datetime      # When charging detected
```

**Key Indexes**: `wallet_pass_token` (unique)

### 4.2 NovaTransaction

```python
class NovaTransaction:
    id: str                    # UUID
    type: str                  # driver_earn, driver_redeem, merchant_earn, merchant_topup, admin_grant
    driver_user_id: int        # FK to users.id (nullable)
    merchant_id: str           # FK to domain_merchants.id (nullable)
    amount: int                # Always positive; type indicates direction
    session_id: str            # FK to charging sessions (nullable)
    event_id: str              # FK to energy_events (nullable)
    stripe_payment_id: str     # FK for merchant purchases (nullable)
    transaction_meta: JSON     # Flexible metadata
    created_at: datetime       # INDEXED
```

**Key Indexes**: `driver_user_id`, `merchant_id`, `type + created_at`

### 4.3 MerchantRedemption

```python
class MerchantRedemption:
    id: str                    # UUID
    merchant_id: str           # FK to domain_merchants.id
    driver_user_id: int        # FK to users.id
    qr_token: str              # QR token used (nullable)
    reward_id: str             # FK to merchant_rewards (nullable)
    order_total_cents: int     # Original order total
    discount_cents: int        # Discount applied
    nova_spent_cents: int      # Nova driver spent
    square_order_id: str       # Square order ID (nullable)
    created_at: datetime       # INDEXED
```

**Double-Redemption Prevention**:
- `UNIQUE INDEX (merchant_id, square_order_id)` - prevents same Square order being redeemed twice

### 4.4 DomainMerchant

```python
class DomainMerchant:
    id: str                    # UUID
    name: str
    lat, lng: float            # Location
    zone_slug: str             # e.g., "domain_austin"
    status: str                # pending, active, flagged, suspended
    nova_balance: int          # Merchant's Nova balance (cents)

    # Square OAuth
    square_merchant_id: str    # Square merchant ID
    square_location_id: str    # Square location ID
    square_access_token: str   # ENCRYPTED access token
    square_connected_at: datetime

    # Perk configuration
    avg_order_value_cents: int
    recommended_perk_cents: int
    custom_perk_cents: int
    perk_label: str            # e.g., "$3 off any order"

    # QR
    qr_token: str              # UNIQUE, for printed QR codes
```

### 4.5 ApplePassRegistration

```python
class ApplePassRegistration:
    id: str                         # UUID
    driver_wallet_id: int           # FK to driver_wallets.user_id
    device_library_identifier: str  # Apple device ID
    push_token: str                 # APNs push token
    pass_type_identifier: str       # e.g., pass.com.nerava.wallet
    serial_number: str              # e.g., "nerava-<wallet_pass_token>"
    is_active: bool                 # Soft delete
    created_at, last_seen_at: datetime
```

### 4.6 MerchantFeeLedger

```python
class MerchantFeeLedger:
    id: str                    # UUID
    merchant_id: str           # FK
    period_start: date         # First day of month
    period_end: date           # Last day of month
    nova_redeemed_cents: int   # Total Nova redeemed this period
    fee_cents: int             # 15% of nova_redeemed_cents
    status: str                # accruing, invoiced, paid
```

**Constraint**: `UNIQUE (merchant_id, period_start)`

---

## 5. Key Flows

### Flow A: Driver Wallet Web Load (`/app/wallet/`)

```
1. User navigates to /app/wallet/ (or /app/)
2. PWA loads wallet.js
3. wallet.js calls GET /v1/wallet/timeline
   - Auth: Bearer token from localStorage OR cookie
   - Returns: [{id, type, amount_cents, title, subtitle, created_at, merchant_id}]
4. wallet.js calls GET /v1/wallet/status (charging detection)
5. wallet.js calls GET /v1/drivers/me/wallet (balance)
6. UI renders balance + timeline

wallet_activity_updated_at: Bumped by mark_wallet_activity() on earn/spend
```

### Flow B: QR Scan → Checkout Page

```
1. Driver scans printed QR → opens /qr/{token} or /qr/eggman-demo-checkout
2. If eggman-demo-checkout: demo_qr.py redirects to /app/checkout.html?token=<DEMO_TOKEN>
3. checkout.html loads with token from URL
4. Frontend calls GET /v1/checkout/qr/{token}
   - Backend: resolve_merchant_qr_token() looks up DomainMerchant by qr_token
   - Returns: {merchant: {id, name, perk_label, reward}, driver: {connected, nova_balance_cents}}
5. If Square connected, calls GET /v1/checkout/orders?token={token}&minutes=10
   - Backend: search_recent_orders() calls Square API
   - Returns: {orders: [{order_id, display, total_cents}]}
6. UI shows merchant info, orders list, balance
```

### Flow C: Checkout → Redeem 300 Nova

```
1. Driver selects order (or enters manual amount)
2. Frontend calls POST /v1/checkout/redeem
   Body: {qr_token, order_total_cents, square_order_id?}

3. Backend (checkout.py:redeem_nova):
   a. resolve_merchant_qr_token(token) → merchant
   b. If square_order_id:
      - get_order_total_cents() → validate order exists
      - Check MerchantRedemption for duplicate (409 if exists)
   c. Get driver wallet, calculate redeem_cents = min(perk, balance, order_total)
   d. NovaService.redeem_from_driver():
      - wallet.nova_balance -= amount
      - merchant.nova_balance += amount
      - Create NovaTransaction (driver_redeem)
      - Create NovaTransaction (merchant_earn)
   e. Create MerchantRedemption record
   f. record_merchant_fee() → MerchantFeeLedger (15%)
   g. mark_wallet_activity() → bumps wallet_activity_updated_at

4. Returns: {success, redemption_id, discount_cents, remaining_nova_cents, message}
```

### Flow D: Redemption Present Screen

```
1. After redeem, frontend navigates to /app/present.html?id={redemption_id}
2. Frontend calls GET /v1/checkout/redemption/{redemption_id}
   - Auth required
   - Validates driver_user_id matches
3. Returns: {redemption_id, merchant_name, discount_cents, order_total_cents, created_at}
4. UI shows "Show this screen to merchant" with discount amount
```

### Flow E: Merchant Dashboard

```
1. Merchant admin logs in, navigates to /app/merchant/dashboard
2. Frontend calls GET /v1/merchants/me
   - Auth: require_merchant_admin dependency
   - Returns: {merchant: {..., nova_balance}, transactions: [...]}
3. For billing: GET /v1/merchants/{id}/billing/summary
   - Returns current month ledger: {nova_redeemed_cents, fee_cents, status}
```

### Flow F: Apple Wallet Pass (PassKit Web Service)

```
PASS CREATION:
1. Driver connects EV via Smartcar
2. Driver taps "Add to Apple Wallet"
3. Frontend calls POST /v1/wallet/pass/apple/create
4. Backend (wallet_pass.py):
   a. Check VehicleAccount exists (eligibility)
   b. Check APPLE_WALLET_SIGNING_ENABLED + certs exist
   c. create_pkpass_bundle():
      - _ensure_wallet_pass_token() → generate opaque token
      - _ensure_apple_auth_token() → generate + encrypt auth token
      - Build pass.json with balance, timeline, barcode (wallet_pass_token)
      - Sign with PKCS#7
   d. Update wallet_pass_last_generated_at
5. Return: application/vnd.apple.pkpass

DEVICE REGISTRATION (Apple calls these):
POST /v1/wallet/pass/apple/devices/{deviceLibId}/registrations/{passTypeId}/{serial}
- Serial format: "nerava-{wallet_pass_token}"
- Body: {pushToken}
- Validates: AuthenticationToken header matches stored encrypted token
- Creates/updates ApplePassRegistration
- Returns: 201 (empty body)

DELETE /v1/wallet/pass/apple/devices/{deviceLibId}/registrations/{passTypeId}/{serial}
- Soft-deletes registration (is_active=false)
- Returns: 200

LIST UPDATED SERIALS (Apple polls this):
GET /v1/wallet/pass/apple/devices/{deviceLibId}/registrations/{passTypeId}?passesUpdatedSince={ts}
- Returns: {serialNumbers: [...], lastUpdated: unix_timestamp}
- Filters by wallet_activity_updated_at > passesUpdatedSince

FETCH UPDATED PASS:
GET /v1/wallet/pass/apple/passes/{passTypeId}/{serial}
- Validates AuthenticationToken
- Returns fresh signed pkpass
- Updates wallet_pass_last_generated_at

APNS PUSH (backend-initiated):
- On mark_wallet_activity(), if APPLE_PASS_PUSH_ENABLED:
  - send_updates_for_wallet() sends silent push to all active registrations
  - Apple Wallet then calls GET registrations → GET pass
```

### Flow G: Google Wallet

```
1. Driver taps "Add to Google Wallet"
2. Frontend calls POST /v1/wallet/pass/google/create
3. Backend:
   a. ensure_google_wallet_class() → create class if needed
   b. create_or_get_google_wallet_object() → create object with barcode
   c. generate_google_wallet_add_link() → signed JWT URL
4. Returns: {object_id, state, add_to_google_wallet_url}
5. User clicks URL → adds to Google Wallet

UPDATE ON ACTIVITY:
- On mark_wallet_activity(), if GOOGLE_WALLET_ENABLED:
  - update_google_wallet_object_on_activity() updates object immediately
- No push needed (Google syncs automatically)
```

### Flow H: Demo Charging Detection/Accrual

```
START CHARGING:
1. (Demo) User triggers charging detection
2. Frontend calls POST /v1/demo/charging/start
   - Gated: DEMO_MODE=true OR DEMO_QR_ENABLED=true
3. Backend:
   a. wallet.charging_detected = True
   b. wallet.charging_detected_at = now()
   c. mark_wallet_activity()
4. Returns: {status: "OK", charging_detected: true}

ACCRUAL:
- nova_accrual_service runs in background (started on app startup)
- Periodically grants Nova to wallets where charging_detected=True
- Calls NovaService.grant_to_driver()

STOP CHARGING:
- POST /v1/demo/charging/stop sets charging_detected = False

WALLET STATUS:
- GET /v1/wallet/status returns charging state for UI banner
```

---

## 6. PassKit Compliance

### Specification Validation

| Endpoint | Spec Requirement | Implementation | Status |
|----------|------------------|----------------|--------|
| POST registration | Return 201, empty body | `return Response(status_code=201)` | **COMPLIANT** |
| DELETE registration | Return 200 | `return Response(status_code=200)` | **COMPLIANT** |
| GET registrations | Return `{serialNumbers, lastUpdated}` | Returns with unix timestamp | **COMPLIANT** |
| GET pass | Return signed pkpass | Content-Type `application/vnd.apple.pkpass` | **COMPLIANT** |
| passesUpdatedSince | Filter by timestamp | Filters by `wallet_activity_updated_at` | **COMPLIANT** |
| lastUpdated | Unix timestamp string | `str(now_ts)` | **COMPLIANT** |
| AuthenticationToken | Validate per-pass | Encrypted token comparison | **COMPLIANT** |

### Deviations/Notes

1. **Serial Number Format**: Uses `nerava-{wallet_pass_token}` prefix (compliant, just a convention)
2. **Authentication Storage**: Token is encrypted at rest (Fernet) - good practice
3. **Push Notifications**: Uses APNs HTTP/2 via `apns2` library - correct
4. **Signing**: Uses PKCS#7 via cryptography library - correct algorithm

---

## 7. Security Findings

### 7.1 Token Encryption

**Location**: `app/services/token_encryption.py`

```python
# Key loading
key_str = os.getenv("TOKEN_ENCRYPTION_KEY", "")
if not key_str and is_prod:
    raise ValueError("TOKEN_ENCRYPTION_KEY required in production")
```

**Tokens Encrypted**:
- `DomainMerchant.square_access_token`
- `DriverWallet.apple_authentication_token`

**Rotation Handling**:
- **ISSUE**: No key rotation mechanism. If key changes, all encrypted tokens become unreadable.
- **Mitigation**: Token decryption failures in `_ensure_apple_auth_token` regenerate a new token.
- **Recommendation**: Implement multi-key decryption (try current, then old key).

### 7.2 Square Token Decryption

**Location**: `app/services/square_orders.py:get_square_token_for_merchant()`

```python
try:
    token = decrypt_token(merchant.square_access_token)
except TokenDecryptionError as e:
    raise SquareNotConnectedError(f"Failed to decrypt Square token: {e}")
```

**Failure Modes**:
- Key mismatch → `TokenDecryptionError` → `SquareNotConnectedError`
- Empty token → `SquareNotConnectedError`
- Merchant can re-OAuth to fix

### 7.3 Logging Redaction

**Findings**:
- `access_token` is logged only at schema level (response shape), not values
- `authenticationToken` is never logged
- `push_token` is not redacted but is device-specific (low risk)
- `Authorization` headers are not logged in request middleware

**Recommendation**: Add explicit redaction in logging middleware for sensitive headers.

### 7.4 Authorization Checks

| Endpoint | Protection | Implementation |
|----------|------------|----------------|
| `/v1/wallet/*` | `get_current_driver` | JWT required, returns 401 |
| `/v1/checkout/redeem` | `get_current_driver` | Driver owns wallet |
| `/v1/checkout/redemption/{id}` | `get_current_driver` | Validates `driver_user_id` matches |
| `/v1/merchants/me` | `require_merchant_admin` | Role check |
| `/v1/demo/square/*` | `verify_demo_admin_key` | Header + env var |
| PassKit endpoints | `_validate_passkit_auth` | Per-pass token validation |

### 7.5 Square OAuth CSRF

**Location**: `app/models/domain.py:SquareOAuthState`

```python
class SquareOAuthState:
    state: str       # Random CSRF token
    expires_at: datetime  # 15 minutes
    used: bool       # Marked after validation
```

**Status**: CSRF protection implemented correctly.

### 7.6 Demo-Gated Endpoints

| Endpoint | Gate |
|----------|------|
| `/v1/demo/charging/start` | `DEMO_MODE=true` OR `DEMO_QR_ENABLED=true` |
| `/v1/demo/charging/stop` | Same |
| `/v1/demo/square/*` | `DEMO_MODE=true` + `X-Demo-Admin-Key` header |
| `/qr/eggman-demo-checkout` | `DEMO_QR_ENABLED=true` + `DEMO_EGGMAN_QR_TOKEN` set |

---

## 8. Test Coverage

### Tests Present

| Area | Test File | Coverage |
|------|-----------|----------|
| Wallet Timeline | `test_wallet_timeline.py` | Duplicate prevention, ordering, limits |
| Apple Wallet Pass | `test_apple_wallet_pass.py` | Pass generation, signing gate |
| Charging Status | `test_apple_pass_charging_status.py` | Status in pass.json |
| Token Encryption | `test_token_encryption.py` | Encrypt/decrypt roundtrip |
| Square Orders | `test_square_orders.py` | Order search, totals |
| Square OAuth | `test_square_oauth_security.py` | CSRF validation |
| Checkout Square | `test_checkout_square.py` | Redemption flow |
| Merchant Fee | `test_merchant_fee.py` | 15% fee calculation |
| Demo QR | `test_demo_qr_redirect.py` | Redirect behavior |
| Demo Charging | `test_demo_charging_flow.py` | Start/stop |
| Merchant Rewards | `test_merchant_rewards.py` | Reward redemption |
| Merchant Billing | `test_merchant_billing.py` | Ledger queries |

### Missing Tests (Recommended)

1. **PassKit Web Service Endpoints**: Full integration test for registration/deregistration/list/fetch cycle
2. **APNs Push Integration**: Mock test for `send_updates_for_wallet`
3. **Google Wallet Create/Refresh**: Service-level tests
4. **Double Redemption Prevention**: Explicit 409 test for duplicate `square_order_id`
5. **Token Encryption Key Rotation**: Test behavior when key changes
6. **Wallet Timeline Edge Cases**: Empty merchant name, null timestamps

---

## 9. Landmines & Next Actions

### Top 10 Demo Landmines

1. **TOKEN_ENCRYPTION_KEY not set** → Square token decryption fails → "Merchant not connected" error
   - *Symptom*: Orders don't load in checkout
   - *Fix*: Ensure key is set and matches what was used to encrypt

2. **DEMO_EGGMAN_QR_TOKEN mismatch** → 404 on QR scan
   - *Symptom*: Demo QR code leads to "Invalid QR token"
   - *Fix*: Verify token in `.env` matches database `qr_token`

3. **Square sandbox token expired** → API calls fail
   - *Symptom*: "Square API error: 401"
   - *Fix*: Re-run OAuth flow for demo merchant

4. **Apple Wallet signing disabled** → 501 on pass creation
   - *Symptom*: "Add to Apple Wallet" shows error
   - *Fix*: Set `APPLE_WALLET_SIGNING_ENABLED=true` + provide certs

5. **Database migrations not run** → Missing columns
   - *Symptom*: 500 errors with "column does not exist"
   - *Fix*: Run `alembic upgrade head`

6. **CORS origin missing** → Frontend can't call API
   - *Symptom*: Browser console shows CORS errors
   - *Fix*: Add frontend URL to `ALLOWED_ORIGINS`

7. **Stale wallet_pass_token** → PassKit can't find pass
   - *Symptom*: Apple Wallet shows "Pass could not be updated"
   - *Fix*: Delete and re-add pass

8. **Demo charging not accruing** → Nova balance stays at 0
   - *Symptom*: Charging detected but no Nova
   - *Fix*: Ensure `nova_accrual_service` is running (check startup logs)

9. **Wrong SQUARE_ENV** → Sandbox vs production mismatch
   - *Symptom*: Orders from wrong environment
   - *Fix*: Verify `SQUARE_ENV=sandbox` for demo

10. **MerchantRedemption duplicate** → 409 on second redeem
    - *Symptom*: "Order already redeemed" error
    - *Fix*: Expected behavior; use different order

### Top 10 Questions for Founder

1. **Smartcar dependency**: Is Smartcar EV connection required for Apple Wallet eligibility in production, or should we allow any driver?

2. **Nova issuance rate**: What's the expected Nova/kWh rate for demo charging accrual? Currently seems hardcoded.

3. **Merchant fee collection**: How will 15% fees be collected? Stripe billing? Manual invoicing?

4. **Pass update frequency**: Should we push pass updates on every transaction, or batch them?

5. **Google Wallet priority**: Is Google Wallet a P0 for demo, or can it wait?

6. **Multi-merchant support**: Can a driver redeem at multiple merchants in same checkout session?

7. **Order age limit**: Currently 10 minutes for Square orders. Should this be configurable?

8. **Charging timeout**: Should `charging_detected` auto-expire after N hours if not stopped?

9. **Redemption cancellation**: Can a redemption be reversed? Need undo flow?

10. **Offline support**: Should checkout work offline with QR token caching?

### Recommended Next 5 Commits (in order)

1. **Add PassKit integration test**
   - Create `test_passkit_web_service.py`
   - Test full registration → update → fetch cycle
   - Mock APNs push

2. **Add duplicate redemption test**
   - Explicit test for 409 on same `square_order_id`
   - Document the unique constraint behavior

3. **Add token encryption rotation**
   - Support `TOKEN_ENCRYPTION_KEY_OLD` for migration
   - Try new key first, fall back to old

4. **Add logging redaction middleware**
   - Redact `Authorization`, `X-Demo-Admin-Key` headers
   - Mask `access_token` in response bodies

5. **Add health check for Square connectivity**
   - `GET /v1/health/square` verifies demo merchant token decrypts and API responds
   - Include in demo script

---

## Appendix: Quick Reference

### Demo Flow Checklist

```bash
# 1. Start backend
cd nerava-backend-v9
source .venv/bin/activate
uvicorn app.main_simple:app --reload --port 8001

# 2. Verify env vars
echo $DEMO_MODE                    # should be "true"
echo $DEMO_QR_ENABLED              # should be "true"
echo $DEMO_EGGMAN_QR_TOKEN         # should match merchant.qr_token
echo $TOKEN_ENCRYPTION_KEY         # must be set

# 3. Test QR redirect
curl -I http://localhost:8001/qr/eggman-demo-checkout
# Should return 302 redirect to /app/checkout.html?token=...

# 4. Test Square token verification (requires X-Demo-Admin-Key)
curl -H "X-Demo-Admin-Key: $DEMO_ADMIN_KEY" \
  "http://localhost:8001/v1/demo/square/verify?merchant_id=<id>"

# 5. Test checkout lookup
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8001/v1/checkout/qr/<qr_token>"
```

### Key File Locations

| Component | File |
|-----------|------|
| Checkout redeem | `app/routers/checkout.py:218` |
| PassKit endpoints | `app/routers/wallet_pass.py:694-1017` |
| Token encryption | `app/services/token_encryption.py` |
| Nova service | `app/services/nova_service.py` |
| Square orders | `app/services/square_orders.py` |
| Wallet timeline | `app/services/wallet_timeline.py` |
| Merchant fee | `app/services/merchant_fee.py` |
| Demo charging | `app/routers/demo_charging.py` |
| Demo QR | `app/routers/demo_qr.py` |

---

*End of Recon Pack*
