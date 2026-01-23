# Admin Endpoints Inventory & Operator Playbook

**Generated:** 2025-01-27  
**Purpose:** Complete enumeration of `/v1/admin/*` endpoints for operations troubleshooting

---

## 1. Complete Endpoint Inventory

### `/v1/admin/health`
- **Method:** GET
- **Purpose:** Get system health status for admin console (database, Redis checks)
- **Inputs:** None (requires admin auth)
- **Real-world question:** "Is the system healthy?"
- **Returns:** `{ready: bool, checks: {database: {...}, redis: {...}}}`

### `/v1/admin/overview`
- **Method:** GET
- **Purpose:** Get high-level system statistics
- **Inputs:** None (requires admin auth)
- **Real-world question:** "What's the overall system state?"
- **Returns:** `{total_drivers, total_merchants, total_driver_nova, total_merchant_nova, total_nova_outstanding, total_stripe_usd}`

### `/v1/admin/merchants`
- **Method:** GET
- **Purpose:** List merchants with optional filters
- **Inputs:** 
  - `zone_slug` (optional): Filter by zone
  - `status_filter` (optional): Filter by status
- **Real-world question:** "What merchants exist and what's their status?"
- **Returns:** `{merchants: [{id, name, zone_slug, status, nova_balance, last_active_at, created_at}]}`

### `/v1/admin/merchants` (duplicate - search version)
- **Method:** GET
- **Purpose:** Search merchants by name or ID
- **Inputs:** `query` (optional): Search by merchant name or ID
- **Real-world question:** "Find a specific merchant by name or ID"
- **Returns:** `{merchants: [{id, name, status, zone_slug, nova_balance, created_at}]}`

### `/v1/admin/merchants/{merchant_id}/status`
- **Method:** GET
- **Purpose:** Get detailed merchant status including Square connection and errors
- **Inputs:** `merchant_id` (path parameter)
- **Real-world question:** "Is this merchant connected to Square and are there any errors?"
- **Returns:** `{merchant_id, name, status, square_connected, square_last_error, nova_balance}`

### `/v1/admin/users`
- **Method:** GET
- **Purpose:** Search users by name, email, or public_id
- **Inputs:** `query` (optional): Search term
- **Real-world question:** "Find a user by email or ID"
- **Returns:** `[{id, public_id, email, role_flags, is_active, created_at}]`

### `/v1/admin/users/{user_id}/wallet`
- **Method:** GET
- **Purpose:** Get user wallet balance and transaction history
- **Inputs:** `user_id` (path parameter)
- **Real-world question:** "What's this user's wallet balance and recent transactions?"
- **Returns:** `{user_id, balance_cents, nova_balance, transactions: [{id, cents, reason, meta, created_at}]}`

### `/v1/admin/users/{user_id}/wallet/adjust`
- **Method:** POST
- **Purpose:** Manually adjust user wallet balance
- **Inputs:** 
  - `user_id` (path parameter)
  - Body: `{amount_cents: int, reason: str}`
- **Real-world question:** "Manually credit/debit a user's wallet"
- **Returns:** `{success, user_id, amount_cents, before_balance_cents, after_balance_cents}`

### `/v1/admin/nova/grant`
- **Method:** POST
- **Purpose:** Manually grant Nova to driver or merchant
- **Inputs:** Body: `{target: "driver"|"merchant", driver_user_id?: int, merchant_id?: str, amount: int, reason: str, idempotency_key?: str}`
- **Real-world question:** "Manually grant Nova to a driver or merchant"
- **Returns:** `{success, transaction_id, target, driver_user_id|merchant_id, amount}`

### `/v1/admin/payments/{payment_id}/reconcile`
- **Method:** POST
- **Purpose:** Reconcile a Stripe payment with status 'unknown'
- **Inputs:** `payment_id` (path parameter)
- **Real-world question:** "Check and update payment status from Stripe"
- **Returns:** `{payment_id, status, stripe_transfer_id, stripe_status, error_code, error_message, reconciled_at, no_transfer_confirmed}`

