# Nerava EV Arrival — System Design & UX Spec

**Date:** 2026-02-01
**Author:** Principal Product Architect + Staff Engineer
**Status:** Implementation-ready. 7-day sprint plan included.

---

## 1. What Nerava Is Now

Nerava is an **EV Arrival coordination network**. When a driver plugs in at a charger near a participating merchant, Nerava verifies that arrival and notifies the merchant in real time — including the driver's order number, vehicle description, and arrival type (Curbside or Dine-In). Drivers order through the merchant's existing channels (Toast, Square, web, phone). Nerava never touches payments or fulfillment. We are the trust layer between "driver is charging nearby" and "merchant acts on that fact." We monetize by taking a percentage of order value on confirmed arrivals, starting at 5% and converging toward 8%+. Exclusives and perks can exist on top of this model but are not required for it to function — the core value is **verified presence + merchant notification at the moment it matters**.

---

## 2. System Architecture

### Component Map

```
┌─────────────────────────────────────────────────────────────┐
│                      DRIVER APP (iOS)                       │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Mode     │  │ Merchant │  │ EV Arrival   │  │ Order # │ │
│  │ Selector │→ │ List     │→ │ Confirmation │→ │ Input   │ │
│  │ (2 tabs) │  │          │  │              │  │         │ │
│  └──────────┘  └──────────┘  └──────────────┘  └─────────┘ │
│       ↕ Native Bridge (location, geofence, auth)            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                        │
│                                                             │
│  /v1/arrival/create          → Creates ArrivalSession       │
│  /v1/arrival/{id}/order      → Binds order number           │
│  /v1/arrival/{id}/confirm    → Geofence triggers notify     │
│  /v1/arrival/{id}/complete   → Merchant marks delivered     │
│  /v1/arrival/{id}/feedback   → Driver rates experience      │
│                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ ArrivalService │  │ POS Adapter    │  │ Notification  │  │
│  │ (core logic)   │  │ (Toast/Square/ │  │ Service       │  │
│  │                │  │  Manual)       │  │ (SMS/email)   │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ BillingService │  │ GeofenceCheck  │  │ PostHog      │  │
│  │ (% of order)   │  │ (radius gate)  │  │ Analytics    │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
        ┌──────────┐  ┌─────────┐  ┌────────────┐
        │ Twilio   │  │ Toast   │  │ Merchant   │
        │ SMS      │  │ API     │  │ Dashboard  │
        │          │  │ (read)  │  │ (web)      │
        └──────────┘  └─────────┘  └────────────┘
```

### Data Flow: Happy Path

```
1. Driver opens app → selects EV Curbside or EV Dine-In
2. App calls /v1/charge-context/nearby with lat/lng → returns nearby merchants for charging location
3. Driver taps merchant → taps "Add EV Arrival"
4. Backend creates ArrivalSession (status: PENDING_ORDER)
5. App shows "Now order" deep link + order number input
6. Driver orders through merchant's channel, returns to Nerava, enters order #
7. Backend calls POS adapter to look up order (if integrated) → binds order_total_cents
8. Driver arrives at charger geofence (native bridge detects entry)
9. Backend receives geofence confirmation → transitions to ARRIVED
10. NotificationService sends SMS/email to merchant:
    "EV Arrival: Order #1234 | EV Curbside | Blue Tesla Model 3 | On-site now"
11. Merchant delivers order → taps "Confirm" in dashboard or replies to SMS
12. Backend transitions to COMPLETED → BillingService records billable amount
13. Driver gets completion screen → optional feedback → session ends
```

### Event Bus (PostHog)

All events use prefix `ev_arrival.` and include `session_id`, `merchant_id`, `driver_id`:

| Event | Trigger |
|-------|---------|
| `ev_arrival.created` | Driver adds EV Arrival |
| `ev_arrival.order_bound` | Order number entered |
| `ev_arrival.order_resolved` | POS adapter confirmed order total |
| `ev_arrival.geofence_entered` | Native bridge detects charger proximity |
| `ev_arrival.merchant_notified` | SMS/email sent to merchant |
| `ev_arrival.merchant_confirmed` | Merchant marks delivered |
| `ev_arrival.completed` | Session fully closed |
| `ev_arrival.feedback_submitted` | Driver leaves thumbs + reason |
| `ev_arrival.expired` | Session timed out without completion |
| `ev_arrival.canceled` | Driver or merchant canceled |

---

## 3. Data Model Updates

### New Table: `arrival_sessions`

