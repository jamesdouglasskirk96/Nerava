# Nerava Engineering Reference — Complete Platform Architecture

**Date:** 2026-02-03
**Purpose:** Single source of truth for engineering onboarding. Upload to NotebookLM. A new CTO or Lead Engineer should be able to understand the entire system and generate working Cursor prompts from this document alone.

---

## Table of Contents

1. [What Nerava Is](#1-what-nerava-is)
2. [Repository Structure](#2-repository-structure)
3. [Technology Stack](#3-technology-stack)
4. [Core Abstraction: Arrival Is the Invariant](#4-core-abstraction-arrival-is-the-invariant)
5. [Database Schema — Complete](#5-database-schema--complete)
6. [Backend Architecture](#6-backend-architecture)
7. [Arrival Session System — End-to-End](#7-arrival-session-system--end-to-end)
8. [Merchant Onboarding Funnel — End-to-End](#8-merchant-onboarding-funnel--end-to-end)
9. [Authentication System](#9-authentication-system)
10. [Notification System](#10-notification-system)
11. [POS Adapter System](#11-pos-adapter-system)
12. [Billing System](#12-billing-system)
13. [Analytics System (PostHog)](#13-analytics-system-posthog)
14. [Driver App (React)](#14-driver-app-react)
15. [Merchant Portal (React)](#15-merchant-portal-react)
16. [Landing Page (Next.js)](#16-landing-page-nextjs)
17. [iOS Native Shell](#17-ios-native-shell)
18. [Android Native Shell](#18-android-native-shell)
19. [Infrastructure & Deployment](#19-infrastructure--deployment)
20. [Configuration Reference](#20-configuration-reference)
21. [API Endpoint Catalog](#21-api-endpoint-catalog)
22. [State Machine Reference](#22-state-machine-reference)
23. [Error Codes & HTTP Status Codes](#23-error-codes--http-status-codes)
24. [PostHog Event Catalog](#24-posthog-event-catalog)
25. [File Index — Where Everything Lives](#25-file-index--where-everything-lives)
26. [How to Write Cursor Prompts for This Codebase](#26-how-to-write-cursor-prompts-for-this-codebase)

---

## 1. What Nerava Is

Nerava is **arrival-aware commerce infrastructure for the EV era**. When a driver plugs in at a charger near a participating merchant, Nerava verifies that arrival and notifies the merchant in real time — including the driver's order number, vehicle description, and arrival type (Curbside or Dine-In).

Drivers order through the merchant's existing channels (Toast, Square, web, phone). Nerava never touches payments or fulfillment. We are the trust layer between "driver is charging nearby" and "merchant acts on that fact."

**Revenue model:** Per-arrival platform fee. Default 5% (500 basis points) of order value on completed, verified arrivals.

**Core principle:** Arrival is the invariant. Charging and ordering are modifiers.

---

## 2. Repository Structure

```
Nerava/
├── backend/                          # FastAPI Python backend
│   ├── app/
│   │   ├── core/config.py           # All env vars and settings (90+ vars)
│   │   ├── db.py                    # SQLAlchemy engine, session factory
│   │   ├── main.py                  # FastAPI app, middleware, router registration
│   │   ├── lifespan.py              # App startup/shutdown events
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── arrival_session.py   # ArrivalSession (core EV Arrival model)
│   │   │   ├── billing_event.py     # BillingEvent (revenue tracking)
│   │   │   ├── merchant_notification_config.py
│   │   │   ├── merchant_pos_credentials.py
│   │   │   ├── while_you_charge.py  # Merchant + ChargerMerchant + Charger models
│   │   │   ├── user.py              # User model (drivers + merchants + admins)
│   │   │   ├── domain.py            # DomainMerchant (owner relationship)
│   │   │   ├── claim_session.py     # ClaimSession (merchant onboarding)
│   │   │   └── ...
│   │   ├── routers/                 # FastAPI route handlers
│   │   │   ├── arrival.py           # 7 EV Arrival endpoints (/v1/arrival/*)
│   │   │   ├── charge_context.py    # Nearby merchants (/v1/charge-context/*)
│   │   │   ├── twilio_sms_webhook.py # SMS reply handler
│   │   │   ├── merchant_arrivals.py # Merchant-facing arrival + notification config
│   │   │   ├── merchant_funnel.py   # Search, resolve, preview, text-link
│   │   │   ├── merchant_claim.py    # 4-step claim flow
│   │   │   ├── auth_domain.py       # OTP, magic links, Google SSO
│   │   │   ├── account.py           # Vehicle setup, profile
│   │   │   ├── admin_domain.py      # Admin endpoints
│   │   │   └── ...
│   │   ├── services/                # Business logic services
│   │   │   ├── pos_adapter.py       # POSAdapter ABC + Manual/Toast/Square
│   │   │   ├── notification_service.py # SMS via Twilio
│   │   │   ├── analytics.py         # PostHog client singleton
│   │   │   ├── merchant_enrichment.py # Google Places enrichment
│   │   │   ├── otp_service_v2.py    # Phone OTP with rate limiting
│   │   │   └── ...
│   │   ├── dependencies/            # FastAPI dependency injection
│   │   │   ├── auth.py              # JWT validation, role checking
│   │   │   └── ...
│   │   └── middleware/              # Request middleware
│   ├── alembic/versions/           # Database migrations
│   │   ├── 062_add_ev_arrival_tables.py  # EV Arrival schema
│   │   └── ...
│   ├── tests/                      # pytest test suites
│   └── requirements.txt
│
├── apps/
│   ├── driver/                     # React driver web app (Vite + Tailwind)
│   │   ├── src/
│   │   │   ├── App.tsx             # Routes: /, /driver, /wyc, /pre-charging, /m/:merchantId
│   │   │   ├── components/
│   │   │   │   ├── EVArrival/      # 5 EV Arrival components (NOT yet wired in)
│   │   │   │   │   ├── ModeSelector.tsx
│   │   │   │   │   ├── VehicleSetup.tsx
│   │   │   │   │   ├── ConfirmationSheet.tsx
│   │   │   │   │   ├── ActiveSession.tsx
│   │   │   │   │   └── CompletionScreen.tsx
│   │   │   │   ├── DriverHome/DriverHome.tsx  # Main orchestrator (1122 lines)
│   │   │   │   ├── MerchantDetails/
│   │   │   │   └── shared/
│   │   │   ├── hooks/
│   │   │   │   └── useNativeBridge.ts  # iOS/Android bridge detection
│   │   │   ├── services/
│   │   │   │   ├── api.ts           # fetchAPI + React Query hooks
│   │   │   │   └── auth.ts          # OTP start/verify
│   │   │   └── analytics/
│   │   └── vite.config.ts
│   │
│   ├── merchant/                   # React merchant portal (Vite + Tailwind)
│   │   ├── app/
│   │   │   ├── App.tsx             # Routes: /find, /preview, /claim, dashboard/*
│   │   │   ├── components/
│   │   │   │   ├── EVArrivals.tsx   # Merchant arrival dashboard
│   │   │   │   ├── FindBusiness.tsx # Google Places search
│   │   │   │   ├── MerchantPreview.tsx # HMAC-signed preview page
│   │   │   │   ├── ClaimBusiness.tsx # 4-step claim flow
│   │   │   │   └── ...
│   │   │   └── services/api.ts
│   │   └── vite.config.ts
│   │
│   ├── admin/                      # React admin portal
│   └── landing/                    # Next.js marketing site
│
├── mobile/
│   └── nerava_android/             # Native Android shell (Kotlin)
│
├── Nerava/                         # iOS Xcode project (Swift)
│   └── Nerava/
│       └── Services/
│           ├── NativeBridge.swift
│           ├── SessionEngine/
│           └── APIClient.swift
│
├── packages/
│   └── analytics/                  # Shared analytics package
│
├── infra/                          # Terraform, nginx
├── scripts/                        # Deploy, seed, validate scripts
└── docs/                           # Documentation
```

---

## 3. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic | Async where needed, sync DB by default |
| **Database** | PostgreSQL (prod), SQLite (dev) | PostGIS not used yet; haversine in Python |
| **Driver App** | React 18, TypeScript, Vite, Tailwind CSS, React Query | Deployed to S3 + CloudFront |
| **Merchant Portal** | React 18, TypeScript, Vite, Tailwind CSS | Same infra as driver app |
| **Landing Page** | Next.js 14, TypeScript, Tailwind CSS | Static export to S3 |
| **iOS Shell** | Swift, WKWebView, UIKit | Native bridge via postMessage |
| **Android Shell** | Kotlin, WebView, AndroidX | Native bridge via @JavascriptInterface |
| **Auth** | JWT (HS256), Phone OTP via Twilio Verify | Refresh tokens in localStorage |
| **SMS** | Twilio (messages.create) | ThreadPoolExecutor for async |
| **Analytics** | PostHog (self-hosted compatible) | Fire-and-forget, never crashes requests |
| **Payments** | Stripe (checkout sessions for Nova) | Billing events are DB records, not Stripe invoices yet |
| **Maps/Places** | Google Places API (New) | Circuit breaker + 24h cache TTL |
| **Vehicle Data** | Smartcar OAuth | Fully integrated, feature-flagged |
| **Hosting** | AWS App Runner (backend), S3 + CloudFront (frontends) | Terraform managed |
| **CI/CD** | Manual deploy scripts | `scripts/deploy_aws.py`, `scripts/deploy-frontend-s3.sh` |

---

## 4. Core Abstraction: Arrival Is the Invariant

The driver understands one thing: **"Nerava times my food to when I arrive or finish charging."**

The driver does not think about charger availability, kitchen timing, fulfillment logistics, or curbside vs dine-in decision trees. Those are merchant-side concerns.

**Canonical flow:**
1. **Before departure** — Driver may order. Order enters `pending_order` state. Kitchen does NOT fire.
2. **Arrival-aware trigger** — Geofence + location verification confirms presence. Order flips from scheduled to active. This is **Ready on Arrival**.
3. **Fulfillment** — Merchant-defined: walk-in pickup (default), eat-in-car (curbside), dine inside. Driver sees only: "Your order will be ready when you arrive."
4. **Ready After Charge** — Same system, trigger fires on charging completion or target SoC.

**Constraints:**
- Arrival is the source of truth
- Merchants cannot fire orders early
- No manual overrides that break arrival integrity
- Charging is a timing modifier, not the anchor

---

## 5. Database Schema — Complete

### Table: `arrival_sessions`
The core EV Arrival table. One row per driver session.

| Column | Type | Default | Nullable | Notes |
|--------|------|---------|----------|-------|
| `id` | UUID | uuid4 | No | Primary key |
| `driver_id` | Integer | — | No | FK → users.id |
| `merchant_id` | String | — | No | FK → merchants.id |
| `charger_id` | String | — | Yes | FK → chargers.id, bound at creation or confirmation |
| `arrival_type` | String(20) | — | No | 'ev_curbside' or 'ev_dine_in' |
| `order_number` | String(100) | — | Yes | Manual entry from driver |
| `order_source` | String(20) | — | Yes | 'manual', 'toast', 'square' |
| `order_total_cents` | Integer | — | Yes | From POS or driver estimate |
| `order_status` | String(20) | — | Yes | 'unknown', 'placed', 'ready', 'completed' |
| `driver_estimate_cents` | Integer | — | Yes | Driver's pre-order estimate |
| `merchant_reported_total_cents` | Integer | — | Yes | Merchant-reported total via SMS or dashboard |
| `total_source` | String(20) | — | Yes | 'pos', 'merchant_reported', 'driver_estimate' |
| `vehicle_color` | String(30) | — | Yes | Copied from User at session creation (immutable) |
| `vehicle_model` | String(60) | — | Yes | Copied from User at session creation (immutable) |
| `status` | String(30) | 'pending_order' | No | See state machine below |
| `merchant_reply_code` | String(4) | auto-gen | Yes | 4-digit code for SMS mapping |
| `created_at` | DateTime | utcnow | No | |
| `order_bound_at` | DateTime | — | Yes | When order number was entered |
| `geofence_entered_at` | DateTime | — | Yes | When arrival was confirmed |
| `merchant_notified_at` | DateTime | — | Yes | When SMS was sent |
| `merchant_confirmed_at` | DateTime | — | Yes | When merchant replied DONE |
| `completed_at` | DateTime | — | Yes | Terminal timestamp |
| `expires_at` | DateTime | — | No | 2 hours from creation |
| `arrival_lat` | Float | — | Yes | Geofence verification lat |
| `arrival_lng` | Float | — | Yes | Geofence verification lng |
| `arrival_accuracy_m` | Float | — | Yes | GPS accuracy at confirmation |
| `platform_fee_bps` | Integer | 500 | No | 5% = 500 basis points |
| `billable_amount_cents` | Integer | — | Yes | Calculated: total * fee / 10000 |
| `billing_status` | String(20) | 'pending' | Yes | 'pending', 'invoiced', 'paid' |
| `feedback_rating` | String(10) | — | Yes | 'up' or 'down' |
| `feedback_reason` | String(50) | — | Yes | Chip selection on thumbs-down |
| `feedback_comment` | String(200) | — | Yes | Free text on thumbs-up |
| `idempotency_key` | String(100) | — | Yes | Unique, prevents duplicates |

**Indexes:**
- `idx_arrival_driver_active` on (driver_id, status)
- `idx_arrival_merchant_status` on (merchant_id, status)
- `idx_arrival_billing` on (billing_status)
- `idx_arrival_created` on (created_at)
- `idx_arrival_reply_code` on (merchant_reply_code)
- `idx_arrival_one_active_per_driver` — **partial unique** on (driver_id) WHERE status IN active statuses (PostgreSQL only)

**Constants defined on model:**
```python
ACTIVE_STATUSES = {"pending_order", "awaiting_arrival", "arrived", "merchant_notified"}
TERMINAL_STATUSES = {"completed", "completed_unbillable", "expired", "canceled"}
VALID_TRANSITIONS = {
    "pending_order": {"awaiting_arrival", "expired", "canceled"},
    "awaiting_arrival": {"arrived", "expired", "canceled"},
    "arrived": {"merchant_notified", "expired", "canceled"},
    "merchant_notified": {"completed", "completed_unbillable", "expired", "canceled"},
}
```

**Helper:** `_generate_reply_code()` returns random 4-digit string.

---

### Table: `billing_events`

| Column | Type | Default | Nullable | Notes |
|--------|------|---------|----------|-------|
| `id` | UUID | uuid4 | No | Primary key |
| `arrival_session_id` | UUID | — | No | FK → arrival_sessions.id |
| `merchant_id` | String | — | No | FK → merchants.id |
| `order_total_cents` | Integer | — | No | The total used for billing |
| `fee_bps` | Integer | — | No | e.g. 500 = 5% |
| `billable_cents` | Integer | — | No | Calculated: total * fee / 10000 |
| `total_source` | String(20) | — | No | 'pos', 'merchant_reported', 'driver_estimate' |
| `status` | String(20) | 'pending' | No | 'pending', 'invoiced', 'paid', 'disputed' |
| `invoice_id` | String(100) | — | Yes | Stripe invoice ID (future) |
| `created_at` | DateTime | utcnow | No | |
| `invoiced_at` | DateTime | — | Yes | |
| `paid_at` | DateTime | — | Yes | |

---

### Table: `merchant_notification_config`

| Column | Type | Default | Nullable | Notes |
|--------|------|---------|----------|-------|
| `id` | Integer | auto | No | Primary key |
| `merchant_id` | String | — | No | FK → merchants.id, UNIQUE |
| `notify_sms` | Boolean | True | No | |
| `notify_email` | Boolean | False | No | Email not implemented |
| `sms_phone` | String(20) | — | Yes | E.164 format |
| `email_address` | String(255) | — | Yes | |
| `pos_integration` | String(20) | 'none' | No | 'none', 'toast', 'square' |
| `created_at` | DateTime | utcnow | No | |
| `updated_at` | DateTime | utcnow | No | |

---

### Table: `merchant_pos_credentials`

| Column | Type | Default | Nullable | Notes |
|--------|------|---------|----------|-------|
| `id` | Integer | auto | No | Primary key |
| `merchant_id` | String | — | No | FK → merchants.id, UNIQUE |
| `pos_type` | String(20) | — | No | 'toast', 'square' |
| `restaurant_guid` | String(100) | — | Yes | Toast-specific |
| `access_token_encrypted` | Text | — | Yes | Fernet-encrypted |
| `refresh_token_encrypted` | Text | — | Yes | Fernet-encrypted |
| `token_expires_at` | DateTime | — | Yes | |
| `created_at` | DateTime | utcnow | No | |
| `updated_at` | DateTime | utcnow | No | |

---

### Table: `merchants` (selected EV Arrival columns)

Added by migration 062:
| Column | Type | Notes |
|--------|------|-------|
| `ordering_url` | String(500) | Deep link or web URL for ordering (e.g. Toast online ordering) |
| `ordering_app_scheme` | String(100) | e.g. "toastapp://" |
| `ordering_instructions` | Text | e.g. "Order at counter" |

Key existing columns:
| Column | Type | Notes |
|--------|------|-------|
| `id` | String | Primary key, e.g. "m_abc123" |
| `name` | String | Merchant name |
| `place_id` | String | Google Places ID, unique |
| `lat`, `lng` | Float | Coordinates |
| `address`, `city`, `state`, `zip_code` | String | Location |
| `rating` | Float | Google rating |
| `user_rating_count` | Integer | Review count |
| `photo_url`, `primary_photo_url` | String | Photos |
| `photo_urls` | JSON | Array of photo URLs |
| `open_now` | Boolean | Current status |
| `hours_json` | JSON | Opening hours |
| `category` | String | 'coffee', 'restaurant', etc. |
| `primary_category` | String(32) | 'coffee', 'food', 'other' |
| `nearest_charger_id` | String(64) | Cached FK |
| `nearest_charger_distance_m` | Integer | Cached distance |

---

### Table: `charger_merchants` (junction table)

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer | Primary key |
| `charger_id` | String | FK → chargers.id |
| `merchant_id` | String | FK → merchants.id |
| `distance_m` | Float | Straight-line distance |
| `walk_duration_s` | Integer | Walking time from Google Distance Matrix |
| `walk_distance_m` | Float | Actual walking distance |
| `is_primary` | Boolean | Default False. Primary merchant flag. |
| `override_mode` | String | 'PRE_CHARGE_ONLY' or 'ALWAYS' |
| `suppress_others` | Boolean | Hide other merchants when primary exists |

Unique constraint: `(charger_id, merchant_id)`

---

### Table: `users` (selected EV Arrival columns)

Added by migration 062:
| Column | Type | Notes |
|--------|------|-------|
| `vehicle_color` | String(30) | e.g. "Blue" |
| `vehicle_model` | String(60) | e.g. "Tesla Model 3" |
| `vehicle_set_at` | DateTime | When vehicle was last set |

Key existing columns:
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer | Primary key |
| `public_id` | UUID | External identifier used in JWT `sub` claim |
| `email` | String | Nullable for phone-only users |
| `phone` | String | E.164 format, nullable for email-only users |
| `role_flags` | String | Comma-separated: "driver", "merchant_admin", "admin" |
| `auth_provider` | String | 'local', 'google', 'apple', 'phone' |
| `admin_role` | String | AdminRole enum value |

---

### Table: `claim_sessions`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `merchant_id` | String | FK → merchants.id or DomainMerchant.id |
| `business_name` | String | From form |
| `email` | String | Merchant contact email |
| `phone` | String | E.164 format |
| `phone_verified` | Boolean | Default False |
| `email_verified` | Boolean | Default False |
| `magic_link_token` | String | secrets.token_urlsafe(32) |
| `magic_link_expires_at` | DateTime | 15 minutes from send |
| `completed_at` | DateTime | When claim finished |
| `created_at` | DateTime | |

---

## 6. Backend Architecture

### App Initialization (`backend/app/main.py`)

1. Creates FastAPI app with title "Nerava Backend v9"
2. Mounts static files: `/app` (ui-mobile), `/assets`, `/static/merchant_photos_*`
3. Creates tables via `Base.metadata.create_all()` (SQLite dev only)
4. Adds middleware stack (order matters — first added = outermost):
   - LoggingMiddleware
   - MetricsMiddleware
   - RateLimitMiddleware (configurable requests_per_minute)
   - RegionMiddleware, ReadWriteRoutingMiddleware, CanaryRoutingMiddleware
   - AuthMiddleware
   - AuditMiddleware
   - CORSMiddleware

5. CORS origins (hardcoded + env):
   ```python
   cors_origins = [
       "http://localhost:8001", "http://127.0.0.1:8001",
       "http://localhost:3000", "http://localhost:5173",
       "https://app.nerava.app", "https://www.nerava.app",
       "https://app.nerava.network", "https://www.nerava.network",
       "https://merchant.nerava.network",
   ]
   ```

6. Registers 30+ routers (see Section 21 for full catalog)

### Dependency Injection Pattern

All route handlers use FastAPI's `Depends()`:
```python
@router.post("/v1/arrival/create")
async def create_arrival(
    request: CreateArrivalRequest,
    db: Session = Depends(get_db),
    driver: User = Depends(get_current_driver),
):
```

Key dependencies:
- `get_db()` — SQLAlchemy Session from session factory
- `get_current_driver()` — Decodes JWT, returns User or raises 401
- `get_current_driver_optional()` — Returns User or None (never raises)
- `require_role("admin")` — Role-based access control
- `get_analytics_client()` — PostHog singleton

### Error Handling Pattern

All routers use `HTTPException`:
```python
raise HTTPException(status_code=409, detail={
    "error": "ACTIVE_SESSION_EXISTS",
    "message": "You already have an active EV Arrival session",
    "session_id": str(existing.id)
})
```

Analytics calls never crash requests:
```python
try:
    analytics.capture("ev_arrival.created", ...)
except Exception:
    logger.warning("Failed to capture analytics event")
```

---

## 7. Arrival Session System — End-to-End

This is the core revenue-generating flow. Every line of code described here is implemented and tested.

### File: `backend/app/routers/arrival.py`
**Prefix:** `/v1/arrival`

### Constants
```python
SESSION_TTL_HOURS = 2
CHARGER_RADIUS_M = 250  # Max distance from charger for geofence verification
```

### Endpoint 1: POST /v1/arrival/create

**Auth:** Required (get_current_driver)
**Status Code:** 201 Created

**Request Schema:**
```python
class CreateArrivalRequest(BaseModel):
    merchant_id: str
    charger_id: Optional[str] = None
    arrival_type: str  # Pattern: ^(ev_curbside|ev_dine_in)$
    lat: float
    lng: float
    accuracy_m: Optional[float] = None
    idempotency_key: Optional[str] = None
```

**Response Schema:**
```python
class CreateArrivalResponse(BaseModel):
    session_id: str
    status: str  # Always "pending_order"
    merchant_name: str
    arrival_type: str
    ordering_url: Optional[str]
    ordering_instructions: Optional[str]
    expires_at: str  # ISO datetime
    vehicle: VehicleInfo
    vehicle_required: bool = False
```

**Logic Flow:**
1. Check idempotency key — return existing session if found
2. Query active sessions for this driver (status IN ACTIVE_STATUSES)
3. If active session exists → **409** `ACTIVE_SESSION_EXISTS` with existing session_id
4. Validate merchant exists → **404** if not
5. Validate charger exists (if charger_id provided) → **404** if not
6. Read vehicle info from User table. Set `vehicle_required=True` if either field missing
7. Create ArrivalSession:
   - status = "pending_order"
   - expires_at = now + 2 hours
   - merchant_reply_code = random 4-digit code
   - Vehicle fields copied from User (immutable snapshot)
8. Commit
9. PostHog: `ev_arrival.created`
10. Return response with ordering_url and ordering_instructions from Merchant

**Database Queries:**
- `ArrivalSession.filter(idempotency_key=key)` (if key provided)
- `ArrivalSession.filter(driver_id=X, status.in_(ACTIVE_STATUSES))`
- `Merchant.filter(id=merchant_id)`
- `Charger.filter(id=charger_id)` (if provided)
- INSERT ArrivalSession

---

### Endpoint 2: PUT /v1/arrival/{session_id}/order

**Auth:** Required
**Status Code:** 200

**Request:**
```python
class BindOrderRequest(BaseModel):
    order_number: str  # 1-100 chars
    estimated_total_cents: Optional[int] = None
```

**Response:**
```python
class BindOrderResponse(BaseModel):
    session_id: str
    status: str  # "awaiting_arrival"
    order_number: str
    order_source: str  # 'manual', 'toast', 'square'
    order_total_cents: Optional[int]
    order_status: str
```

**Logic Flow:**
1. Find session by id, verify belongs to driver → **404** if not
2. Check status is pending_order or awaiting_arrival → **400** if not
3. Check expiry → **410 Gone** if expired
4. Query MerchantNotificationConfig for pos_integration type
5. Query MerchantPOSCredentials
6. Get POS adapter via `get_pos_adapter(pos_integration, credentials)`
7. Call `adapter.lookup_order(order_number)` → POSOrder or None
8. If POS found order with total > 0:
   - order_source = pos_integration ('toast' or 'square')
   - order_total_cents = pos_order.total_cents
   - total_source = "pos"
9. Else (manual):
   - order_source = "manual"
   - order_total_cents = estimated_total_cents from request
   - total_source = "driver_estimate" (if estimate provided)
10. Set status = "awaiting_arrival", order_bound_at = now
11. Commit
12. PostHog: `ev_arrival.order_bound`

---

### Endpoint 3: POST /v1/arrival/{session_id}/confirm-arrival

**Auth:** Required
**Status Code:** 200
**This is the anti-spoofing gate.**

**Request:**
```python
class ConfirmArrivalRequest(BaseModel):
    charger_id: str  # REQUIRED for anti-spoofing
    lat: float
    lng: float
    accuracy_m: Optional[float] = None
```

**Response:**
```python
class ConfirmArrivalResponse(BaseModel):
    status: str
    merchant_notified: bool
    notification_method: str  # 'sms', 'email', 'both', 'none'
```

**Logic Flow:**
1. Find session, verify driver → **404**
2. Check status is awaiting_arrival or pending_order → **400**
3. Check expiry → **410 Gone**
4. Find charger by charger_id → **400** if not found
5. **Anti-spoofing:** Calculate haversine distance from (req.lat, req.lng) to (charger.lat, charger.lng)
6. If distance > 250m → **400** `TOO_FAR_FROM_CHARGER` with actual distance
7. Update session:
   - arrival_lat, arrival_lng, arrival_accuracy_m from request
   - geofence_entered_at = now
   - charger_id = req.charger_id (binds charger if not set at creation)
   - status = "arrived"
8. Query MerchantNotificationConfig
9. If config exists and sms_phone set:
   - Call `notify_merchant()` with all session details + merchant_reply_code
   - If notification sent: status = "merchant_notified", merchant_notified_at = now
10. Commit
11. PostHog: `ev_arrival.geofence_entered` + `ev_arrival.merchant_notified` (if sent)

**Haversine Implementation:**
```python
def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000  # Earth radius in meters
    # Standard haversine formula
    return distance_in_meters
```

---

### Endpoint 4: POST /v1/arrival/{session_id}/merchant-confirm

**Auth:** None (called from dashboard or SMS webhook)
**Status Code:** 200

**Request:**
```python
class MerchantConfirmRequest(BaseModel):
    confirmed: bool = True
    merchant_reported_total_cents: Optional[int] = None
```

**Response:**
```python
class MerchantConfirmResponse(BaseModel):
    status: str
    billable_amount_cents: Optional[int]
```

**Logic Flow:**
1. Find session → **404**
2. Check status is merchant_notified or arrived → **400**
3. merchant_confirmed_at = now
4. If merchant_reported_total_cents provided, store it
5. **Billing total precedence** (most important business rule):
   - If total_source == "pos" and order_total_cents > 0 → use POS total
   - Else if merchant_reported_total_cents > 0 → use merchant reported, set total_source = "merchant_reported"
   - Else if driver_estimate_cents > 0 → use driver estimate, set total_source = "driver_estimate"
6. If billing_total > 0:
   - billable_amount_cents = (billing_total * platform_fee_bps) // 10000
   - status = "completed"
   - Create BillingEvent row
7. Else (no total available):
   - status = "completed_unbillable"
   - No BillingEvent created
8. completed_at = now
9. Commit
10. PostHog: `ev_arrival.merchant_confirmed` + `ev_arrival.completed`

**Billing Calculation Example:**
- Order total: $28.47 (2847 cents)
- Fee: 500 bps (5%)
- Billable: (2847 * 500) // 10000 = 142 cents ($1.42)

---

### Endpoint 5: POST /v1/arrival/{session_id}/feedback

**Auth:** Required
**Status Code:** 200

**Request:** `{ rating: "up"|"down", reason?: string, comment?: string (max 200) }`
**Response:** `{ ok: true }`

Only allowed on completed or completed_unbillable sessions.

---

### Endpoint 6: GET /v1/arrival/active

**Auth:** Required
**Status Code:** 200

**Response:** `{ session: SessionResponse | null }`

Checks expiry on read — if session past expires_at, transitions to "expired" and returns null.

---

### Endpoint 7: POST /v1/arrival/{session_id}/cancel

**Auth:** Required
**Status Code:** 200

**Response:** `{ ok: true, status: "canceled" }`

Rejects if already in terminal status. Sets status = "canceled", completed_at = now.

---

### SMS Reply Flow (Twilio Webhook)

**File:** `backend/app/routers/twilio_sms_webhook.py`
**Endpoint:** POST /v1/webhooks/twilio-arrival-sms

Twilio sends form-encoded POST with `Body` and `From` fields.

**Parsing Logic:**
- Body is `.strip().upper()`
- `DONE {code}` → Look up ArrivalSession by merchant_reply_code, run same billing logic as merchant-confirm
- `HELP` → Reply with dashboard URL
- `CANCEL` → Reply with instructions (no actual cancellation)
- Anything else → Reply with usage instructions

**TwiML Response Format:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>Order #1234 marked as delivered. Thank you!</Message>
</Response>
```

**Reply code matching query:**
```python
ArrivalSession.filter(
    merchant_reply_code == code,
    status.in_(("arrived", "merchant_notified"))
)
```

---

### Charge Context (Nearby Discovery)

**File:** `backend/app/routers/charge_context.py`
**Endpoint:** GET /v1/charge-context/nearby?lat=X&lng=Y&accuracy_m=Z&category=C

**Auth:** Optional
**Returns:** Nearest charger + list of nearby merchants sorted by distance

**Response Shape:**
```python
class NearbyResponse:
    charger: Optional[NearbyCharger]  # { charger_id, name, network, lat, lng, distance_m, open_stalls }
    merchants: List[NearbyMerchant]   # { merchant_id, name, category, lat, lng, address, photo_url, rating, walk_minutes, distance_m, ordering_url, verified_visit_count, active_arrival_count }
    total: int
```

**Performance note:** Currently loads ALL chargers and merchants, filters in Python. Works at pilot scale. Needs spatial index for production scale.

---

## 8. Merchant Onboarding Funnel — End-to-End

### Phase 1: Search + Preview (no auth required)

**File:** `backend/app/routers/merchant_funnel.py`
**Prefix:** `/v1/merchant/funnel`

#### GET /search?q=...&lat=...&lng=...
- Wraps Google Places text search
- Returns max 10 results with place_id, name, address, lat, lng, rating, photo_url, types
- Analytics: captures search event with result count

#### POST /resolve
- Request: `{ place_id, name, lat, lng }`
- Idempotent: checks Merchant.place_id first
- If new: creates Merchant with id `m_{uuid.hex[:12]}`, calls `enrich_from_google_places()`
- Signs preview URL: HMAC-SHA256 over `{merchant_id}:{expires_at}` with 7-day TTL
- Response: `{ merchant_id, preview_url, sig, expires_at }`

#### GET /preview?merchant_id=X&exp=Y&sig=Z
- Validates HMAC signature → **403** if invalid or expired
- Returns merchant data + nearest charger info + verified visit count
- No sensitive data exposed (no phone, email, owner info)

#### POST /text-preview-link
- Request: `{ phone, preview_url, merchant_name }`
- Sends SMS via Twilio: "See how {name} appears to EV drivers on Nerava: {url}"

**HMAC Implementation:**
```python
PREVIEW_TTL_DAYS = 7

def sign_preview(merchant_id: str, expires_at: int) -> str:
    key = settings.PREVIEW_SIGNING_KEY or settings.JWT_SECRET
    message = f"{merchant_id}:{expires_at}"
    return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()

def verify_signature(merchant_id: str, expires_at: int, sig: str) -> bool:
    if int(time.time()) > expires_at:
        return False
    expected = sign_preview(merchant_id, expires_at)
    return hmac.compare_digest(expected, sig)
```

### Phase 2: Claim Flow (phone + email verification)

**File:** `backend/app/routers/merchant_claim.py`
**Prefix:** `/v1/merchant/claim`

#### Step 1: POST /start
- Request: `{ merchant_id, email, phone, business_name }`
- Validates merchant exists and not already claimed
- Creates or updates ClaimSession
- Sends OTP to phone via Twilio
- Response: `{ session_id, message }`

#### Step 2: POST /verify-phone
- Request: `{ session_id, code }`
- Verifies 6-digit OTP via OTPServiceV2
- Sets claim_session.phone_verified = True
- Response: `{ phone_verified: true, message }`

#### Step 3: POST /send-magic-link
- Request: `{ session_id }`
- Requires phone_verified = True
- Generates `secrets.token_urlsafe(32)` token with 15-minute expiry
- Sends email with magic link to `{merchant_portal_url}/claim/verify?token={token}`
- Response: `{ email_sent: true, message }`

#### Step 4: GET /verify-magic-link?token=...
- Validates token exists, not expired, phone was verified
- Creates User if doesn't exist (role_flags="merchant_admin")
- Sets merchant.owner_user_id = user.id
- Generates JWT access_token with role="merchant"
- Response: `{ access_token, token_type, user, merchant_id }`

### Frontend Components

**FindBusiness.tsx** — Search input with 300ms debounce, skeleton loaders, result cards
**MerchantPreview.tsx** — HMAC-validated preview page with Loom modal, 3 CTAs (Claim, Schedule, Text)
**ClaimBusiness.tsx** — 4-step wizard with form → OTP → email link → success

---

## 9. Authentication System

### Driver Auth: Phone OTP

**Flow:**
1. Driver enters phone number
2. `POST /v1/auth/otp/start` → sends 6-digit code via Twilio Verify
3. Driver enters code
4. `POST /v1/auth/otp/verify` → returns JWT access_token + refresh_token

**OTP Service (`backend/app/services/otp_service_v2.py`):**
- `send_otp(db, phone, request_id, ip, user_agent)`:
  - Normalizes phone to E.164
  - Checks rate limit (per phone + per IP)
  - Records attempt
  - Calls Twilio Verify `verification_checks.create()`
  - Returns boolean
- `verify_otp(db, phone, code, request_id, ip, user_agent)`:
  - Checks rate limit
  - Calls Twilio Verify
  - Records attempt (success/failure)
  - Returns normalized phone on success
  - Raises 401 on invalid code, 429 on rate limit

**Rate Limiting:** Per-phone and per-IP limits. Lockout after N failed attempts.

### Merchant Auth: Google SSO or Magic Link

**Google SSO:** `POST /v1/auth/merchant/google`
- Verifies Google ID token
- Optionally checks Google Business Profile ownership (GOOGLE_GBP_REQUIRED setting)
- Creates/finds User with auth_provider="google", role_flags="merchant_admin"

**Magic Link:** Part of claim flow (see Section 8)

### JWT Structure

```python
payload = {
    "sub": str(user.public_id),  # UUID
    "auth_provider": "phone",     # or "google", "local"
    "role": "driver",             # or "merchant", "admin"
    "exp": datetime + timedelta(minutes=60),
    "iat": datetime.utcnow(),
}
# Encoded with HS256 using settings.SECRET_KEY
```

**Token Refresh:** POST /auth/refresh with refresh_token → new access_token + refresh_token

### Auth Dependencies

```python
# Require authenticated driver
driver: User = Depends(get_current_driver)

# Optional auth (returns None if not authenticated)
driver: Optional[User] = Depends(get_current_driver_optional)

# Require specific role
role: str = Depends(require_role("admin"))
```

---

## 10. Notification System

**File:** `backend/app/services/notification_service.py`

### SMS via Twilio

Uses `ThreadPoolExecutor(max_workers=2)` because Twilio's Python client is synchronous.

**SMS Template (exact):**
```
NERAVA EV ARRIVAL {emoji}

Order #{order_number}
Type: {type_label}
Vehicle: {vehicle_desc}
Status: On-site now

Driver is {charger_info}.

Reply DONE {merchant_reply_code} when delivered.
Reply HELP for support.
```

Where:
- emoji = "🚗" for ev_curbside, "🍽️" for ev_dine_in
- type_label = "EV Curbside" or "EV Dine-In"
- vehicle_desc = "{color} {model}" or "Unknown vehicle"
- charger_info = "charging at {charger_name}" or "charging nearby"
- merchant_reply_code = 4-digit code from session

**Function Signatures:**
```python
async def send_arrival_sms(to_phone, order_number, arrival_type, vehicle_color, vehicle_model, charger_name, merchant_reply_code) -> bool

async def send_arrival_email(...) -> bool  # Placeholder, returns False

async def notify_merchant(notify_sms, notify_email, sms_phone, email_address, order_number, arrival_type, vehicle_color, vehicle_model, charger_name, merchant_name, merchant_reply_code) -> str
# Returns: 'sms', 'email', 'both', or 'none'
```

### Email: Not Implemented
`send_arrival_email()` logs a message and returns False. Email toggle exists in the config but no emails are actually sent.

---

## 11. POS Adapter System

**File:** `backend/app/services/pos_adapter.py`

### POSOrder Dataclass
```python
@dataclass
class POSOrder:
    order_number: str
    status: str       # 'placed', 'ready', 'completed', 'unknown'
    total_cents: int
    customer_name: Optional[str] = None
    items_summary: Optional[str] = None
```

### POSAdapter ABC
```python
class POSAdapter(ABC):
    async def lookup_order(self, order_number: str) -> Optional[POSOrder]
    async def get_order_status(self, order_number: str) -> Optional[str]
    async def get_order_total(self, order_number: str) -> Optional[int]
```

### Implementations

| Adapter | Status | Returns |
|---------|--------|---------|
| ManualPOSAdapter | **Default, always used** | POSOrder(status='unknown', total_cents=0) |
| ToastPOSAdapter | **Stub** (returns None) | Needs Toast partner API access |
| SquarePOSAdapter | **Stub** (returns None) | Not prioritized |

### Factory
```python
def get_pos_adapter(pos_integration: str, credentials=None) -> POSAdapter:
    if pos_integration == "toast" and credentials: return ToastPOSAdapter(...)
    if pos_integration == "square" and credentials: return SquarePOSAdapter(...)
    return ManualPOSAdapter()
```

**Key design:** Every POS failure degrades to ManualPOSAdapter. The system always works without POS integration.

---

## 12. Billing System

### Revenue Calculation

```
billable_amount_cents = (order_total_cents * platform_fee_bps) // 10000
```

Default: `platform_fee_bps = 500` (5%)

### Billing Total Precedence (most important business rule)

1. **POS-verified total** (from Toast/Square API) — highest trust
2. **Merchant-reported total** (from SMS reply or dashboard) — medium trust
3. **Driver estimate** (entered at order binding) — lowest trust
4. **No total available** → session completes as `completed_unbillable`, no BillingEvent created

### BillingEvent Creation

BillingEvent rows are created in two places:
1. `POST /v1/arrival/{id}/merchant-confirm` — merchant confirms via dashboard
2. `POST /v1/webhooks/twilio-arrival-sms` — merchant replies "DONE {code}" to SMS

Both use identical billing logic. Both check the same precedence.

### Revenue Tracking

Currently: BillingEvent rows with status='pending'. No automated invoicing.
Future: Stripe invoicing aggregated per merchant per month.

---

## 13. Analytics System (PostHog)

**File:** `backend/app/services/analytics.py`

### Singleton Pattern
```python
_analytics_client: Optional[AnalyticsClient] = None

def get_analytics_client() -> AnalyticsClient:
    global _analytics_client
    if _analytics_client is None:
        _analytics_client = AnalyticsClient()
    return _analytics_client
```

### Capture Method
```python
def capture(self, event, distinct_id, properties=None,
            request_id=None, user_id=None, merchant_id=None,
            charger_id=None, session_id=None,
            ip=None, user_agent=None,
            lat=None, lng=None, accuracy_m=None):
```

Every capture call enriches properties with:
- `app: "backend"`, `env: settings.ENV`, `source: "api"`
- `ts: datetime.utcnow().isoformat() + "Z"`
- Correlation IDs (request_id, user_id, merchant_id, etc.)
- Geo coordinates when available

### Design Rule
**Analytics calls NEVER crash requests.** Every capture is wrapped in try/except.

---

## 14. Driver App (React)

### Routes (`apps/driver/src/App.tsx`)

```typescript
<BrowserRouter basename={BASE_URL || '/app'}>
  <OnboardingGate>
    <Routes>
      <Route path="/" element={<DriverHome />} />
      <Route path="/driver" element={<DriverHome />} />
      <Route path="/wyc" element={<WhileYouChargeScreen />} />
      <Route path="/pre-charging" element={<PreChargingScreen />} />
      <Route path="/m/:merchantId" element={<MerchantDetailsScreen />} />
    </Routes>
  </OnboardingGate>
</BrowserRouter>
```

### DriverHome.tsx (1122 lines — the main orchestrator)

This is the most complex frontend component. It manages:
- Location detection and polling (every 10s)
- Charger/merchant discovery via `/v1/charge-context/nearby`
- Charging state machine: PRE_CHARGING → CHARGING_ACTIVE → EXCLUSIVE_ACTIVE
- Merchant carousel with filters (amenities: bathrooms, food, wifi, pets)
- Exclusive activation flow
- Multiple modal states (activate, arrival, completion, preferences, account)
- Favorites management
- Browse mode fallback when location is unavailable

**Key hooks used:**
```typescript
useDriverSessionContext()    // location, coordinates, appChargingState, sessionId
useIntentCapture()           // queries chargers/merchants at location
useActivateExclusive()       // React Query mutation
useCompleteExclusive()       // React Query mutation
useActiveExclusive()         // polls every 30s for active exclusive
useLocationCheck(lat, lng)   // polls every 10s for in-charger-radius
useNativeBridge()            // iOS/Android bridge detection
useFavorites()               // favorite merchants from context
```

### EVArrival Components (NOT YET WIRED IN)

5 components exist at `apps/driver/src/components/EVArrival/` but are not imported anywhere:

#### ModeSelector.tsx
- **Props:** `{ mode: ArrivalMode, onChange: (mode) => void }`
- Stateless tab group: "EV Curbside" / "EV Dine-In"
- Fires `DRIVER_EVENTS.EV_ARRIVAL_MODE_CHANGED`

#### VehicleSetup.tsx
- **Props:** `{ onSave: (color, model) => void, onCancel: () => void, isLoading?: boolean }`
- **State:** color (string), model (string), showSuggestions (boolean)
- **Constants:** 8 COLORS, 23 POPULAR_EVS (Tesla, Rivian, Ford, Chevy, Hyundai, Kia, BMW, etc.)
- Full-screen overlay with color dropdown + model autocomplete (max 6 suggestions)
- Fires `DRIVER_EVENTS.EV_ARRIVAL_VEHICLE_SETUP`

#### ConfirmationSheet.tsx
- **Props:** `{ merchantName, merchantId, arrivalMode, vehicleColor?, vehicleModel?, onConfirm, onCancel, onEditVehicle, isLoading? }`
- **State:** verifying (boolean)
- Shows mode badge, vehicle card, confirmation text
- On confirm: shows 1-second "Verifying..." interstitial with pulsing shield icon, then calls onConfirm
- Fires `DRIVER_EVENTS.EV_ARRIVAL_CONFIRMED`

#### ActiveSession.tsx
- **Props:** `{ sessionId, merchantName, arrivalType, orderNumber?, orderSource?, orderTotalCents?, expiresAt, status, merchantNotifiedAt?, orderingUrl?, vehicleColor?, vehicleModel?, onBindOrder, onCancel, isBindingOrder? }`
- **State:** inputOrderNumber, estimateCents, timeLeft (countdown)
- Status banner: green (merchant notified), blue (arrived), amber (waiting)
- If no order: shows ordering link + order # input + estimate input
- Countdown timer updating every second
- Fires `DRIVER_EVENTS.EV_ARRIVAL_ORDER_BOUND`, `EV_ARRIVAL_CANCELED`

#### CompletionScreen.tsx
- **Props:** `{ merchantName, arrivalType, orderNumber?, onSubmitFeedback, onDone }`
- **State:** rating ('up'|'down'|null), reason (string|null), comment (string), submitted (boolean)
- **DOWN_REASONS:** ['wrong_hours', 'too_crowded', 'slow_service', 'other']
- Thumbs up → optional comment (max 140 chars)
- Thumbs down → reason chip selection
- Fires `DRIVER_EVENTS.EV_ARRIVAL_FEEDBACK_SUBMITTED`

### API Client (`apps/driver/src/services/api.ts`)

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

async function fetchAPI<T>(endpoint: string, options?: RequestInit, retryOn401 = true): Promise<T>
```

**401 Handling:** Gets refresh_token → POST /auth/refresh → retry with new token. If refresh fails, clears tokens.

**React Query Hooks:**
- `useIntentCapture(request)` — POST /v1/intent/capture
- `useMerchantDetails(merchantId, sessionId)` — GET /v1/merchants/{id}
- `useActivateExclusive()` — POST /v1/exclusive/activate (mutation)
- `useCompleteExclusive()` — POST /v1/exclusive/complete (mutation)
- `useActiveExclusive()` — GET /v1/exclusive/active (polls every 30s)
- `useLocationCheck(lat, lng)` — GET /v1/drivers/location/check (polls every 10s)

### Native Bridge (`apps/driver/src/hooks/useNativeBridge.ts`)

Detects iOS/Android native shells. When `isNative === true`, uses native bridge for location, geofencing, auth. When `false`, falls back to browser APIs.

**Bridge detection:**
- Env var: `VITE_NATIVE_BRIDGE_ENABLED !== 'false'`
- Runtime: `window.neravaNative` exists

**Exported interface:**
```typescript
{
  isNative: boolean
  sessionState: SessionState | null  // IDLE | NEAR_CHARGER | ANCHORED | SESSION_ACTIVE | IN_TRANSIT | AT_MERCHANT | SESSION_ENDED
  setChargerTarget(chargerId, lat, lng): void
  setAuthToken(token): void
  confirmExclusiveActivated(sessionId, merchantId, lat, lng): void
  confirmVisitVerified(sessionId, verificationCode): void
  endSession(): void
  requestAlwaysLocation(): void
  getLocation(): Promise<NativeLocation>
  getPermissionStatus(): Promise<PermissionStatus>
  getAuthToken(): Promise<AuthTokenResponse | null>
}
```

**Web injection contract (iOS):**
```javascript
window.neravaNative = {
  postMessage(action, payload) { window.webkit.messageHandlers.neravaBridge.postMessage({action, payload}) },
  request(action, payload) { /* returns Promise resolved via neravaNativeCallback */ }
}
```

**Android equivalent:**
```javascript
window.neravaNative = {
  postMessage(action, payload) { AndroidBridge.onMessage(JSON.stringify({action, payload})) },
  // same request pattern
}
```

---

## 15. Merchant Portal (React)

### Routes (`apps/merchant/app/App.tsx`)

```typescript
<BrowserRouter basename={BASE_URL || '/merchant'}>
  <Routes>
    {/* Public funnel pages (no auth) */}
    <Route path="/find" element={<FindBusiness />} />
    <Route path="/preview" element={<MerchantPreview />} />

    {/* Onboarding */}
    <Route path="/claim" element={<ClaimBusiness />} />
    <Route path="/claim/:merchantId" element={<ClaimBusiness />} />
    <Route path="/claim/verify" element={<ClaimVerify />} />

    {/* Dashboard (requires claim) */}
    <Route path="/" element={isClaimed ? <DashboardLayout /> : <Navigate to="/claim" />}>
      <Route index element={<Overview />} />
      <Route path="overview" element={<Overview />} />
      <Route path="exclusives" element={<Exclusives />} />
      <Route path="visits" element={<Visits />} />
      <Route path="ev-arrivals" element={<EVArrivals />} />
      <Route path="billing" element={<Billing />} />
      <Route path="settings" element={<Settings />} />
    </Route>
  </Routes>
</BrowserRouter>
```

### EVArrivals.tsx — Merchant Arrival Dashboard

**State:** sessions[], config, loading, editingConfig, smsPhone, emailAddress, notifySms, notifyEmail

**API Calls:**
- `GET /v1/merchants/{id}/arrivals` — list sessions (most recent 50)
- `GET /v1/merchants/{id}/notification-config` — current config
- `POST /v1/arrival/{id}/merchant-confirm` with `{ confirmed: true }` — mark delivered
- `PUT /v1/merchants/{id}/notification-config` — save settings

**Session Filtering:**
- Active: status in ['arrived', 'merchant_notified', 'awaiting_arrival']
- Completed: status in ['completed', 'completed_unbillable']

**UI Sections:**
1. Active sessions (green badge, vehicle info, "Mark Delivered" button)
2. Completed sessions (top 10, order total)
3. Notification settings form (SMS toggle, phone, email toggle, email address)

---

## 16. Landing Page (Next.js)

**Location:** `apps/landing/`

CTA links centralized in `apps/landing/app/components/v2/ctaLinks.ts`:
```typescript
getDriverCTAHref()     // → https://app.nerava.network?src=landing&cta=driver
getMerchantCTAHref()   // → https://merchant.nerava.network?src=landing&cta=merchant
getMerchantFindHref()  // → https://merchant.nerava.network/find?src=landing&cta=merchant
getChargerOwnerCTAHref() // → form URL or portal URL
```

---

## 17. iOS Native Shell

**Location:** `Nerava/Nerava/`

Swift WKWebView wrapper. Key files:
- `NativeBridge.swift` — Injects `window.neravaNative`, handles 10 bridge actions
- `SessionEngine/SessionState.swift` — 7 states, 13 events
- `SessionEngine/SessionConfig.swift` — Configurable radii, dwell times, timeouts
- `APIClient.swift` — Talks to `/v1/native/session-events` and `/v1/native/pre-session-events`

**Bridge actions:** SET_CHARGER_TARGET, SET_AUTH_TOKEN, EXCLUSIVE_ACTIVATED, VISIT_VERIFIED, END_SESSION, REQUEST_ALWAYS_LOCATION, GET_LOCATION, GET_SESSION_STATE, GET_PERMISSION_STATUS, GET_AUTH_TOKEN

---

## 18. Android Native Shell

**Location:** `mobile/nerava_android/`

Kotlin WebView wrapper matching iOS feature parity. Key files:
- `bridge/NativeBridge.kt` — `@JavascriptInterface` methods
- `bridge/BridgeInjector.kt` — Identical injection script using `AndroidBridge.onMessage()`
- `engine/SessionEngine.kt` — 7-state machine matching iOS
- `location/LocationService.kt` — FusedLocationProviderClient
- `location/GeofenceManager.kt` — GeofencingClient with max 2 regions, FIFO eviction
- `auth/SecureTokenStore.kt` — EncryptedSharedPreferences

**Build variants:** debug (localhost:5173), staging (staging.nerava.network), release (app.nerava.network)

---

## 19. Infrastructure & Deployment

| Component | Hosting | Domain |
|-----------|---------|--------|
| Backend API | AWS App Runner | api.nerava.network |
| Driver App | S3 + CloudFront | app.nerava.network |
| Merchant Portal | S3 + CloudFront | merchant.nerava.network |
| Landing Page | S3 + CloudFront | www.nerava.network |
| Database | AWS RDS PostgreSQL | Private VPC |
| Redis | AWS ElastiCache | For rate limiting (optional) |

**Deploy commands:**
```bash
python scripts/deploy_aws.py --env prod     # Backend
./scripts/deploy-frontend-s3.sh driver prod  # Driver app
./scripts/deploy-frontend-s3.sh merchant prod # Merchant portal
```

---

## 20. Configuration Reference

All configuration in `backend/app/core/config.py`. Key groups:

### Auth & Security
| Variable | Default | Notes |
|----------|---------|-------|
| JWT_SECRET | "dev-secret-change-me" | **Must change in prod** |
| SECRET_KEY | (alias for JWT_SECRET) | |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 | |
| TOKEN_ENCRYPTION_KEY | "" | Fernet key for POS credentials |

### Twilio
| Variable | Default | Notes |
|----------|---------|-------|
| TWILIO_ACCOUNT_SID | "" | |
| TWILIO_AUTH_TOKEN | "" | |
| TWILIO_VERIFY_SERVICE_SID | "" | For OTP |
| OTP_FROM_NUMBER | "" | For SMS notifications |
| OTP_PROVIDER | "stub" | twilio_verify, twilio_sms, stub |

### Google
| Variable | Default | Notes |
|----------|---------|-------|
| GOOGLE_PLACES_API_KEY | "" | |
| GOOGLE_OAUTH_CLIENT_ID | "" | Merchant SSO |
| GOOGLE_GBP_REQUIRED | "true" | Require Google Business Profile |

### Geofencing
| Variable | Default | Notes |
|----------|---------|-------|
| NATIVE_CHARGER_INTENT_RADIUS_M | 400 | |
| NATIVE_CHARGER_ANCHOR_RADIUS_M | 30 | |
| NATIVE_CHARGER_DWELL_SECONDS | 120 | |
| NATIVE_MERCHANT_UNLOCK_RADIUS_M | 40 | |
| NATIVE_GRACE_PERIOD_SECONDS | 900 | |
| NATIVE_HARD_TIMEOUT_SECONDS | 3600 | |
| CHARGER_RADIUS_M | 150 | Web confirmation radius |
| GOOGLE_PLACES_SEARCH_RADIUS_M | 800 | Merchant search |

### Billing
| Variable | Default | Notes |
|----------|---------|-------|
| PLATFORM_FEE_BPS | 1500 | 15% default (overridden per session at 500) |

### Signing
| Variable | Default | Notes |
|----------|---------|-------|
| PREVIEW_SIGNING_KEY | "" | HMAC key for preview URLs |

---

## 21. API Endpoint Catalog

### EV Arrival (`/v1/arrival`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /v1/arrival/create | Driver | Create session |
| PUT | /v1/arrival/{id}/order | Driver | Bind order number |
| POST | /v1/arrival/{id}/confirm-arrival | Driver | Geofence confirm |
| POST | /v1/arrival/{id}/merchant-confirm | None | Merchant marks delivered |
| POST | /v1/arrival/{id}/feedback | Driver | Driver feedback |
| GET | /v1/arrival/active | Driver | Get active session |
| POST | /v1/arrival/{id}/cancel | Driver | Cancel session |

### Charge Context (`/v1/charge-context`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | /v1/charge-context/nearby | Optional | Nearby merchants |

### Merchant Arrivals (`/v1/merchants`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | /v1/merchants/{id}/arrivals | None | List arrivals |
| GET | /v1/merchants/{id}/notification-config | None | Get config |
| PUT | /v1/merchants/{id}/notification-config | None | Update config |

### Merchant Funnel (`/v1/merchant/funnel`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | /v1/merchant/funnel/search | None | Google Places search |
| POST | /v1/merchant/funnel/resolve | None | Create/find merchant |
| GET | /v1/merchant/funnel/preview | None | HMAC-validated preview |
| POST | /v1/merchant/funnel/text-preview-link | None | SMS preview link |

### Merchant Claim (`/v1/merchant/claim`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /v1/merchant/claim/start | None | Start claim |
| POST | /v1/merchant/claim/verify-phone | None | Verify OTP |
| POST | /v1/merchant/claim/send-magic-link | None | Send email link |
| GET | /v1/merchant/claim/verify-magic-link | None | Complete claim |
| GET | /v1/merchant/claim/session/{id} | None | Check status |

### Auth (`/v1/auth`)
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /v1/auth/otp/start | None | Send OTP |
| POST | /v1/auth/otp/verify | None | Verify OTP |
| POST | /v1/auth/magic_link/request | None | Send magic link |
| POST | /v1/auth/magic_link/verify | None | Verify magic link |
| POST | /v1/auth/merchant/google | None | Merchant Google SSO |
| POST | /v1/auth/admin/login | None | Admin email/password |
| POST | /auth/refresh | None | Refresh JWT token |

### Webhooks
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /v1/webhooks/twilio-arrival-sms | None | SMS reply handler |

### Account
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| PUT | /v1/account/vehicle | Driver | Set vehicle info |

---

## 22. State Machine Reference

### Arrival Session States

```
pending_order ──→ awaiting_arrival ──→ arrived ──→ merchant_notified ──→ completed
     │                  │                │              │                     │
     │                  │                │              └─→ completed_unbillable
     ↓                  ↓                ↓              ↓
   expired           expired          expired        expired
     ↓                  ↓                ↓              ↓
   canceled          canceled         canceled       canceled
```

| State | Meaning | Next States |
|-------|---------|-------------|
| pending_order | Session created, waiting for order # | awaiting_arrival, expired, canceled |
| awaiting_arrival | Order bound, waiting for driver to arrive at charger | arrived, expired, canceled |
| arrived | Geofence confirmed driver at charger | merchant_notified, expired, canceled |
| merchant_notified | SMS sent to merchant | completed, completed_unbillable, expired, canceled |
| completed | Merchant confirmed, billing event created | (terminal) |
| completed_unbillable | Completed but no order total available | (terminal) |
| expired | Session past expires_at (2 hours) | (terminal) |
| canceled | Driver or merchant canceled | (terminal) |

### Native Session States (iOS/Android)

```
IDLE → NEAR_CHARGER → ANCHORED → SESSION_ACTIVE → IN_TRANSIT → AT_MERCHANT → SESSION_ENDED
```

| State | Trigger |
|-------|---------|
| IDLE | Default, no activity |
| NEAR_CHARGER | Enter 400m charger intent zone |
| ANCHORED | Dwell 120s within 30m at low speed (<1.5 m/s) |
| SESSION_ACTIVE | Exclusive activated |
| IN_TRANSIT | Left charger area during session |
| AT_MERCHANT | Enter 40m merchant zone |
| SESSION_ENDED | Session completed or grace period expired |

---

## 23. Error Codes & HTTP Status Codes

| Code | Error Key | Endpoint | Meaning |
|------|-----------|----------|---------|
| 400 | — | /order | Cannot bind order in current status |
| 400 | TOO_FAR_FROM_CHARGER | /confirm-arrival | Driver >250m from charger |
| 400 | — | /confirm-arrival | Charger not found |
| 400 | — | /merchant-confirm | Cannot confirm in current status |
| 400 | — | /feedback | Can only feedback on completed sessions |
| 400 | — | /cancel | Session already ended |
| 400 | — | /claim/start | Merchant already claimed |
| 400 | — | /claim/verify-phone | Invalid code / phone mismatch |
| 401 | — | any auth'd | Missing or invalid token |
| 403 | — | /preview | Invalid or expired HMAC signature |
| 403 | — | /auth/merchant/google | Google Business Profile required |
| 404 | — | /create | Merchant not found |
| 404 | — | /order, /confirm, etc. | Session not found or not owned by driver |
| 409 | ACTIVE_SESSION_EXISTS | /create | Driver already has active session |
| 410 | — | /order, /confirm | Session expired |
| 429 | — | /auth/otp/* | Rate limited |

---

## 24. PostHog Event Catalog

### EV Arrival Events
| Event | Trigger | Key Properties |
|-------|---------|----------------|
| ev_arrival.created | Session created | session_id, merchant_id, arrival_type, charger_id |
| ev_arrival.order_bound | Order # entered | session_id, order_number, order_source, order_total_cents |
| ev_arrival.geofence_entered | Arrival confirmed | session_id, charger_id, distance_m |
| ev_arrival.merchant_notified | SMS sent | session_id, notification_method |
| ev_arrival.merchant_confirmed | Merchant confirms | session_id, billable_amount_cents, total_source |
| ev_arrival.completed | Session complete | session_id, status |
| ev_arrival.feedback_submitted | Feedback given | session_id, rating, reason |
| ev_arrival.expired | Session timed out | session_id |
| ev_arrival.canceled | Session canceled | session_id, previous_status |

### Merchant Funnel Events
| Event | Trigger | Key Properties |
|-------|---------|----------------|
| merchant_funnel.resolve | Business resolved | merchant_id, place_id |
| merchant_funnel.preview_view | Preview page loaded | merchant_id, has_charger |
| merchant_funnel.text_link_sent | SMS link sent | merchant_name |

### Charge Context Events
| Event | Trigger | Key Properties |
|-------|---------|----------------|
| charge_context.nearby | Discovery query | lat, lng, charger_id, merchant_count |

### Driver Events (Frontend)
| Event | Trigger |
|-------|---------|
| EV_ARRIVAL_MODE_CHANGED | Mode selector toggled |
| EV_ARRIVAL_VEHICLE_SETUP | Vehicle saved |
| EV_ARRIVAL_CONFIRMED | Arrival confirmed |
| EV_ARRIVAL_ORDER_BOUND | Order # saved |
| EV_ARRIVAL_CANCELED | Session canceled |
| EV_ARRIVAL_FEEDBACK_SUBMITTED | Feedback submitted |

---

## 25. File Index — Where Everything Lives

### To modify the arrival session state machine:
`backend/app/models/arrival_session.py` — VALID_TRANSITIONS, ACTIVE_STATUSES, TERMINAL_STATUSES

### To modify arrival API endpoints:
`backend/app/routers/arrival.py` — All 7 endpoints, request/response schemas

### To modify SMS notification template:
`backend/app/services/notification_service.py` — `send_arrival_sms()` function, line ~69

### To modify billing calculation:
`backend/app/routers/arrival.py` — `merchant-confirm` endpoint billing logic
`backend/app/routers/twilio_sms_webhook.py` — SMS DONE handler billing logic

### To modify the anti-spoofing distance check:
`backend/app/routers/arrival.py` — `CHARGER_RADIUS_M = 250` constant

### To modify geofence radii (native apps):
`backend/app/core/config.py` — `NATIVE_CHARGER_*` and `NATIVE_MERCHANT_*` settings

### To add a new POS adapter:
`backend/app/services/pos_adapter.py` — Extend POSAdapter ABC, add to factory

### To modify merchant discovery query:
`backend/app/routers/charge_context.py` — `nearby` endpoint

### To modify the claim flow:
`backend/app/routers/merchant_claim.py` — 5 endpoints
`apps/merchant/app/components/ClaimBusiness.tsx` — Frontend wizard

### To wire EVArrival into the driver app:
`apps/driver/src/components/DriverHome/DriverHome.tsx` — Main orchestrator (1122 lines)
`apps/driver/src/components/EVArrival/*.tsx` — 5 existing components
`apps/driver/src/App.tsx` — Route registration

### To modify merchant portal arrival dashboard:
`apps/merchant/app/components/EVArrivals.tsx`

### To add new environment variables:
`backend/app/core/config.py` — Settings class
`backend/ENV.example` — Example file

### Database migrations:
`backend/alembic/versions/062_add_ev_arrival_tables.py` — EV Arrival tables

---

## 26. How to Write Cursor Prompts for This Codebase

### Template for Backend Changes

```
You are Cursor. Modify [endpoint/service/model].

File: backend/app/[path]

Context:
- Auth: Depends(get_current_driver) from backend/app/dependencies/auth.py
- DB: Depends(get_db) from backend/app/db.py
- Analytics: get_analytics_client() from backend/app/services/analytics.py
- Follow patterns in backend/app/routers/arrival.py for:
  - Pydantic request/response models
  - Error handling with HTTPException
  - PostHog event capture (never crashes requests)

Changes:
[specific changes]
```

### Template for Frontend Changes

```
You are Cursor. Modify [component].

File: apps/driver/src/components/[path]

Context:
- API client: apps/driver/src/services/api.ts (fetchAPI function)
- Analytics: apps/driver/src/analytics/ (capture function + DRIVER_EVENTS)
- Native bridge: apps/driver/src/hooks/useNativeBridge.ts (isNative detection)
- Styling: Tailwind CSS classes (follow existing patterns)

Changes:
[specific changes]
```

### Template for Test Writing

```
You are Codex. Write tests for [feature].

File: backend/tests/[test_file].py

Context:
- Use fixtures from backend/tests/conftest.py (client, db)
- Import models from backend/app/models/
- Follow patterns in backend/tests/test_arrival_sessions.py

Test cases:
[numbered list with expected behavior]
```

### Key Patterns to Reference

When writing prompts, always tell Cursor which existing file to follow patterns from:
- **Backend endpoints:** Follow `backend/app/routers/arrival.py`
- **Backend services:** Follow `backend/app/services/notification_service.py`
- **Frontend components:** Follow `apps/driver/src/components/EVArrival/ActiveSession.tsx`
- **Tests:** Follow `backend/tests/test_arrival_sessions.py`
- **Merchant portal:** Follow `apps/merchant/app/components/EVArrivals.tsx`

---

*This document is the engineering source of truth for Nerava. Every function signature, database column, API endpoint, state transition, and error code described here is implemented in the codebase as of February 2026.*
