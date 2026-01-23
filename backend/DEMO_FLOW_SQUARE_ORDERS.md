# Square Order Lookup Demo Flow

This document describes the complete demo flow for Square Order Lookup + Select Your Order + Apply 300 Nova + Merchant Fee Ledger.

## Setup: Stable Encryption Key

**CRITICAL:** Before running the demo, you must set a stable `TOKEN_ENCRYPTION_KEY` in your `.env` file. This key encrypts Square access tokens at rest. If the key changes, existing tokens cannot be decrypted.

1. **Set the encryption key in `.env`:**
   ```bash
   TOKEN_ENCRYPTION_KEY=TaHJDO442DD22r5y-jQYw_ig0MUouqbA0LjCS7e9C2M=
   ```
   - This key must be exactly 44 characters (base64-encoded 32-byte Fernet key)
   - **Do not change this key** after setting it, or you'll need to re-onboard merchants

2. **Set the demo admin key:**
   ```bash
   DEMO_ADMIN_KEY=demo-admin-key
   ```

3. **Restart the backend** after setting these variables.

4. **Re-onboard Square sandbox merchant** (if tokens were encrypted with a different key):
   - Visit: `GET /v1/merchants/square/sandbox/connect`
   - Complete the Square OAuth flow
   - This will store a fresh token encrypted with the current key

5. **Verify token works:**
   - Call: `GET /v1/demo/square/verify?merchant_id=<merchant_id>`
   - Add header: `X-Demo-Admin-Key: <DEMO_ADMIN_KEY>`
   - Should return: `{"ok": true, "location_id": "...", "merchant_name": "..."}`
   - If verification fails, redo the Square OAuth flow

## Prerequisites

1. **Environment Variables:**
   ```bash
   SQUARE_ENV=sandbox
   DEMO_MODE=true
   DEMO_ADMIN_KEY=<your-secure-key>
   PUBLIC_BASE_URL=<your-tunnel-url>
   TOKEN_ENCRYPTION_KEY=TaHJDO442DD22r5y-jQYw_ig0MUouqbA0LjCS7e9C2M=
   ```

2. **Merchant Setup:**
   - Merchant must be connected to Square (has `square_access_token`, `square_location_id`)
   - Merchant must have a QR token
   - Merchant should have `recommended_perk_cents` or `custom_perk_cents` set (defaults to 300)

## Demo Flow Steps

### Step 1: Start Backend + Tunnel

```bash
# Start backend
SQUARE_ENV=sandbox \
DEMO_MODE=true \
DEMO_ADMIN_KEY=your-secure-key \
PUBLIC_BASE_URL=https://your-tunnel-url.trycloudflare.com \
uvicorn app.main_simple:app --reload --port 8001

# In another terminal, start tunnel (if needed)
cloudflared tunnel --url http://localhost:8001
```

### Step 2: Create Square Sandbox Order (via Swagger)

1. Open Swagger UI: `http://127.0.0.1:8001/docs`
2. Authorize with your bearer token (top right)
3. Find `POST /v1/demo/square/orders/create`
4. Click "Try it out"
5. Add header: `X-Demo-Admin-Key: <DEMO_ADMIN_KEY>`
6. Body:
   ```json
   {
     "merchant_id": "86465be6-96b6-47c5-b43d-59003b12cb81",
     "amount_cents": 850,
     "name": "Coffee"
   }
   ```
7. Execute and copy the `order_id`

### Step 3: Pay the Order (via Swagger)

1. Find `POST /v1/demo/square/payments/create`
2. Click "Try it out"
3. Add header: `X-Demo-Admin-Key: <DEMO_ADMIN_KEY>`
4. Body:
   ```json
   {
     "merchant_id": "86465be6-96b6-47c5-b43d-59003b12cb81",
     "order_id": "<ORDER_ID_FROM_STEP_2>",
     "amount_cents": 850
   }
   ```
5. Execute - confirm status is `COMPLETED`

### Step 4: Driver Redemption Flow

1. Open checkout page:
   ```
   http://127.0.0.1:8001/app/checkout.html?token=<merchant_qr_token>
   ```

2. The page will:
   - Load merchant context
   - Call `GET /v1/checkout/orders?token=...&minutes=10`
   - Display "Recent purchases (last 10 minutes)" list
   - Show the order from Step 2

3. Select the order (radio button)

4. Click "Apply 300 Nova"

5. The system will:
   - Fetch order total from Square
   - Validate no duplicate redemption
   - Debit Nova from driver wallet
   - Create `MerchantRedemption` with `square_order_id`
   - Record merchant fee (15% of 300 = 45 cents)
   - Update wallet activity timestamp

6. Success screen shows:
   - Order total
   - Discount applied
   - Remaining Nova
   - Merchant fee (if applicable)

### Step 5: Verify Merchant Dashboard

1. Open merchant dashboard:
   ```
   http://127.0.0.1:8001/app/merchant/dashboard.html?merchant_id=<merchant_id>
   ```