### `/v1/admin/locations/{location_id}/google-place/candidates`
- **Method:** GET
- **Purpose:** Get Google Places candidates for a merchant location
- **Inputs:** 
  - `location_id` (path parameter - merchant ID)
  - `query` (optional): Search query
- **Real-world question:** "Find Google Places matches for this merchant"
- **Returns:** `{candidates: [{place_id, name, formatted_address, geometry, rating, types}]}`

### `/v1/admin/locations/{location_id}/google-place/resolve`
- **Method:** POST
- **Purpose:** Resolve Google Place ID for a merchant location
- **Inputs:** 
  - `location_id` (path parameter - merchant ID)
  - Body: `{place_id: str}`
- **Real-world question:** "Link this merchant to a Google Place"
- **Returns:** `{success, merchant_id, google_place_id, place_details}`

### `/v1/admin/settle`
- **Method:** POST
- **Purpose:** Settle unpaid follower shares by crediting wallets
- **Inputs:** `limit` (query parameter, default 500)
- **Real-world question:** "Process pending follower share payouts"
- **Returns:** `{settled: int}`

---

## 2. Operator Playbook: "Merchant Reports Nova Redemption Failed for Order X"

### Scenario
A merchant contacts support: "Order X failed to process Nova redemption. Customer says they tried to redeem but it didn't work."

### Step-by-Step Diagnosis

#### Step 1: Identify Merchant
**Question:** "Which merchant reported this issue?"

**Endpoint:** `GET /v1/admin/merchants?query={merchant_name}`
- **Input:** Merchant name from support ticket
- **Returns:** `{merchants: [{id, name, status, nova_balance, ...}]}`
- **Action:** Note `merchant_id` from results

**Alternative:** If merchant name unknown, use:
- `GET /v1/admin/merchants` (list all) or
- `GET /v1/admin/merchants/{merchant_id}/status` (if merchant_id known)

---

#### Step 2: Get Merchant Status
**Question:** "Is the merchant properly configured and connected?"

**Endpoint:** `GET /v1/admin/merchants/{merchant_id}/status`
- **Input:** `merchant_id` from Step 1
- **Returns:** `{merchant_id, name, status, square_connected: bool, square_last_error: str|null, nova_balance}`
- **Check:**
  - `square_connected`: Should be `true` if using Square POS
  - `square_last_error`: Check for recent errors
  - `status`: Should be `"active"`

**Gap Identified:** No endpoint to list recent redemptions for a merchant.

---

#### Step 3: Find Redemption by Square Order ID
**Question:** "Did the redemption attempt succeed or fail?"

**⚠️ MISSING ENDPOINT:** No direct endpoint to look up redemption by `square_order_id`.

**Workaround Required:**
1. Query database directly: `SELECT * FROM merchant_redemptions WHERE square_order_id = 'X'`
2. Or search by merchant and date range (if endpoint existed)

**Data Needed:**
- `redemption_id`
- `driver_user_id`
- `merchant_id`
- `square_order_id`
- `order_total_cents`
- `discount_cents`
- `nova_spent_cents`
- `created_at`
- `qr_token`
- `idempotency_key`

**Gap Identified:** No endpoint `GET /v1/admin/merchants/{merchant_id}/redemptions` or `GET /v1/admin/redemptions?square_order_id=X`

---

#### Step 4: Check Driver Wallet (if redemption found)
**Question:** "Did the driver have sufficient Nova balance?"

**Endpoint:** `GET /v1/admin/users/{user_id}/wallet`
- **Input:** `user_id` = `driver_user_id` from Step 3
- **Returns:** `{user_id, balance_cents, nova_balance, transactions: [...]}`
- **Check:**
  - Current `nova_balance`: Should be sufficient for redemption
  - Transaction history: Look for redemption transaction at time of order

**Gap Identified:** No endpoint to get redemption details by `redemption_id` directly.

---

#### Step 5: Verify Order in Square (if Square order)
**Question:** "Does the Square order exist and match our records?"

**⚠️ MISSING ENDPOINT:** No admin endpoint to query Square API for order details.