```sql
CREATE TABLE arrival_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id       INTEGER NOT NULL REFERENCES users(id),
    merchant_id     VARCHAR NOT NULL REFERENCES merchants(id),
    charger_id      VARCHAR REFERENCES chargers(id),

    -- Mode
    arrival_type    VARCHAR(20) NOT NULL,  -- 'ev_curbside' or 'ev_dine_in'

    -- Order binding
    order_number    VARCHAR(100),          -- Manual entry or POS-resolved
    order_source    VARCHAR(20),           -- 'manual', 'toast', 'square'
    order_total_cents INTEGER,             -- From POS or driver estimate
    order_status    VARCHAR(20),           -- 'unknown','placed','ready','completed'

    -- Vehicle (cached per user, copied here for immutability)
    vehicle_color   VARCHAR(30),
    vehicle_model   VARCHAR(60),

    -- Session lifecycle
    status          VARCHAR(30) NOT NULL DEFAULT 'pending_order',
    -- pending_order → awaiting_arrival → arrived → merchant_notified → completed
    -- also: expired, canceled, completed_unbillable
    -- Copy vocabulary: Armed → On-site confirmed → Merchant notified → Completed

    -- Timestamps
    created_at              TIMESTAMP NOT NULL DEFAULT now(),
    order_bound_at          TIMESTAMP,
    geofence_entered_at     TIMESTAMP,
    merchant_notified_at    TIMESTAMP,
    merchant_confirmed_at   TIMESTAMP,
    completed_at            TIMESTAMP,
    expires_at              TIMESTAMP NOT NULL,  -- 2 hours from creation

    -- Geofence
    arrival_lat     FLOAT,
    arrival_lng     FLOAT,
    arrival_accuracy_m FLOAT,

    -- Billing
    platform_fee_bps    INTEGER NOT NULL DEFAULT 500,  -- 5% = 500 bps
    billable_amount_cents INTEGER,  -- order_total_cents * fee_bps / 10000
    billing_status  VARCHAR(20) DEFAULT 'pending',  -- pending, invoiced, paid

    -- Idempotency
    idempotency_key VARCHAR(100) UNIQUE,

    -- SMS reply code for session mapping
    merchant_reply_code VARCHAR(6),       -- 4-digit code sent in SMS so DONE replies map to this session

    -- Manual billing fields
    driver_estimate_cents INTEGER,         -- Driver's pre-order estimate
    merchant_reported_total_cents INTEGER, -- Merchant-reported total (via SMS or dashboard)
    total_source VARCHAR(20),             -- 'pos', 'merchant_reported', 'driver_estimate'

    -- Feedback
    feedback_rating  VARCHAR(10),         -- 'up' or 'down'
    feedback_reason  VARCHAR(50),         -- chip selection
    feedback_comment VARCHAR(200),        -- optional text

    -- Indexes
    -- CRITICAL: Partial unique index on driver_id ONLY (not driver_id + status).
    -- This prevents a driver from having more than one active session at a time,
    -- regardless of which active status it's in.
    CONSTRAINT idx_arrival_one_active_per_driver UNIQUE (driver_id)
        WHERE status IN ('pending_order','awaiting_arrival','arrived','merchant_notified')
);

CREATE INDEX idx_arrival_merchant ON arrival_sessions(merchant_id, status);
CREATE INDEX idx_arrival_billing ON arrival_sessions(billing_status) WHERE billing_status = 'pending';
CREATE INDEX idx_arrival_created ON arrival_sessions(created_at);
```

### New Table: `merchant_notification_config`

```sql
CREATE TABLE merchant_notification_config (
    id              SERIAL PRIMARY KEY,
    merchant_id     VARCHAR NOT NULL UNIQUE REFERENCES merchants(id),
    notify_sms      BOOLEAN DEFAULT true,
    notify_email    BOOLEAN DEFAULT false,
    sms_phone       VARCHAR(20),           -- E.164 format
    email_address   VARCHAR(255),
    pos_integration VARCHAR(20),           -- 'none','toast','square'
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);
```

### New Table: `merchant_pos_credentials` (SEPARATED from notification config)

POS credentials are isolated in their own table so notification preferences
can be edited without touching secrets. Same Fernet encryption as Square.

```sql
CREATE TABLE merchant_pos_credentials (
    id              SERIAL PRIMARY KEY,
    merchant_id     VARCHAR NOT NULL UNIQUE REFERENCES merchants(id),
    pos_type        VARCHAR(20) NOT NULL,  -- 'toast','square'
    restaurant_guid VARCHAR(100),          -- Toast restaurant GUID
    access_token_encrypted  TEXT,          -- Fernet-encrypted OAuth access token
    refresh_token_encrypted TEXT,          -- Fernet-encrypted OAuth refresh token
    token_expires_at TIMESTAMP,
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now()
);
```

### New Table: `billing_events`

```sql
CREATE TABLE billing_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arrival_session_id  UUID NOT NULL REFERENCES arrival_sessions(id),
    merchant_id         VARCHAR NOT NULL REFERENCES merchants(id),
    order_total_cents   INTEGER NOT NULL,
    fee_bps             INTEGER NOT NULL,
    billable_cents      INTEGER NOT NULL,  -- order_total * fee_bps / 10000
    status              VARCHAR(20) DEFAULT 'pending',  -- pending, invoiced, paid, disputed
    invoice_id          VARCHAR(100),       -- Stripe invoice ID or internal ref
    created_at          TIMESTAMP DEFAULT now(),
    invoiced_at         TIMESTAMP,
    paid_at             TIMESTAMP
);

CREATE INDEX idx_billing_merchant ON billing_events(merchant_id, status);
CREATE INDEX idx_billing_pending ON billing_events(status) WHERE status = 'pending';
```

### Modified Table: `users` (add vehicle fields)

```sql
ALTER TABLE users ADD COLUMN vehicle_color VARCHAR(30);
ALTER TABLE users ADD COLUMN vehicle_model VARCHAR(60);
ALTER TABLE users ADD COLUMN vehicle_set_at TIMESTAMP;
```

### Modified Table: `merchants` (add ordering info)

```sql
ALTER TABLE merchants ADD COLUMN ordering_url VARCHAR(500);       -- Deep link or web URL
ALTER TABLE merchants ADD COLUMN ordering_app_scheme VARCHAR(100); -- e.g. "toastapp://"
ALTER TABLE merchants ADD COLUMN ordering_instructions TEXT;       -- "Order at counter"
```

---

## 4. API Contracts

### Arrival Endpoints (`/v1/arrival`)

#### `POST /v1/arrival/create`

Create a new EV Arrival session. Requires authenticated driver.