2. Check:
   - Redemption count increased
   - Billing section shows:
     - Nova Redeemed: $3.00 (300 cents)
     - Fee (15%): $0.45 (45 cents)
     - Status: accruing

## Swagger Instructions (No curl)

### Create Order

1. Go to `http://127.0.0.1:8001/docs`
2. Find `POST /v1/demo/square/orders/create`
3. Click "Try it out"
4. Add header: `X-Demo-Admin-Key: <DEMO_ADMIN_KEY>`
5. Body:
   ```json
   {
     "merchant_id": "<merchant_id>",
     "amount_cents": 850,
     "name": "Coffee"
   }
   ```
6. Execute → Copy `order_id`

### Pay Order

1. Find `POST /v1/demo/square/payments/create`
2. Click "Try it out"
3. Add header: `X-Demo-Admin-Key: <DEMO_ADMIN_KEY>`
4. Body:
   ```json
   {
     "merchant_id": "<merchant_id>",
     "order_id": "<order_id>",
     "amount_cents": 850
   }
   ```
5. Execute → Confirm `status: COMPLETED`

## Key Features

### Duplicate Prevention

- Unique constraint on `(merchant_id, square_order_id)`
- Returns 409 `ORDER_ALREADY_REDEEMED` if order already redeemed

### Merchant Fee Calculation

- Fee = 15% of Nova redeemed (not order total)
- Example: 300 cents Nova → 45 cents fee
- Tracked per merchant per month in `merchant_fee_ledger`

### Order Selection

- UI shows recent orders from last 10 minutes
- Driver selects order via radio button
- Falls back to manual entry if no orders or merchant not connected
- localStorage caches last demo order_id for resilience

### Error Handling

- `SQUARE_NOT_CONNECTED` - Merchant not connected to Square
- `ORDER_ALREADY_REDEEMED` - Duplicate redemption attempt
- `INSUFFICIENT_NOVA` - Driver doesn't have enough Nova
- `SQUARE_ORDER_TOTAL_UNAVAILABLE` - Could not fetch order total

## Investor Narration Script

> "Here's the demo: Nerava turns EV charging into real-world rewards, without changing the merchant's POS flow.
>
> First, I open the driver wallet — it looks like Apple Cash: a single Nova balance and a transaction timeline. When charging is detected, the wallet shows Nova accruing.
>
> Now I scan the merchant QR. Nerava pulls the last few Square purchases from the merchant's POS — no manual entry. I select my real purchase from the last 10 minutes and tap 'Apply 300 Nova'. That creates an on-ledger redemption tied to the Square order ID, updates the driver wallet instantly, and updates the merchant dashboard instantly.
>
> On the merchant side, you can see redemptions, drivers, and also billing: merchants are charged later, and only pay 15% of the Nova redeemed — so if I redeem $3 in Nova, the merchant fee is $0.45 for that period. This is the core loop: drivers earn Nova for grid-friendly charging, spend it at merchants, and merchants get measurable EV foot traffic with transparent fees."

## Testing

Run tests:
```bash
pytest tests/unit/test_square_orders.py
pytest tests/unit/test_merchant_fee.py
pytest tests/integration/test_checkout_square.py
```

## Troubleshooting

1. **Token decryption fails / "SQUARE_NOT_CONNECTED" errors:**
   - **Root cause:** Token was encrypted with a different `TOKEN_ENCRYPTION_KEY` than the one currently set
   - **Solution:** 
     - Ensure `TOKEN_ENCRYPTION_KEY` is set in `.env` and matches the key used when the token was stored
     - If you don't have the original key, you must re-onboard the merchant:
       1. Call `GET /v1/merchants/square/sandbox/connect`
       2. Complete Square OAuth flow
       3. Verify with `GET /v1/demo/square/verify?merchant_id=<merchant_id>`
   - **Prevention:** Never change `TOKEN_ENCRYPTION_KEY` after setting it

2. **Orders not showing:**
   - Check merchant is connected to Square (`square_access_token` set)
   - Verify `SQUARE_ENV=sandbox`
   - Check order was created within last 10 minutes
   - Verify token works: `GET /v1/demo/square/verify?merchant_id=<merchant_id>`

3. **Redemption fails:**
   - Verify driver has sufficient Nova balance
   - Check order hasn't been redeemed already
   - Ensure merchant location matches order location
   - Verify Square token is working (use verify endpoint)

4. **Fee not recording:**
   - Check `merchant_fee_ledger` table exists (migration 027)
   - Verify `record_merchant_fee` is called after redemption
   - Check logs for errors

5. **Verify endpoint returns error:**
   - If `ok: false` with `SQUARE_NOT_CONNECTED` or `VERIFICATION_ERROR`:
     - Token may be encrypted with wrong key → redo OAuth
     - Token may be expired → redo OAuth
     - Square API may be down → check Square status