**Workaround Required:**
- Use Square API directly with merchant's access token
- Or check merchant's Square dashboard

**Gap Identified:** No endpoint `GET /v1/admin/merchants/{merchant_id}/square/orders/{order_id}`

---

#### Step 6: Check System Health (if issue persists)
**Question:** "Was there a system issue at the time?"

**Endpoint:** `GET /v1/admin/health`
- **Input:** None
- **Returns:** `{ready: bool, checks: {database, redis}}`
- **Check:** System was healthy at time of redemption

**Note:** This only shows current health, not historical.

---

### Summary of Data Flow

```
1. GET /v1/admin/merchants?query={name}
   → merchant_id

2. GET /v1/admin/merchants/{merchant_id}/status
   → square_connected, square_last_error, status

3. [MISSING] GET /v1/admin/redemptions?square_order_id=X
   → redemption_id, driver_user_id, discount_cents, created_at

4. GET /v1/admin/users/{driver_user_id}/wallet
   → nova_balance, transactions

5. [MISSING] GET /v1/admin/merchants/{merchant_id}/square/orders/{order_id}
   → Square order details

6. GET /v1/admin/health
   → System health (current only)
```

---

## 3. Missing Endpoints (Blocking Resolution)

### 1. **GET /v1/admin/redemptions** (or `/v1/admin/merchants/{merchant_id}/redemptions`)
**Purpose:** List redemptions with filters  
**Inputs:**
- `merchant_id` (optional): Filter by merchant
- `square_order_id` (optional): Find specific order
- `driver_user_id` (optional): Filter by driver
- `start_date` / `end_date` (optional): Date range
- `limit` (optional): Pagination

**Returns:** `{redemptions: [{id, merchant_id, driver_user_id, square_order_id, order_total_cents, discount_cents, nova_spent_cents, created_at, qr_token}]}`

**Why Critical:** Cannot diagnose redemption failures without ability to look up redemption records.

---

### 2. **GET /v1/admin/redemptions/{redemption_id}**
**Purpose:** Get detailed redemption information  
**Inputs:** `redemption_id` (path parameter)

**Returns:** Full redemption details including:
- All fields from MerchantRedemption
- Related NovaTransaction records
- Driver wallet balance at time of redemption
- Merchant balance impact

**Why Critical:** Need to see full redemption context for troubleshooting.

---

### 3. **GET /v1/admin/merchants/{merchant_id}/square/orders/{order_id}**
**Purpose:** Query Square API for order details  
**Inputs:** 
- `merchant_id` (path parameter)
- `order_id` (path parameter - Square order ID)

**Returns:** Square order details:
- Order total
- Order status
- Order timestamp
- Line items
- Payment information

**Why Critical:** Need to verify order exists in Square and matches our redemption record.

---

## 4. Additional Data Gaps

### Missing from Current Endpoints:
1. **Redemption lookup by square_order_id** - Cannot find redemption without database query
2. **Redemption lookup by redemption_id** - Cannot get redemption details
3. **List redemptions for merchant** - Cannot see redemption history
4. **List redemptions for driver** - Cannot see driver's redemption history
5. **Square order verification** - Cannot verify order exists in Square
6. **Historical system health** - Cannot check if system was down at time of redemption
7. **Redemption error logs** - No endpoint to see redemption attempt failures

### Workarounds Available:
- Direct database queries (requires database access)
- Square API direct calls (requires merchant access token)
- Application logs (requires log access)

---

## 5. Recommended Minimal API Additions

To unblock redemption diagnosis, add these 3 endpoints:

1. **GET /v1/admin/redemptions**
   - Query redemptions by merchant_id, square_order_id, driver_user_id, date range
   - Returns list of redemptions with core fields

2. **GET /v1/admin/redemptions/{redemption_id}**
   - Get full redemption details including related transactions
   - Returns complete redemption context

3. **GET /v1/admin/merchants/{merchant_id}/square/orders/{order_id}**
   - Query Square API for order details
   - Returns Square order information for verification

These 3 endpoints would enable complete diagnosis of redemption failures without requiring database or Square API access.