```json
// Request
{
  "merchant_id": "m_abc123",
  "charger_id": "ch_456",           // optional
  "arrival_type": "ev_curbside",    // or "ev_dine_in"
  "lat": 30.2672,                   // current location
  "lng": -97.7431,
  "accuracy_m": 25.0
}

// Response 201
{
  "session_id": "uuid-here",
  "status": "pending_order",
  "merchant_name": "Asadas Grill",
  "arrival_type": "ev_curbside",
  "ordering_url": "https://order.toasttab.com/asadas-grill",
  "ordering_instructions": null,
  "expires_at": "2026-02-01T14:00:00Z",
  "vehicle": {
    "color": "Blue",
    "model": "Tesla Model 3"
  }
}
```

**Logic:**
- Validates driver has no other active arrival session (1 at a time)
- Copies vehicle info from `users` table
- Sets `expires_at` to 2 hours from now
- If no vehicle set, response includes `"vehicle_required": true`

#### `PUT /v1/arrival/{session_id}/order`

Bind an order number to the session.

```json
// Request
{
  "order_number": "1234",
  "estimated_total_cents": 2500  // optional, for manual mode
}

// Response 200
{
  "session_id": "uuid-here",
  "status": "awaiting_arrival",
  "order_number": "1234",
  "order_source": "toast",        // or "manual" if no POS match
  "order_total_cents": 2847,      // from POS, or driver estimate
  "order_status": "placed"        // from POS, or "unknown"
}
```

**Logic:**
- Calls POS adapter to resolve order (if merchant has integration)
- Falls back to manual if POS lookup fails
- Transitions status: `pending_order` → `awaiting_arrival`

#### `POST /v1/arrival/{session_id}/confirm-arrival`

Called by native bridge when driver enters charger geofence.
**ANTI-SPOOFING:** Requires `charger_id` + server-side distance verification.

```json
// Request
{
  "charger_id": "ch_456",    // REQUIRED — anti-spoofing
  "lat": 30.2672,
  "lng": -97.7431,
  "accuracy_m": 15.0
}

// Response 200
{
  "status": "merchant_notified",
  "merchant_notified": true,
  "notification_method": "sms"
}
```

**Logic:**
- Requires `charger_id` in request body (rejects if missing)
- Server looks up charger lat/lng from DB and computes haversine distance
- Rejects if driver is >250m from charger (returns TOO_FAR_FROM_CHARGER error)
- Transitions status: `awaiting_arrival` → `arrived` → `merchant_notified`
- Triggers NotificationService (sends SMS with reply code to merchant)
- Records `geofence_entered_at` and `merchant_notified_at`

#### `POST /v1/arrival/{session_id}/merchant-confirm`

Merchant confirms order was delivered. Can include merchant-reported total.

```json
// Request (from merchant dashboard or SMS reply)
{
  "confirmed": true,
  "merchant_reported_total_cents": 2847  // optional
}

// Response 200
{
  "status": "completed",       // or "completed_unbillable"
  "billable_amount_cents": 142 // or null
}
```

**Logic:**
- Transitions: `merchant_notified` → `completed` (or `completed_unbillable`)
- **Billing total precedence:** POS-verified > merchant_reported > driver_estimate
- If a total is available: creates `billing_events` row, status = `completed`
- If NO total (no POS, no merchant report, no driver estimate): status = `completed_unbillable`
- Stores `total_source` field: `'pos'`, `'merchant_reported'`, or `'driver_estimate'`
- Records `merchant_confirmed_at` and `completed_at`
- **Separate "analytics completion" from "billable completion":** PostHog fires
  `ev_arrival.completed` for all completions, but `ev_arrival.billed` only when
  a billing event is created.

#### `POST /v1/arrival/{session_id}/feedback`

Driver post-visit feedback.

```json
// Request
{
  "rating": "up",                  // "up" or "down"
  "reason": "fast_service",        // chip selection (down only)
  "comment": "Great experience"    // optional text (up only)
}

// Response 200
{
  "ok": true
}
```

#### `GET /v1/arrival/active`

Get driver's current active arrival session (if any).

```json
// Response 200
{
  "session": {
    "session_id": "uuid-here",
    "status": "awaiting_arrival",
    "merchant_name": "Asadas Grill",
    "arrival_type": "ev_curbside",
    "order_number": "1234",
    "expires_at": "2026-02-01T14:00:00Z",
    "vehicle": { "color": "Blue", "model": "Tesla Model 3" }
  }
}
// or { "session": null } if no active session
```

### Vehicle Endpoint

#### `PUT /v1/account/vehicle`

One-time vehicle setup (cached, editable).

```json
// Request
{
  "color": "Blue",
  "model": "Tesla Model 3"
}

// Response 200
{
  "color": "Blue",
  "model": "Tesla Model 3",
  "set_at": "2026-02-01T12:00:00Z"
}
```

### Merchant Notification Config

#### `PUT /v1/merchants/{merchant_id}/notification-config`

Merchant sets how they want to receive arrival notifications.

```json
// Request
{
  "sms_phone": "+15125551234",
  "email_address": "manager@asadas.com",
  "notify_sms": true,
  "notify_email": false
}
```

---

## 5. Toast Read-Only Integration Design

### Auth Method

**Assumption:** Toast uses OAuth 2.0 with restaurant-level authorization. The merchant grants Nerava read access during onboarding.

- **OAuth flow:** Merchant clicks "Connect Toast" in Nerava merchant dashboard → redirected to Toast authorization → Toast returns auth code → we exchange for access_token + refresh_token
- **Scopes requested:** `orders:read` only. No write scopes.
- **Token storage:** Encrypted in `merchant_pos_credentials.access_token_encrypted` using existing Fernet encryption (same pattern as Square). Credentials are in a separate table from notification config to isolate secrets from preferences.
- **Token refresh:** Background job refreshes tokens before expiry

### Abstraction Layer: POS Adapter

We build a `POSAdapter` interface so Toast, Square, and Manual all share the same contract:

```python
# backend/app/services/pos_adapter.py

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class POSOrder:
    order_number: str
    status: str          # 'placed', 'ready', 'completed', 'unknown'
    total_cents: int
    customer_name: Optional[str] = None
    items_summary: Optional[str] = None

class POSAdapter(ABC):
    @abstractmethod
    async def lookup_order(self, order_number: str) -> Optional[POSOrder]:
        """Find order by number. Returns None if not found."""
        pass

    @abstractmethod
    async def get_order_status(self, order_number: str) -> Optional[str]:
        """Get current status of an order."""
        pass

    @abstractmethod
    async def get_order_total(self, order_number: str) -> Optional[int]:
        """Get order total in cents."""
        pass

class ManualPOSAdapter(POSAdapter):
    """No POS integration — uses driver-reported data."""
    async def lookup_order(self, order_number: str) -> Optional[POSOrder]:
        return POSOrder(
            order_number=order_number,
            status='unknown',
            total_cents=0,  # Filled by driver estimate or merchant confirmation
        )

    async def get_order_status(self, order_number: str) -> Optional[str]:
        return 'unknown'

    async def get_order_total(self, order_number: str) -> Optional[int]:
        return None

class ToastPOSAdapter(POSAdapter):
    """Read-only Toast integration."""
    def __init__(self, restaurant_guid: str, access_token: str):
        self.restaurant_guid = restaurant_guid
        self.access_token = access_token
        self.base_url = "https://ws-api.toasttab.com"

    async def lookup_order(self, order_number: str) -> Optional[POSOrder]:
        # Toast API: GET /orders/v2/orders
        # Filter by externalReferenceId or check number
        # Assumption: Toast exposes order lookup by check number
        # If not available, fall back to recent orders scan
        ...

    async def get_order_status(self, order_number: str) -> Optional[str]:
        order = await self.lookup_order(order_number)
        if not order:
            return None
        return order.status

    async def get_order_total(self, order_number: str) -> Optional[int]:
        order = await self.lookup_order(order_number)
        if not order:
            return None
        return order.total_cents
```

### Toast API Endpoints We Need

| Toast Endpoint | Purpose | Our Usage |
|----------------|---------|-----------|
| `GET /orders/v2/orders?businessDate={date}` | List orders for a business date | Scan for matching order number |
| `GET /orders/v2/orders/{orderGuid}` | Get single order details | Read total, status, items |
| `GET /config/v2/restaurants/{restaurantGuid}` | Restaurant config | Validate connection during onboarding |

**Assumption:** Toast orders have a `checks[].displayNumber` or similar field that maps to the receipt number the customer sees. We match on this.

### Order Number → Order Total → Completed Status

```
1. Driver enters "1234" as order number
2. Backend calls ToastPOSAdapter.lookup_order("1234")
3. Adapter hits GET /orders/v2/orders?businessDate=2026-02-01
4. Scans response for check where displayNumber matches "1234"
5. If found:
   - Extract total from checks[0].totalAmount (convert to cents)
   - Extract status from voidDate (null = active), closedDate (null = open)
   - Map to our status: no closedDate → "placed", closedDate → "completed"
6. Store order_total_cents and order_status on arrival_session
7. On session completion, re-fetch to get final total (in case of modifications)
```

### Failure Modes + Fallback

| Failure | Behavior |
|---------|----------|
| Toast API timeout (>5s) | Fall back to ManualPOSAdapter. Log warning. Retry in background. |
| Order number not found in Toast | Keep session with `order_source: 'manual'`. Driver estimate used if provided. |
| Toast token expired | Attempt refresh. If refresh fails, fall back to manual. Email merchant to reconnect. |
| Toast API returns 429 | Exponential backoff. Fall back to manual for current request. |
| Order total is $0 or negative | Flag for review. Do not bill. |
| Toast integration not configured | Use ManualPOSAdapter automatically. |

**Key principle:** Every failure mode degrades to manual. The system always works — POS integration just makes billing more accurate.

---

## 6. Driver UX Flows

### Screen 1: Home — Mode Selector + Merchant List

```
┌─────────────────────────────┐
│  ┌───────────┬────────────┐ │
│  │EV Curbside│ EV Dine-In │ │  ← Segmented control, top of screen
│  └───────────┴────────────┘ │
│                             │
│  ⚡ Canyon Ridge Chargers   │  ← Charger context header
│  3 open stalls              │
│                             │
│  ┌─────────────────────────┐│
│  │ [photo]  Asadas Grill   ││  ← Merchant card
│  │          ★ 4.5 (128)    ││
│  │          3 min walk      ││
│  │  🟢 2 here now          ││  ← Social proof badge (consistent)
│  │                         ││
│  │  [Add EV Arrival →]     ││  ← Primary CTA on card
│  └─────────────────────────┘│
│                             │
│  ┌─────────────────────────┐│
│  │ [photo]  Epoch Coffee   ││
│  │  ...                    ││
│  └─────────────────────────┘│
│                             │
│  Coffee  Dining  Grocery    │  ← Category filter chips
│  Retail  Pharmacy           │     (selected: filled blue, unselected: outline)
└─────────────────────────────┘
```

**States:**
- **No charger nearby:** "Drive to a charger to see nearby merchants" + map
- **At charger, no merchants:** "No participating merchants near this charger yet"
- **Active session exists:** Show active session card instead of list (see Screen 4)

**Filter chips behavior:**
- Tap to toggle (multi-select)
- Selected: `bg-blue-600 text-white`
- Unselected: `bg-white text-gray-600 border border-gray-200`
- `aria-pressed` for accessibility
- Filters merchant list in real-time

### Screen 2: Merchant Detail

```
┌─────────────────────────────┐
│  [← Back]                   │
│                             │
│  [═══════ hero photo ══════]│
│  🟢 2 here now              │  ← Badge overlay, top-left
│                             │
│  Asadas Grill               │
│  ★ 4.5 (128 reviews)       │
│  Mexican · $$ · Open now    │
│                             │
│  ⚡ Tesla Supercharger       │
│     3 min walk · 2 open     │
│                             │
│  ┌─────────────────────────┐│
│  │                         ││
│  │   🛒 Add EV Arrival     ││  ← PRIMARY CTA (large, blue)
│  │                         ││
│  └─────────────────────────┘│
│                             │
│  📱 View order options      │  ← Secondary: deep link to menu
│                             │
│  128 EV drivers visited     │
│  42 verified this month     │  ← Trust proof (no exclusives needed)
└─────────────────────────────┘
```

**"Add EV Arrival" tap → triggers:**
1. Check if vehicle is set. If not → Vehicle Setup sheet (one-time).
2. Show confirmation bottom sheet (Screen 3).

### Screen 3: EV Arrival Confirmation (Bottom Sheet)

```
┌─────────────────────────────┐
│                             │
│   ─────  (drag handle)      │
│                             │
│   EV Curbside Arrival       │  ← or "EV Dine-In Arrival"
│   at Asadas Grill           │
│                             │
│   🚗 Blue Tesla Model 3    │  ← From cached vehicle
│      [Edit vehicle]         │
│                             │
│   When you arrive at the    │
│   charger, we'll notify     │
│   Asadas Grill to have      │
│   your order ready.         │
│                             │
│   ┌───────────────────────┐ │
│   │  Confirm EV Arrival   │ │  ← Triggers "Verifying..." interstitial
│   └───────────────────────┘ │
│                             │
│   Cancel                    │
└─────────────────────────────┘
```

**On "Confirm EV Arrival":**
1. Show "Verifying..." interstitial (1 second, animated shield icon)
2. POST `/v1/arrival/create`
3. Transition to Screen 4

### Screen 4: Active Session — Order Binding

```
┌─────────────────────────────┐
│  EV Arrival Active          │
│  Asadas Grill · EV Curbside │
│                             │
│  ✅ On-site confirmed       │
│                             │
│  ── Step 1: Place your order│
│                             │
│  ┌───────────────────────┐  │
│  │  🛒 Order from Asadas │  │  ← Deep link (in-app browser or external)
│  └───────────────────────┘  │
│                             │
│  ── Step 2: Enter order #   │
│                             │
│  ┌──────────────────┐       │
│  │ Order #           │      │  ← Text input
│  └──────────────────┘       │
│  ┌───────────────────────┐  │
│  │     Save Order #      │  │
│  └───────────────────────┘  │
│                             │
│  ── Status                  │
│  ⏳ Waiting for arrival     │  ← Updates when geofence triggers
│     at charger              │
│                             │
│  Expires in 1h 45m          │
│                             │
│  [Cancel arrival]           │  ← Tertiary, destructive
└─────────────────────────────┘
```

**After order # entered:**
- "Save Order #" → PUT `/v1/arrival/{id}/order`
- Status text updates to show order info
- If POS resolved: "Order #1234 · $28.47 · Placed"
- If manual: "Order #1234 · Saved"

**After geofence triggers:**
- Native bridge fires `confirm-arrival`
- Status updates: "✅ Asadas Grill notified — On-site now"
- Shows: "Your order details have been sent to the merchant"

### Screen 5: Completion

After merchant confirms (or driver taps "I've Arrived — Done"):

```
┌─────────────────────────────┐
│                             │
│         ✅                  │
│                             │
│   Visit Complete            │
│   Asadas Grill              │
│                             │
│   EV Curbside · Order #1234 │
│                             │
│   How was your experience?  │
│                             │
│   👍        👎              │
│                             │
│   [If 👎 tapped:]          │
│   ┌────────┐┌─────────────┐│
│   │Wrong   ││Too crowded  ││ ← Reason chips (single-select)
│   │hours   ││             ││
│   └────────┘└─────────────┘│
│   ┌────────┐┌─────────────┐│
│   │Slow    ││Other        ││
│   │service ││             ││
│   └────────┘└─────────────┘│
│                             │
│   [If 👍 tapped:]          │
│   ┌───────────────────────┐ │
│   │What did you love?     │ │ ← Optional text (140 char)
│   └───────────────────────┘ │
│                             │
│   ┌───────────────────────┐ │
│   │        Done           │ │
│   └───────────────────────┘ │
└─────────────────────────────┘
```

### Vehicle Setup (One-time Bottom Sheet)

Triggered on first "Add EV Arrival" if no vehicle saved:

```
┌─────────────────────────────┐
│   ─────                     │
│                             │
│   What do you drive?        │
│                             │
│   Color                     │
│   ┌───────────────────────┐ │
│   │ [White ▼]             │ │  ← Dropdown: White, Black, Blue, Red,
│   └───────────────────────┘ │     Silver, Gray, Green, Other
│                             │
│   Model                     │
│   ┌───────────────────────┐ │
│   │ Tesla Model 3          │ │  ← Text input with autocomplete
│   └───────────────────────┘ │     (common EVs pre-populated)
│                             │
│   This helps merchants      │
│   find you at the charger.  │
│                             │
│   ┌───────────────────────┐ │
│   │       Save            │ │
│   └───────────────────────┘ │
└─────────────────────────────┘
```

### Deep Link Return Flow

When driver orders externally and returns:
1. App registers universal link: `https://app.nerava.network/return`
2. Merchant ordering page includes "Return to Nerava" link (or we instruct driver)
3. On return, app checks for active session → shows Screen 4 with order # input focused
4. iOS: `application(_:open:options:)` routes to active session screen

### Transitions (all screens)

| From → To | Animation | Duration |
|-----------|-----------|----------|
| Home → Merchant Detail | Slide up from bottom | 300ms ease-out |
| Merchant Detail → Confirmation Sheet | Bottom sheet rise | 250ms ease-out |
| Confirmation → Active Session | Crossfade with "Verifying..." | 200ms + 1s hold |
| Active → Completion | Crossfade | 200ms |
| Any → Back | Reverse of forward | Same duration |
| `prefers-reduced-motion` | All transitions instant | 0ms |

---

## 7. Merchant UX Flows

### Notification Format (SMS)

```
NERAVA EV ARRIVAL 🚗

Order #1234
Type: EV Curbside
Vehicle: Blue Tesla Model 3
Status: On-site now

Driver is charging at [Charger Name] near your location.

Reply DONE 1234 when delivered.
Reply HELP for support.
```

(Where `1234` is the session's `merchant_reply_code` — a unique 4-digit code
generated per session so DONE replies can be mapped to the correct session.)

**For EV Dine-In:**

```
NERAVA EV ARRIVAL 🍽️

Order #5678
Type: EV Dine-In (party of 2)
Name: James K.
Status: On-site now

Driver is charging at [Charger Name]. They'll walk over shortly.

Reply DONE 5678 when seated.
```

### SMS Reply Handling

| Reply | Action |
|-------|--------|
| `DONE {code}` | Looks up session by `merchant_reply_code`, marks as merchant-confirmed |
| `HELP` | Sends merchant a link to dashboard |
| `CANCEL` | Marks session as merchant-canceled (edge case) |
| Anything else | "Reply DONE when order is delivered, or HELP for support." |

### Merchant Dashboard (Merchant Portal additions)

Add to existing merchant portal (`apps/merchant/`):

**New tab: "EV Arrivals"**

```
┌──────────────────────────────────────┐
│ Overview | Exclusives | EV Arrivals  │  ← New tab
│──────────────────────────────────────│
│                                      │
│  Today: 3 arrivals · $87.41 total   │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ 🟢 ACTIVE                   │    │
│  │ Order #1234 · EV Curbside   │    │
│  │ Blue Tesla Model 3          │    │
│  │ Arrived 5 min ago           │    │
│  │                             │    │
│  │ [Mark Delivered]            │    │
│  └──────────────────────────────┘    │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ ✅ COMPLETED                 │    │
│  │ Order #5678 · EV Dine-In    │    │
│  │ White Rivian R1S            │    │
│  │ Completed 1h ago · $34.50   │    │
│  └──────────────────────────────┘    │
│                                      │
│  Notification Settings               │
│  SMS: (512) 555-1234 ✓              │
│  Email: Off                          │
│  [Edit settings]                     │
└──────────────────────────────────────┘
```

---

## 8. Trust & Verification (Without Exclusives)

### How We Prove Value

The old model required an exclusive (free margarita) to justify verification. The new model doesn't.

**Value chain:**
1. **Driver presence is verified** — geofence confirms driver is physically at the charger
2. **Order is real** — POS integration confirms order exists and its value (or driver manually enters)
3. **Merchant is notified** — SMS/email with vehicle details enables personalized service
4. **Delivery is confirmed** — Merchant replies DONE or taps confirm in dashboard
5. **Both sides benefit without a coupon:**
   - Driver gets coordinated service (food ready on arrival, table prepped)
   - Merchant gets a qualified, spending customer delivered to their awareness

### Trust Layers

| Layer | What it proves | How |
|-------|---------------|-----|
| Geofence verification | Driver is physically at the charger | Native bridge + lat/lng within 150m of charger |
| Order binding | Driver placed a real order | POS lookup confirms order number exists |
| Order total | Revenue is real | POS returns exact amount, or driver estimates |
| Merchant confirmation | Service was delivered | Merchant replies DONE to SMS |
| Feedback loop | Quality signal | Thumbs + reason chips from driver |

### Billing Justification

The merchant pays 5% because:
- We brought them a **verified, spending customer** they wouldn't have otherwise known about
- We gave them **advance notice** to prepare (EV Curbside → bring to charger; EV Dine-In → prep table)
- We provided **vehicle identification** so staff can find the right customer
- This is lower than DoorDash (15-30%), Uber Eats (15-30%), or Yelp ads (variable CPM with no conversion guarantee)

### Social Proof (Consistent)

All surfaces (card, detail, endpoint) use the same green badge:

```tsx
// SocialProofBadge.tsx — single component, used everywhere
<span className="inline-flex items-center gap-1 bg-green-500/90 text-white text-xs
  font-medium px-2 py-0.5 rounded-full">
  <span className="w-1.5 h-1.5 bg-white rounded-full" />
  {count} here now
</span>
```

Positioned: top-left overlay on merchant hero image (card and detail screen).

---

## 9. Rollout Plan — 7 Days

### Day 1–2: Backend Core

| Task | Owner | Notes |
|------|-------|-------|
| Alembic migration: `arrival_sessions`, `merchant_notification_config`, `billing_events`, user vehicle fields, merchant ordering fields | Backend | Single migration file |
| SQLAlchemy models: `ArrivalSession`, `MerchantNotificationConfig`, `BillingEvent` | Backend | |
| `POSAdapter` interface + `ManualPOSAdapter` | Backend | Toast adapter is a stub |
| `POST /v1/arrival/create` | Backend | Core session creation |
| `PUT /v1/arrival/{id}/order` | Backend | Order binding + POS lookup |
| `POST /v1/arrival/{id}/confirm-arrival` | Backend | Geofence gate + notification trigger |
| `PUT /v1/account/vehicle` | Backend | Vehicle CRUD |
| `GET /v1/arrival/active` | Backend | Active session check |
| PostHog events for all endpoints | Backend | |

### Day 3: Notification Service + Merchant Confirm

| Task | Owner | Notes |
|------|-------|-------|
| `NotificationService` — SMS via Twilio (reuse existing pattern) | Backend | Async, executor thread |
| SMS reply webhook (Twilio → `/v1/webhooks/twilio-sms`) | Backend | Parse DONE/HELP/CANCEL |
| `POST /v1/arrival/{id}/merchant-confirm` | Backend | Dashboard + SMS |
| `POST /v1/arrival/{id}/feedback` | Backend | Driver feedback |
| Merchant notification config endpoints | Backend | |

### Day 4–5: Driver App

| Task | Owner | Notes |
|------|-------|-------|
| Mode selector (EV Curbside / EV Dine-In) — segmented control at top | Frontend | Replace current header |
| Update merchant card: "Add EV Arrival" CTA | Frontend | Replace "Secure Spot" |
| Merchant detail: rework CTAs (Add EV Arrival primary, order link secondary) | Frontend | |
| Vehicle setup bottom sheet (one-time) | Frontend | |
| Confirmation bottom sheet with "Verifying..." interstitial | Frontend | |
| Active session screen (order input, status, deep link) | Frontend | |
| Completion screen with feedback (thumbs + reason chips + comment) | Frontend | |
| Native bridge: wire geofence → `confirm-arrival` API call | Frontend | |
| Fix "Done Charging" → context-aware "I've Arrived" / "Visit Complete" | Frontend | |
| Filter chips with selected state + `aria-pressed` | Frontend | |
| Screen transitions (bottom sheet, crossfade) + reduced-motion | Frontend | |
| Social proof badge consistent across card + detail | Frontend | |
| Skeleton loaders verified under real latency | Frontend | |

### Day 6: Merchant Portal + Polish

| Task | Owner | Notes |
|------|-------|-------|
| "EV Arrivals" tab in merchant portal | Frontend | List + confirm button |
| Notification settings in merchant portal | Frontend | SMS phone + email |
| Account screen: profile, visit history, reputation tier | Frontend | |
| OTP per-digit aria-labels | Frontend | |
| OG/Twitter card images created + deployed | Infra | |
| iOS deep-link routing (native handler in AppDelegate) | iOS | |
| Wire RBAC to admin endpoints | Backend | |
| ORM migration for remaining raw SQL in intent endpoints | Backend | |

### Day 7: Integration Test + Deploy

| Task | Owner | Notes |
|------|-------|-------|
| End-to-end test: create arrival → bind order → geofence → notify → confirm | QA | |
| SMS notification test with real Twilio | QA | |
| Toast adapter stub test (manual fallback) | QA | |
| Backend pytest: arrival endpoints + billing + signature | QA | |
| Deploy to staging → smoke test | Infra | |
| Deploy to production | Infra | |

### Deferred (Post-7-day)

- Toast OAuth flow + real `ToastPOSAdapter` implementation (needs Toast partner API access)
- Square POS adapter (reuse existing `square_service.py` pattern)
- Stripe invoicing for merchant billing (currently manual/invoice)
- Push notifications (in addition to SMS)
- Battery-aware "almost done charging" pre-notification
- Multi-session support (driver with 2 orders at 2 merchants)
- Merchant app native (currently web dashboard)

---

## 10. Architectural Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Partial unique index on `driver_id` only** (not `driver_id, status`) | A unique constraint on `(driver_id, status)` would allow a driver to have `pending_order` AND `awaiting_arrival` simultaneously — different statuses. The partial index on `driver_id` alone, filtered to active statuses, correctly enforces one-at-a-time. |
| 2 | **Copy vocabulary: Armed → On-site confirmed → Merchant notified → Completed** | "Arrival confirmed" was ambiguous — it could mean the system confirmed or the merchant confirmed. "On-site confirmed" is what the driver sees (geofence verified), "Merchant notified" is what happened next, "Completed" is terminal. |
| 3 | **`merchant_reply_code` (4 digits) per session** | Without a code, a DONE reply from a merchant's phone can't be mapped to a specific session. 4 digits gives 10k combinations — more than enough for concurrent sessions from one merchant phone. |
| 4 | **Manual billing rules: require estimate OR merchant total, else `completed_unbillable`** | With no POS integration, we need at least one number to bill on. Precedence: POS > merchant_reported > driver_estimate. If none exist, session completes but we don't bill — better than billing $0 or guessing. |
| 5 | **`confirm-arrival` requires `charger_id` + server-side distance check** | Without charger_id, the endpoint just trusts lat/lng from the client. By requiring charger_id, the server looks up the charger's known coordinates and independently verifies the driver is within 250m — defeating GPS spoofing. |
| 6 | **Rename `/v1/intent/capture` → `/v1/charge-context/nearby`** | "Intent" implies user intent detection, which this endpoint doesn't do. It returns nearby merchants for a charging location — that's context, not intent. The new name is accurate and avoids confusion with the old intent model. |
| 7 | **Separate `merchant_pos_credentials` from `merchant_notification_config`** | POS tokens are secrets (encrypted OAuth tokens). Notification preferences are not secrets. Mixing them in one table means every notification settings edit touches the same row as token storage. Separation means we can give different teams/UIs different access levels. |
| 8 | **Separate "analytics completion" from "billable completion"** | `ev_arrival.completed` fires on ALL completions (including `completed_unbillable`). `ev_arrival.billed` fires only when a billing event is created. This lets us track conversion rate vs. billable rate independently. |
| 9 | **POS Adapter abstraction with ManualPOSAdapter as default** | Toast/Square integrations are deferred. The adapter pattern means the billing pipeline works identically regardless of POS — ManualPOSAdapter just returns `status: 'unknown'`. When Toast is ready, we swap one class. |
| 10 | **SMS via Twilio with executor thread (same as OTP)** | Twilio's Python client is synchronous. Wrapping in `loop.run_in_executor()` avoids blocking the async event loop. This is the same pattern used by the existing OTP service, proven in production. |

---

## 11. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | **Toast API access delayed** — Partner approval takes weeks, not days | High | Medium | ManualPOSAdapter is the default. Toast is additive, not blocking. Abstraction layer means we can swap in Toast later without changing any other code. |
| 2 | **Geofence false positives** — Driver notified as "arrived" when driving past | Medium | High | Use 150m radius (tight). Require 30s dwell time before triggering (reuse existing `NATIVE_CHARGER_DWELL_SECONDS`). Add "I'm not here yet" cancel option. |
| 3 | **Merchant ignores SMS notifications** — SMS goes to spam, phone on silent | High | High | Follow up with email if no DONE reply within 15 min. Dashboard shows active arrivals. Onboarding emphasizes notification setup. Long-term: native push. |
| 4 | **Order number mismatch** — Driver enters wrong number, POS can't find it | Medium | Medium | Graceful fallback to manual. Show "Order not found in Toast — we'll use your entry." Merchant can still identify by vehicle. |
| 5 | **Billing disputes** — Merchant disputes order total or says delivery didn't happen | Medium | High | Both sides must confirm (driver geofence + merchant DONE). POS-verified totals are authoritative. Dispute resolution: human review with PostHog audit trail. |
| 6 | **Low driver adoption** — Drivers don't understand why to "Add EV Arrival" | Medium | High | Onboarding tooltip on first visit. Value prop copy: "Get your order ready before you walk in." A/B test CTA copy. Track funnel drop-off in PostHog. |
| 7 | **Deep link return fails** — Driver can't get back to Nerava after ordering | Medium | Medium | Multiple return paths: universal link, "Open Nerava" button on thank-you page (requires merchant cooperation), manual app switch. iOS banner reminder. |
| 8 | **SMS costs scale** — Twilio SMS at $0.0079/segment, 1000 arrivals/day = $240/month | Low | Low | Acceptable at scale. Migrate to push notifications for drivers. Keep SMS for merchants (they expect it). Batch billing notifications into daily digest. |
| 9 | **Charger data stale** — Charger is removed or moved, merchants still show | Low | Medium | Existing charger data refresh pipeline. Add "Report issue" in app. Flag merchants with 0 arrivals in 30 days for review. |
| 10 | **Single active session limit frustrates users** — Driver wants curbside from 2 places | Low | Low | Defer multi-session. Copy: "Complete your current arrival to start a new one." This simplifies v1 enormously and matches real behavior (one order at a time). |

---

## Appendix: Claude Code / Cursor / Codex Workflow

### How to use each tool this week:

**Claude Code** — Architecture + thinking + file discovery
- Use for: "What files need to change?", "Design the migration", "Review this API contract"
- Best at: Reading multiple files, understanding cross-cutting concerns, generating migration SQL
- This week: Days 1-2 backend design, Day 6 integration review

**Cursor** — Code implementation
- Use for: Writing the actual components, endpoints, models
- Best at: Single-file or 2-3 file changes with clear specs
- Prompt pattern: Give it the exact file path, the exact change, existing patterns to follow
- This week: Days 2-6 for all implementation tasks

**Codex** — Testing + validation
- Use for: Writing pytest files, vitest files, integration test scripts
- Best at: Generating comprehensive test cases from specs
- Prompt pattern: Give it the API contract + edge cases + expected responses
- This week: Day 7 for test suite, plus spot checks on Days 3-5

### Cursor Prompt Templates

**For backend endpoints:**
```
You are Cursor. Create the arrival session endpoints.

File: backend/app/routers/arrival.py
Prefix: /v1/arrival
Auth: Depends(get_current_user) from backend/app/dependencies/auth.py
DB: Depends(get_db) from backend/app/db.py
Analytics: get_analytics_client() from backend/app/services/analytics.py

Follow the pattern in backend/app/routers/exclusive.py for:
- Pydantic request/response models
- Error handling with HTTPException
- PostHog event capture

Endpoints:
[paste the API contracts from Section 4 above]
```

**For frontend components:**
```
You are Cursor. Build the EV Arrival active session screen.

File: apps/driver/src/components/EVArrival/ActiveSession.tsx
Follow patterns from: apps/driver/src/components/ExclusiveActiveView/ExclusiveActiveView.tsx
API client: apps/driver/src/services/api.ts (fetchAPI function)
Analytics: apps/driver/src/analytics/ (capture function + DRIVER_EVENTS)

[paste Screen 4 wireframe from Section 6]
```

**For Codex testing:**
```
You are Codex. Write tests for the arrival system.

Backend tests: backend/tests/test_arrival.py
Use conftest.py fixtures (client, db) from backend/tests/conftest.py

Test cases:
1. Create arrival session → returns 201 with session_id
2. Create second session while one is active → returns 409
3. Bind order number → status transitions to awaiting_arrival
4. Confirm arrival outside geofence (>150m) → returns 403
5. Confirm arrival inside geofence → status transitions, merchant notified
6. Merchant confirm → creates billing event with correct fee
7. Expired session → returns 410 Gone
8. Vehicle required but not set → response includes vehicle_required: true
9. POS lookup fails → falls back to manual, session still works
10. Feedback with thumbs down + reason chip → stored correctly
```

---

*This document is the single source of truth for the EV Arrival pivot. All implementation should reference it. Update it as decisions change.*
