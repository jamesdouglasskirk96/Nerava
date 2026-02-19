# V0 EV Arrival Code Specification

**Date:** 2026-02-07
**Author:** Staff Engineer / Product Architect
**Status:** Implementation Ready
**Timeline:** 2-4 days

---

## One-Page Summary

### What We're Building

An **EV Arrival Code** system that:
1. Verifies a driver is at/near a charger (Tesla browser, phone geofence, or QR scan)
2. Generates a short-lived code (e.g., `NVR-4821`)
3. Texts the code + checkout link to the driver
4. Driver orders via merchant's existing checkout (Toast, Square, Popmenu, etc.)
5. Driver applies code at checkout or shows it at pickup
6. Merchant confirms fulfillment → BillingEvent created

### Why This Architecture

- **No POS integration required** — merchant uses their existing ordering system
- **No Fleet API dependency** — browser + phone + QR are sufficient
- **Car browser for verification only** — no checkout in car
- **Revenue day 1** — billing on merchant confirmation

### Key Constraints

| Constraint | Implementation |
|------------|----------------|
| Code TTL | 15-30 minutes |
| Single-use | `redeemed_at` timestamp, reject if set |
| Identity anchor | Phone OTP (not vehicle) |
| Verification methods | A) Browser geofence, B) Phone geofence, C) QR scan |
| Billing trigger | Merchant confirmation only |

---

## Decision: Extend ArrivalSession vs. New Model

### Recommendation: **Extend ArrivalSession**

**Rationale:**
1. `ArrivalSession` already has 80% of required fields (driver_id, merchant_id, charger_id, expires_at, billing)
2. Existing merchant portal, analytics, and billing infrastructure work with ArrivalSession
3. Adding 4-5 new columns is cleaner than duplicating the model
4. V0 can be a "code-first" mode of ArrivalSession, not a replacement

**New columns to add:**
```python
# EV Arrival Code fields
arrival_code = Column(String(10), unique=True, nullable=True, index=True)
arrival_code_generated_at = Column(DateTime, nullable=True)
arrival_code_redeemed_at = Column(DateTime, nullable=True)
arrival_code_sms_sent_at = Column(DateTime, nullable=True)
verification_method = Column(String(20), nullable=True)  # 'browser_geofence', 'phone_geofence', 'qr_scan'
checkout_url_sent = Column(String(500), nullable=True)  # The URL texted to driver
```

**New status values:**
```python
# Existing: pending_order → awaiting_arrival → arrived → merchant_notified → completed
# New simplified flow:
# verified → code_generated → code_sent → redeemed → merchant_confirmed → completed
```

For V0, we'll add a `flow_type` column to distinguish:
- `flow_type = 'legacy'` — existing ArrivalSession flow
- `flow_type = 'arrival_code'` — new V0 code-first flow

---

## Section A: Canonical User Flows

### Driver Flow: In-Car Verification → Code → Checkout → Pickup

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Driver at Charger                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Driver plugs in at Tesla Supercharger                                  │
│  Opens Nerava in Tesla browser: app.nerava.network                      │
│                                                                         │
│  ┌─────────────────────────────────────────┐                            │
│  │  ⚡ You're at Canyon Ridge Supercharger │                            │
│  │                                         │                            │
│  │  Get your EV Arrival Code to unlock     │                            │
│  │  priority service at nearby restaurants │                            │
│  │                                         │                            │
│  │  [Get My Code →]                        │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Identity Check (if not logged in)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  IF driver is logged in → Skip to Step 3                                │
│                                                                         │
│  IF not logged in → Show QR pairing:                                    │
│                                                                         │
│  ┌─────────────────────────────────────────┐                            │
│  │  📱 Scan to verify your phone           │                            │
│  │                                         │                            │
│  │       ┌─────────────────────┐           │                            │
│  │       │     [QR CODE]       │           │                            │
│  │       │                     │           │                            │
│  │       └─────────────────────┘           │                            │
│  │                                         │                            │
│  │  Scan with your phone camera            │                            │
│  │  One-time setup (30 seconds)            │                            │
│  │                                         │                            │
│  │  Waiting for verification...            │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                         │
│  Phone opens: app.nerava.network/pair?token=XXX                         │
│  Phone: Enter phone number → OTP → Verified                             │
│  Car browser: Polling detects pairing → Proceeds                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Verification (any ONE method is sufficient)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  METHOD A: Browser Geofence (automatic for Tesla browser)               │
│  - Browser requests geolocation                                         │
│  - Backend verifies location is within 250m of charger                  │
│  - ✓ Verified                                                           │
│                                                                         │
│  METHOD B: Phone Geofence (if phone app is available)                   │
│  - Phone location within 250m of charger                                │
│  - + Dwell time > 30 seconds                                            │
│  - ✓ Verified                                                           │
│                                                                         │
│  METHOD C: QR Scan at Charger                                           │
│  - Physical QR code on charger (charger_id + nonce encoded)             │
│  - Driver scans with phone                                              │
│  - Backend validates charger_id matches claimed location                │
│  - ✓ Verified                                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Code Generation + SMS                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Backend generates code: NVR-4821                                       │
│  Backend sends SMS:                                                     │
│                                                                         │
│  ┌─────────────────────────────────────────┐                            │
│  │ Nerava: Your EV Arrival Code is         │                            │
│  │ NVR-4821                                │                            │
│  │                                         │                            │
│  │ Order here: https://order.asadas.com    │                            │
│  │ Enter code at checkout for priority     │                            │
│  │ service.                                │                            │
│  │                                         │                            │
│  │ Valid for 30 min.                       │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                         │
│  Car browser shows:                                                     │
│                                                                         │
│  ┌─────────────────────────────────────────┐                            │
│  │  ✓ Your EV Arrival Code                 │                            │
│  │                                         │                            │
│  │        ┌───────────────────┐            │                            │
│  │        │    NVR-4821       │            │                            │
│  │        └───────────────────┘            │                            │
│  │                                         │                            │
│  │  📱 Text sent to (512) 555-1234         │                            │
│  │                                         │                            │
│  │  Enter this code at checkout to unlock  │                            │
│  │  priority service at:                   │                            │
│  │                                         │                            │
│  │  • Asadas Grill (3 min walk)            │                            │
│  │  • Epoch Coffee (5 min walk)            │                            │
│  │  • True Texas BBQ (4 min walk)          │                            │
│  │                                         │                            │
│  │  Code expires in 30 minutes             │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Driver Orders on Phone                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Driver taps link in SMS → Opens merchant's ordering page               │
│  (Toast, Square, Popmenu, or any web ordering)                          │
│                                                                         │
│  At checkout:                                                           │
│  - If merchant supports promo codes: Driver enters NVR-4821             │
│  - If not: Driver shows code at pickup                                  │
│                                                                         │
│  Driver completes payment on merchant's platform                        │
│  (We do NOT handle payment)                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Pickup + Merchant Confirmation                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Driver picks up order                                                  │
│  Shows code if needed: "I'm the EV Arrival — code NVR-4821"             │
│                                                                         │
│  Merchant confirms via:                                                 │
│  - SMS reply: "DONE 4821" or "DONE 4821 $45"                            │
│  - OR Merchant portal: Click "Mark Delivered"                           │
│                                                                         │
│  On confirmation:                                                       │
│  - Session marked complete                                              │
│  - BillingEvent created (if total is known)                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Merchant Flow: Onboarding → Configure → Confirm

```
┌─────────────────────────────────────────────────────────────────────────┐
│ MERCHANT ONBOARDING (One-time setup)                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Merchant signs up at merchant.nerava.network                        │
│  2. Claims their business (Google Places lookup)                        │
│  3. Configures:                                                         │
│     - Ordering URL (Toast, Square, Popmenu, or custom)                  │
│     - SMS notification phone                                            │
│     - Optional: Discount amount for EV arrivals                         │
│     - Optional: Charging credit amount                                  │
│                                                                         │
│  ┌─────────────────────────────────────────┐                            │
│  │ EV Arrival Settings                      │                            │
│  ├─────────────────────────────────────────┤                            │
│  │                                         │                            │
│  │ Ordering URL                            │                            │
│  │ [https://order.asadas.com____________]  │                            │
│  │                                         │                            │
│  │ Notification Phone                      │                            │
│  │ [(512) 555-9876____________________]    │                            │
│  │                                         │                            │
│  │ EV Arrival Benefit (optional)           │                            │
│  │ ○ None                                  │                            │
│  │ ● 10% discount                          │                            │
│  │ ○ $5 off                                │                            │
│  │ ○ Free item: [________________]         │                            │
│  │                                         │                            │
│  │ [Save Settings]                         │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ MERCHANT RECEIVES NOTIFICATION                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SMS to merchant:                                                       │
│                                                                         │
│  ┌─────────────────────────────────────────┐                            │
│  │ Nerava: EV Arrival incoming!            │                            │
│  │                                         │                            │
│  │ Code: NVR-4821                          │                            │
│  │ Vehicle: White Model Y                  │                            │
│  │ Charger: Canyon Ridge Supercharger      │                            │
│  │                                         │                            │
│  │ Reply DONE 4821 when fulfilled          │                            │
│  │ or DONE 4821 $45.00 with order total    │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ MERCHANT CONFIRMS FULFILLMENT                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Option A: SMS Reply                                                    │
│  Merchant replies: "DONE 4821 $45"                                      │
│                                                                         │
│  Option B: Merchant Portal                                              │
│  ┌─────────────────────────────────────────┐                            │
│  │ EV Arrivals                             │                            │
│  ├─────────────────────────────────────────┤                            │
│  │                                         │                            │
│  │ NVR-4821 • White Model Y • 2:34 PM      │                            │
│  │ Canyon Ridge Supercharger               │                            │
│  │                                         │                            │
│  │ Order Total: [$45.00________]           │                            │
│  │                                         │                            │
│  │ [Mark Delivered ✓]                      │                            │
│  │                                         │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                         │
│  On confirmation:                                                       │
│  - BillingEvent created with 5% platform fee                            │
│  - Session marked completed                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Section B: Data Model Changes

### B.1 ArrivalSession Extensions

**File:** `backend/app/models/arrival_session.py`

Add these columns:

```python
# EV Arrival Code fields (V0)
flow_type = Column(String(20), nullable=False, default='legacy')
# 'legacy' = existing flow, 'arrival_code' = V0 code-first

arrival_code = Column(String(10), unique=True, nullable=True, index=True)
# Format: NVR-XXXX (4 alphanumeric chars)

arrival_code_generated_at = Column(DateTime, nullable=True)
arrival_code_expires_at = Column(DateTime, nullable=True)  # Separate from session expires_at
arrival_code_redeemed_at = Column(DateTime, nullable=True)
arrival_code_redemption_count = Column(Integer, default=0)

verification_method = Column(String(20), nullable=True)
# 'browser_geofence', 'phone_geofence', 'qr_scan', 'manual'

checkout_url_sent = Column(String(500), nullable=True)
sms_sent_at = Column(DateTime, nullable=True)
sms_message_sid = Column(String(50), nullable=True)  # Twilio message SID

# QR pairing fields
pairing_token = Column(String(64), unique=True, nullable=True, index=True)
pairing_token_expires_at = Column(DateTime, nullable=True)
paired_at = Column(DateTime, nullable=True)
paired_phone = Column(String(20), nullable=True)  # Masked: (512) ***-1234
```

### B.2 Migration

**File:** `backend/alembic/versions/066_add_arrival_code_fields.py`

```python
"""Add EV Arrival Code fields to arrival_sessions

Revision ID: 066
Revises: 065
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa

revision = '066'
down_revision = '065'

def upgrade():
    # Add arrival code columns
    op.add_column('arrival_sessions', sa.Column('flow_type', sa.String(20), nullable=False, server_default='legacy'))
    op.add_column('arrival_sessions', sa.Column('arrival_code', sa.String(10), nullable=True))
    op.add_column('arrival_sessions', sa.Column('arrival_code_generated_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('arrival_code_expires_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('arrival_code_redeemed_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('arrival_code_redemption_count', sa.Integer(), server_default='0'))
    op.add_column('arrival_sessions', sa.Column('verification_method', sa.String(20), nullable=True))
    op.add_column('arrival_sessions', sa.Column('checkout_url_sent', sa.String(500), nullable=True))
    op.add_column('arrival_sessions', sa.Column('sms_sent_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('sms_message_sid', sa.String(50), nullable=True))
    op.add_column('arrival_sessions', sa.Column('pairing_token', sa.String(64), nullable=True))
    op.add_column('arrival_sessions', sa.Column('pairing_token_expires_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('paired_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('paired_phone', sa.String(20), nullable=True))

    # Create indexes
    op.create_index('idx_arrival_code', 'arrival_sessions', ['arrival_code'], unique=True)
    op.create_index('idx_pairing_token', 'arrival_sessions', ['pairing_token'], unique=True)

def downgrade():
    op.drop_index('idx_pairing_token', table_name='arrival_sessions')
    op.drop_index('idx_arrival_code', table_name='arrival_sessions')
    op.drop_column('arrival_sessions', 'paired_phone')
    op.drop_column('arrival_sessions', 'paired_at')
    op.drop_column('arrival_sessions', 'pairing_token_expires_at')
    op.drop_column('arrival_sessions', 'pairing_token')
    op.drop_column('arrival_sessions', 'sms_message_sid')
    op.drop_column('arrival_sessions', 'sms_sent_at')
    op.drop_column('arrival_sessions', 'checkout_url_sent')
    op.drop_column('arrival_sessions', 'verification_method')
    op.drop_column('arrival_sessions', 'arrival_code_redemption_count')
    op.drop_column('arrival_sessions', 'arrival_code_redeemed_at')
    op.drop_column('arrival_sessions', 'arrival_code_expires_at')
    op.drop_column('arrival_sessions', 'arrival_code_generated_at')
    op.drop_column('arrival_sessions', 'arrival_code')
    op.drop_column('arrival_sessions', 'flow_type')
```

### B.3 Merchant Model Extension

**File:** `backend/app/models/while_you_charge.py` (Merchant model)

Add if not exists:

```python
# EV Arrival benefit configuration
ev_arrival_benefit_type = Column(String(20), nullable=True)
# 'none', 'percent_discount', 'fixed_discount', 'free_item', 'charging_credit'

ev_arrival_benefit_value = Column(Integer, nullable=True)
# For percent: 10 = 10%, For fixed: 500 = $5.00, For charging_credit: cents

ev_arrival_benefit_description = Column(String(200), nullable=True)
# Human-readable: "10% off your order" or "Free chips & salsa"
```

---

## Section C: API Contract

### C.1 Checkin Router

**File:** `backend/app/routers/checkin.py`

```python
"""
EV Arrival Code Checkin Router — /v1/checkin/*

V0 implementation of the EV Arrival Code flow.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timedelta

router = APIRouter(prefix="/v1/checkin", tags=["checkin"])

# ─── Constants ────────────────────────────────────────────────────────
CODE_TTL_MINUTES = 30
PAIRING_TTL_MINUTES = 5
CHARGER_RADIUS_M = 250

# ─── Request/Response Models ──────────────────────────────────────────

class StartCheckinRequest(BaseModel):
    """Start a checkin session from car browser."""
    charger_id: Optional[str] = None
    lat: float
    lng: float
    accuracy_m: Optional[float] = None
    idempotency_key: Optional[str] = None


class StartCheckinResponse(BaseModel):
    session_id: str
    status: str  # 'pending_verification', 'needs_pairing', 'verified'
    pairing_required: bool
    pairing_qr_url: Optional[str] = None  # QR code image URL
    pairing_url: Optional[str] = None     # URL encoded in QR
    pairing_token: Optional[str] = None   # Token for polling
    charger_name: Optional[str] = None
    nearby_merchants: list[dict] = []


class VerifyCheckinRequest(BaseModel):
    """Verify arrival using one of three methods."""
    session_id: str
    method: Literal['browser_geofence', 'phone_geofence', 'qr_scan']

    # For browser_geofence and phone_geofence:
    lat: Optional[float] = None
    lng: Optional[float] = None
    accuracy_m: Optional[float] = None

    # For qr_scan:
    qr_payload: Optional[str] = None  # Encoded charger_id + nonce


class VerifyCheckinResponse(BaseModel):
    verified: bool
    verification_method: str
    error: Optional[str] = None


class GenerateCodeRequest(BaseModel):
    """Generate arrival code after verification."""
    session_id: str
    merchant_id: Optional[str] = None  # If driver selected a merchant


class GenerateCodeResponse(BaseModel):
    code: str  # e.g., "NVR-4821"
    expires_at: str  # ISO timestamp
    expires_in_minutes: int
    sms_sent: bool
    sms_phone_masked: str  # "(512) ***-1234"
    checkout_url: Optional[str] = None
    merchant_name: Optional[str] = None
    nearby_merchants: list[dict] = []  # If no merchant selected


class SessionStatusResponse(BaseModel):
    """Poll for session status."""
    session_id: str
    status: str
    # Possible values:
    # 'pending_pairing' - waiting for phone to complete OTP
    # 'pending_verification' - paired but not verified
    # 'verified' - verified, ready for code generation
    # 'code_generated' - code generated, waiting for redemption
    # 'redeemed' - code was used
    # 'merchant_confirmed' - fulfillment confirmed
    # 'completed' - session complete
    # 'expired' - session or code expired

    paired: bool
    verified: bool
    code: Optional[str] = None
    code_expires_at: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None


class RedeemCodeRequest(BaseModel):
    """Log code redemption (optional callback from checkout)."""
    code: str
    order_number: Optional[str] = None
    order_total_cents: Optional[int] = None


class RedeemCodeResponse(BaseModel):
    redeemed: bool
    session_id: str
    already_redeemed: bool


class MerchantConfirmRequest(BaseModel):
    """Merchant confirms fulfillment."""
    code: str  # Can confirm by code
    # OR
    session_id: Optional[str] = None  # Or by session_id

    order_total_cents: Optional[int] = None
    confirmed: bool = True


class MerchantConfirmResponse(BaseModel):
    confirmed: bool
    session_id: str
    billable_amount_cents: Optional[int] = None
    billing_event_id: Optional[str] = None


class PairSessionRequest(BaseModel):
    """Complete pairing from phone."""
    pairing_token: str
    phone: str  # Phone number for OTP


class PairSessionResponse(BaseModel):
    paired: bool
    session_id: str
    otp_sent: bool


class ConfirmPairingRequest(BaseModel):
    """Confirm OTP and complete pairing."""
    pairing_token: str
    otp_code: str


class ConfirmPairingResponse(BaseModel):
    confirmed: bool
    session_id: str
    access_token: str  # JWT for subsequent requests


# ─── Endpoints ────────────────────────────────────────────────────────

@router.post("/start", response_model=StartCheckinResponse, status_code=201)
async def start_checkin(req: StartCheckinRequest, request: Request):
    """
    Start a checkin session from car browser.

    Returns:
    - If user is logged in: session ready for verification
    - If not logged in: pairing_required=True with QR code

    Idempotent via idempotency_key.
    """
    pass


@router.post("/verify", response_model=VerifyCheckinResponse)
async def verify_checkin(req: VerifyCheckinRequest):
    """
    Verify arrival using one of three methods:

    A) browser_geofence: Browser location within 250m of charger
    B) phone_geofence: Phone location + 30s dwell within 250m
    C) qr_scan: QR code at charger scanned (charger_id + nonce)

    Only ONE method needs to succeed.

    Rate limited: 10 attempts per session.
    """
    pass


@router.post("/generate-code", response_model=GenerateCodeResponse)
async def generate_code(req: GenerateCodeRequest):
    """
    Generate EV Arrival Code after verification.

    - Code format: NVR-XXXX (4 alphanumeric chars)
    - TTL: 30 minutes
    - Single-use
    - Sends SMS with code + checkout URL

    Idempotent: returns existing code if already generated for session.
    """
    pass


@router.get("/session/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Poll for session status.

    Used by car browser to detect:
    - Pairing complete (phone finished OTP)
    - Verification complete
    - Code redemption
    - Merchant confirmation
    """
    pass


@router.post("/redeem", response_model=RedeemCodeResponse)
async def redeem_code(req: RedeemCodeRequest):
    """
    Log code redemption.

    Called by:
    - Merchant checkout callback (if integrated)
    - Driver app when applying code

    Marks code as redeemed (prevents re-use).

    Note: V0 may not have checkout callbacks, so this is optional.
    Merchant confirmation is the billing trigger, not redemption.
    """
    pass


@router.post("/merchant-confirm", response_model=MerchantConfirmResponse)
async def merchant_confirm(req: MerchantConfirmRequest):
    """
    Merchant confirms fulfillment.

    Creates BillingEvent if order_total_cents is provided.

    Can be called via:
    - Merchant portal
    - SMS reply webhook (parsed by twilio_sms_webhook router)

    Idempotent: second call returns existing confirmation.
    """
    pass


# ─── Pairing Endpoints ────────────────────────────────────────────────

@router.post("/pair", response_model=PairSessionResponse)
async def pair_session(req: PairSessionRequest):
    """
    Start pairing from phone.

    Called when user scans QR code on phone.
    Sends OTP to provided phone number.

    Rate limited: 3 OTP requests per phone per hour.
    """
    pass


@router.post("/pair/confirm", response_model=ConfirmPairingResponse)
async def confirm_pairing(req: ConfirmPairingRequest):
    """
    Confirm OTP and complete pairing.

    Returns JWT access token for subsequent requests.
    Car browser polling will detect pairing is complete.
    """
    pass
```

### C.2 Error Codes

```python
# Error responses follow this format:
{
    "error": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}  # Optional additional context
}

# Error codes:
"SESSION_NOT_FOUND"         # 404
"SESSION_EXPIRED"           # 410
"CODE_EXPIRED"              # 410
"CODE_ALREADY_REDEEMED"     # 409
"VERIFICATION_FAILED"       # 400
"TOO_FAR_FROM_CHARGER"      # 400
"INVALID_QR_CODE"           # 400
"PAIRING_REQUIRED"          # 401
"PAIRING_EXPIRED"           # 410
"RATE_LIMIT_EXCEEDED"       # 429
"OTP_INVALID"               # 400
"OTP_EXPIRED"               # 410
```

---

## Section D: Frontend Implementation Plan

### D.1 File Structure

```
apps/driver/src/
├── components/
│   └── Checkin/
│       ├── CheckinEntry.tsx        # Entry point: "Get My Code" button
│       ├── PairingQRScreen.tsx     # QR code display for pairing
│       ├── VerificationScreen.tsx  # Verification in progress
│       ├── CodeDisplayScreen.tsx   # Shows code + merchant options
│       ├── CodeSuccessScreen.tsx   # Confirmation after SMS sent
│       └── hooks/
│           ├── useCheckinSession.ts    # Session state management
│           ├── useSessionPolling.ts    # Poll /session/{id}
│           └── useGeolocation.ts       # Browser geolocation
├── pages/
│   └── pair.tsx                    # /pair?token=XXX (phone landing)
```

### D.2 Component Specifications

#### CheckinEntry.tsx
```
┌─────────────────────────────────────────┐
│  ⚡ You're at [Charger Name]            │
│                                         │
│  Get your EV Arrival Code to unlock     │
│  priority service at nearby restaurants │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │        [Get My Code →]          │    │
│  │        (big touch target)       │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Nearby:                                │
│  • Asadas Grill (3 min)                 │
│  • Epoch Coffee (5 min)                 │
└─────────────────────────────────────────┘

Touch target: 64px height minimum
Font: 18px+ for car readability
```

#### PairingQRScreen.tsx
```
┌─────────────────────────────────────────┐
│  📱 Scan to verify                      │
│                                         │
│      ┌─────────────────────┐            │
│      │                     │            │
│      │     [QR CODE]       │            │
│      │     256x256px       │            │
│      │                     │            │
│      └─────────────────────┘            │
│                                         │
│  Scan with your phone camera            │
│  One-time setup                         │
│                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━             │
│  Waiting for verification...            │
│  (polling indicator)                    │
│                                         │
│  [Cancel]                               │
└─────────────────────────────────────────┘

Poll: GET /session/{id} every 2 seconds
On paired=true: navigate to VerificationScreen
```

#### CodeDisplayScreen.tsx
```
┌─────────────────────────────────────────┐
│  ✓ Your EV Arrival Code                 │
│                                         │
│      ┌───────────────────────┐          │
│      │                       │          │
│      │      NVR-4821         │          │
│      │      (48px font)      │          │
│      │                       │          │
│      └───────────────────────┘          │
│                                         │
│  📱 Text sent to (512) ***-1234         │
│                                         │
│  ────────────────────────────           │
│                                         │
│  Order from:                            │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ [img] Asadas Grill              │    │
│  │       3 min walk · Mexican      │    │
│  │       [Order Now →]             │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ [img] Epoch Coffee              │    │
│  │       5 min walk · Coffee       │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Code expires in 28:45                  │
└─────────────────────────────────────────┘

Countdown: live timer from code_expires_at
Merchant cards: link to ordering_url
```

### D.3 Phone Pairing Page

**File:** `apps/driver/src/pages/pair.tsx`

Route: `/pair?token=XXX`

```
┌─────────────────────────────────────────┐
│  Nerava                                 │
├─────────────────────────────────────────┤
│                                         │
│  Verify your phone to continue          │
│                                         │
│  Phone Number                           │
│  [(512) 555-1234________________]       │
│                                         │
│  [Send Code →]                          │
│                                         │
└─────────────────────────────────────────┘

After OTP sent:

┌─────────────────────────────────────────┐
│  Nerava                                 │
├─────────────────────────────────────────┤
│                                         │
│  Enter the code sent to                 │
│  (512) 555-1234                         │
│                                         │
│  [____] [____] [____] [____]            │
│                                         │
│  [Verify →]                             │
│                                         │
│  Didn't receive it? [Resend]            │
│                                         │
└─────────────────────────────────────────┘

On success:

┌─────────────────────────────────────────┐
│  Nerava                                 │
├─────────────────────────────────────────┤
│                                         │
│  ✓ Verified!                            │
│                                         │
│  Return to your car screen to           │
│  get your EV Arrival Code.              │
│                                         │
│  You can close this page.               │
│                                         │
└─────────────────────────────────────────┘
```

---

## Section E: Abuse Prevention

### E.1 Rate Limits

| Endpoint | Limit | Window | Key |
|----------|-------|--------|-----|
| `POST /checkin/start` | 10 | 1 hour | IP |
| `POST /checkin/verify` | 10 | per session | session_id |
| `POST /checkin/generate-code` | 3 | per session | session_id |
| `POST /checkin/pair` | 3 | 1 hour | phone |
| `POST /checkin/pair/confirm` | 5 | per pairing | pairing_token |

### E.2 Code Security

```python
def generate_arrival_code() -> str:
    """
    Generate a short, unique, human-readable code.
    Format: NVR-XXXX where X is alphanumeric (no confusing chars)
    """
    # Exclude confusing characters: 0, O, I, L, 1
    alphabet = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
    suffix = ''.join(secrets.choice(alphabet) for _ in range(4))
    return f"NVR-{suffix}"
```

### E.3 Verification Requirements

```python
def verify_browser_geofence(session: ArrivalSession, lat: float, lng: float) -> bool:
    """
    Verify browser location is within charger radius.

    Anti-spoofing measures:
    1. Server-side distance calculation (can't fake on client)
    2. Accuracy threshold (reject if accuracy > 100m)
    3. Session must be from EV browser user-agent
    """
    if not session.charger_id:
        return False

    charger = get_charger(session.charger_id)
    distance = haversine_m(lat, lng, charger.lat, charger.lng)

    return distance <= CHARGER_RADIUS_M
```

### E.4 Single-Use Enforcement

```python
def redeem_code(code: str) -> ArrivalSession:
    """
    Mark code as redeemed.

    Atomic operation to prevent race conditions.
    """
    session = (
        db.query(ArrivalSession)
        .filter(
            ArrivalSession.arrival_code == code,
            ArrivalSession.arrival_code_redeemed_at.is_(None),
            ArrivalSession.arrival_code_expires_at > datetime.utcnow(),
        )
        .with_for_update()  # Row lock
        .first()
    )

    if not session:
        raise CodeNotFoundOrExpired()

    session.arrival_code_redeemed_at = datetime.utcnow()
    session.arrival_code_redemption_count += 1
    db.commit()

    return session
```

### E.5 TTL Expiry Job

```python
# Run every 5 minutes via cron or Celery beat

async def expire_stale_sessions():
    """Expire sessions and codes that have passed TTL."""
    now = datetime.utcnow()

    # Expire sessions
    expired = (
        db.query(ArrivalSession)
        .filter(
            ArrivalSession.expires_at < now,
            ArrivalSession.status.in_(ACTIVE_STATUSES),
        )
        .all()
    )

    for session in expired:
        session.status = 'expired'

    db.commit()
    logger.info(f"Expired {len(expired)} stale sessions")
```

---

## Section F: Revenue Model (V0)

### F.1 Fee Structure

| Fee Type | Default | When Applied |
|----------|---------|--------------|
| Platform fee | 5% (500 bps) | On merchant confirmation with known total |
| Minimum fee | $0.50 | If 5% < $0.50 |
| Maximum fee | $5.00 | If 5% > $5.00 |

### F.2 Billing Event Creation

```python
def create_billing_event(session: ArrivalSession, order_total_cents: int) -> BillingEvent:
    """
    Create billing event on merchant confirmation.

    Only created if:
    1. order_total_cents is provided and > 0
    2. Session is not already billed
    """
    fee_bps = session.platform_fee_bps or 500
    billable_cents = (order_total_cents * fee_bps) // 10000

    # Apply min/max
    billable_cents = max(50, min(500, billable_cents))  # $0.50 - $5.00

    billing_event = BillingEvent(
        arrival_session_id=session.id,
        merchant_id=session.merchant_id,
        order_total_cents=order_total_cents,
        fee_bps=fee_bps,
        billable_cents=billable_cents,
        total_source='merchant_confirmed',
    )

    db.add(billing_event)
    session.billing_status = 'pending'
    db.commit()

    return billing_event
```

### F.3 CSV Export (V0 Invoicing)

```python
# GET /v1/admin/billing/export?start_date=2026-02-01&end_date=2026-02-28

def export_billing_csv(start_date: date, end_date: date) -> str:
    """
    Export billing events to CSV for manual invoicing.

    Columns:
    - billing_event_id
    - merchant_id
    - merchant_name
    - arrival_session_id
    - order_total_cents
    - billable_cents
    - status
    - created_at
    """
    pass
```

---

## Cursor-Ready Implementation Tasks

### Task 1: Database Migration (30 min)

```markdown
# Task: Add EV Arrival Code columns to ArrivalSession

## Context
We're implementing V0 of the EV Arrival Code flow. This requires adding new columns to the existing `arrival_sessions` table.

## Files to modify
- backend/alembic/versions/066_add_arrival_code_fields.py (create)
- backend/app/models/arrival_session.py (add columns)
- backend/app/models/__init__.py (if needed)

## Columns to add
See Section B.1 of V0_EV_ARRIVAL_CODE_SPEC.md

## Acceptance criteria
- [ ] Migration runs without errors
- [ ] Migration is reversible (downgrade works)
- [ ] New columns have proper indexes
- [ ] arrival_code has unique constraint
- [ ] pairing_token has unique constraint

## Commands to test
```bash
cd backend
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```
```

### Task 2: Checkin Router - Start & Pairing (1 hour)

```markdown
# Task: Implement /v1/checkin/start and pairing endpoints

## Context
Implement the session start and QR pairing flow for the EV Arrival Code system.

## Files to create/modify
- backend/app/routers/checkin.py (create)
- backend/app/main.py (register router)
- backend/app/services/checkin_service.py (create)

## Endpoints to implement
1. POST /v1/checkin/start
   - Detect EV browser
   - Find nearest charger
   - Check if user is authenticated
   - If not authenticated: generate pairing token + QR
   - Return session_id + pairing info

2. POST /v1/checkin/pair
   - Accept pairing_token + phone
   - Send OTP via Twilio
   - Return otp_sent=true

3. POST /v1/checkin/pair/confirm
   - Verify OTP
   - Link phone to session
   - Return JWT access token

4. GET /v1/checkin/session/{session_id}
   - Return current session status
   - Used for polling from car browser

## Acceptance criteria
- [ ] Start creates ArrivalSession with flow_type='arrival_code'
- [ ] Pairing token expires in 5 minutes
- [ ] OTP rate limit: 3 per phone per hour
- [ ] Session polling returns paired=true after OTP confirmed
- [ ] Idempotency key prevents duplicate sessions
```

### Task 3: Checkin Router - Verification (45 min)

```markdown
# Task: Implement /v1/checkin/verify endpoint

## Context
Implement the three verification methods for proving driver is at charger.

## Files to modify
- backend/app/routers/checkin.py
- backend/app/services/checkin_service.py

## Endpoint
POST /v1/checkin/verify

## Verification methods
A) browser_geofence
   - lat/lng from request
   - Server-side distance check
   - Must be within 250m of charger
   - Must be from EV browser (user-agent check)

B) phone_geofence
   - lat/lng from request
   - Server-side distance check
   - Must be within 250m of charger
   - (Dwell time check is optional for V0)

C) qr_scan
   - qr_payload contains encoded charger_id + nonce
   - Validate charger_id matches session's charger
   - Validate nonce is fresh (< 5 min old)

## Acceptance criteria
- [ ] Any ONE method succeeding marks session as verified
- [ ] Rate limit: 10 verification attempts per session
- [ ] Proper error codes for each failure mode
- [ ] verification_method is recorded on session
```

### Task 4: Checkin Router - Code Generation (45 min)

```markdown
# Task: Implement /v1/checkin/generate-code endpoint

## Context
Generate the EV Arrival Code and send SMS to driver.

## Files to modify
- backend/app/routers/checkin.py
- backend/app/services/checkin_service.py
- backend/app/services/sms_service.py (if not exists, create)

## Endpoint
POST /v1/checkin/generate-code

## Logic
1. Verify session is in 'verified' status
2. Generate unique code (NVR-XXXX format)
3. Set code_expires_at to now + 30 minutes
4. Build SMS message with code + checkout URL
5. Send SMS via Twilio
6. Record sms_sent_at and sms_message_sid
7. Return code + nearby merchants

## Code generation
- Format: NVR-XXXX
- Alphabet: 23456789ABCDEFGHJKMNPQRSTUVWXYZ (no confusing chars)
- Must be unique in database

## SMS template
```
Nerava: Your EV Arrival Code is {code}

Order here: {checkout_url}
Enter code at checkout for priority service.

Valid for 30 min.
```

## Acceptance criteria
- [ ] Code is unique
- [ ] Code expires in 30 minutes
- [ ] SMS is sent via Twilio
- [ ] Idempotent: returns existing code if already generated
- [ ] checkout_url comes from merchant.ordering_url
```

### Task 5: Checkin Router - Redeem & Confirm (45 min)

```markdown
# Task: Implement redemption and merchant confirmation endpoints

## Files to modify
- backend/app/routers/checkin.py
- backend/app/services/checkin_service.py

## Endpoints

1. POST /v1/checkin/redeem
   - Mark code as redeemed
   - Prevent re-use
   - Atomic operation (row lock)

2. POST /v1/checkin/merchant-confirm
   - Accept code OR session_id
   - Accept order_total_cents
   - Create BillingEvent if total provided
   - Mark session complete

## BillingEvent creation
- Only if order_total_cents > 0
- Apply 5% fee (500 bps)
- Min $0.50, max $5.00

## Acceptance criteria
- [ ] Code can only be redeemed once
- [ ] Expired codes return 410
- [ ] Merchant confirm creates BillingEvent
- [ ] Merchant confirm is idempotent
- [ ] Session status transitions correctly
```

### Task 6: Frontend - Checkin Components (2 hours)

```markdown
# Task: Implement car browser checkin UI

## Files to create
- apps/driver/src/components/Checkin/CheckinEntry.tsx
- apps/driver/src/components/Checkin/PairingQRScreen.tsx
- apps/driver/src/components/Checkin/VerificationScreen.tsx
- apps/driver/src/components/Checkin/CodeDisplayScreen.tsx
- apps/driver/src/components/Checkin/hooks/useCheckinSession.ts
- apps/driver/src/components/Checkin/hooks/useSessionPolling.ts

## Requirements
- Large touch targets (64px+ height)
- Large fonts (18px+)
- Works on Tesla browser (1920x1080 or 1200x1920)
- Polling for pairing status (2 second interval)
- Countdown timer for code expiry

## Flow
1. CheckinEntry: "Get My Code" button
2. If not logged in: PairingQRScreen with QR
3. VerificationScreen: "Verifying location..."
4. CodeDisplayScreen: Show code + merchants

## Acceptance criteria
- [ ] QR code displays correctly
- [ ] Polling detects pairing completion
- [ ] Geolocation request works
- [ ] Code displays prominently
- [ ] Countdown timer works
- [ ] Merchant links work
```

### Task 7: Frontend - Phone Pairing Page (1 hour)

```markdown
# Task: Implement phone pairing page

## Files to create
- apps/driver/src/pages/pair.tsx (or equivalent route)

## Route
/pair?token=XXX

## Flow
1. Extract token from URL
2. Show phone number input
3. Call POST /v1/checkin/pair
4. Show OTP input
5. Call POST /v1/checkin/pair/confirm
6. Show success message

## Requirements
- Mobile-optimized
- Auto-focus OTP fields
- Resend OTP option
- Clear error messages

## Acceptance criteria
- [ ] Token extracted from URL
- [ ] Phone validation
- [ ] OTP input works
- [ ] Success redirects appropriately
- [ ] Error states handled
```

### Task 8: SMS Webhook for Merchant Confirmation (30 min)

```markdown
# Task: Add SMS reply parsing for merchant confirmation

## Files to modify
- backend/app/routers/twilio_sms_webhook.py

## Message formats to parse
- "DONE 4821" -> confirm session with code ending in 4821
- "DONE 4821 $45" -> confirm with order total
- "DONE 4821 45.00" -> confirm with order total

## Logic
1. Parse incoming SMS body
2. Extract code (last 4 chars of NVR-XXXX)
3. Look up session by merchant_reply_code or arrival_code suffix
4. Extract order total if present
5. Call merchant_confirm logic

## Acceptance criteria
- [ ] "DONE XXXX" confirms session
- [ ] "DONE XXXX $XX" confirms with total
- [ ] Invalid code returns helpful SMS reply
- [ ] Already confirmed returns acknowledgment
```

---

## Test Checklist (pytest)

### File: `backend/tests/test_checkin.py`

```python
"""
Tests for EV Arrival Code (V0) flow.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

class TestCheckinStart:
    """Tests for POST /v1/checkin/start"""

    def test_start_creates_session(self, client, mock_charger):
        """Starting checkin creates an ArrivalSession with flow_type='arrival_code'"""
        pass

    def test_start_detects_tesla_browser(self, client, mock_charger):
        """Tesla user-agent is detected and recorded"""
        pass

    def test_start_returns_pairing_qr_if_not_logged_in(self, client, mock_charger):
        """Unauthenticated request returns pairing_required=True with QR"""
        pass

    def test_start_skips_pairing_if_logged_in(self, client, auth_headers, mock_charger):
        """Authenticated request proceeds directly to verification"""
        pass

    def test_start_idempotency(self, client, mock_charger):
        """Same idempotency_key returns same session"""
        pass


class TestCheckinVerify:
    """Tests for POST /v1/checkin/verify"""

    def test_verify_browser_geofence_success(self, client, session_in_progress):
        """Browser geofence within 250m succeeds"""
        pass

    def test_verify_browser_geofence_too_far(self, client, session_in_progress):
        """Browser geofence > 250m fails with TOO_FAR_FROM_CHARGER"""
        pass

    def test_verify_phone_geofence_success(self, client, session_in_progress):
        """Phone geofence within 250m succeeds"""
        pass

    def test_verify_qr_scan_success(self, client, session_in_progress):
        """Valid QR payload succeeds"""
        pass

    def test_verify_qr_scan_invalid_charger(self, client, session_in_progress):
        """QR with wrong charger_id fails"""
        pass

    def test_verify_rate_limit(self, client, session_in_progress):
        """More than 10 attempts returns 429"""
        pass


class TestGenerateCode:
    """Tests for POST /v1/checkin/generate-code"""

    def test_generate_code_format(self, client, verified_session):
        """Code follows NVR-XXXX format"""
        pass

    def test_generate_code_unique(self, client, verified_session):
        """Each code is unique"""
        pass

    def test_generate_code_sends_sms(self, client, verified_session, mock_twilio):
        """SMS is sent with code and checkout URL"""
        pass

    def test_generate_code_idempotent(self, client, verified_session):
        """Second call returns same code"""
        pass

    def test_generate_code_sets_expiry(self, client, verified_session):
        """Code expires in 30 minutes"""
        pass


class TestCodeTTL:
    """Tests for code expiration"""

    def test_expired_code_cannot_be_redeemed(self, client, session_with_expired_code):
        """Expired code returns 410"""
        pass

    def test_session_polling_shows_expired(self, client, session_with_expired_code):
        """Session status shows 'expired' after TTL"""
        pass

    def test_expiry_job_marks_stale_sessions(self, db, old_sessions):
        """Background job expires stale sessions"""
        pass


class TestCodeSingleUse:
    """Tests for single-use enforcement"""

    def test_code_can_be_redeemed_once(self, client, session_with_code):
        """First redemption succeeds"""
        pass

    def test_second_redemption_fails(self, client, redeemed_session):
        """Second redemption returns 409 CODE_ALREADY_REDEEMED"""
        pass

    def test_redemption_is_atomic(self, client, session_with_code):
        """Concurrent redemptions don't create race condition"""
        pass


class TestMerchantConfirm:
    """Tests for POST /v1/checkin/merchant-confirm"""

    def test_confirm_creates_billing_event(self, client, redeemed_session):
        """Confirmation with total creates BillingEvent"""
        pass

    def test_confirm_without_total_no_billing(self, client, redeemed_session):
        """Confirmation without total doesn't create BillingEvent"""
        pass

    def test_confirm_by_code(self, client, redeemed_session):
        """Can confirm by code"""
        pass

    def test_confirm_by_session_id(self, client, redeemed_session):
        """Can confirm by session_id"""
        pass

    def test_confirm_idempotent(self, client, confirmed_session):
        """Second confirm returns existing confirmation"""
        pass

    def test_billing_fee_calculation(self, client, redeemed_session):
        """5% fee is calculated correctly"""
        pass

    def test_billing_min_fee(self, client, redeemed_session_small_order):
        """Minimum fee of $0.50 is applied"""
        pass

    def test_billing_max_fee(self, client, redeemed_session_large_order):
        """Maximum fee of $5.00 is applied"""
        pass


class TestPairing:
    """Tests for QR pairing flow"""

    def test_pairing_token_expires(self, client, session_with_expired_pairing):
        """Expired pairing token returns 410"""
        pass

    def test_otp_rate_limit(self, client):
        """More than 3 OTP requests per hour returns 429"""
        pass

    def test_pairing_links_phone_to_session(self, client, session_with_pairing):
        """Successful pairing links phone and creates user"""
        pass

    def test_car_polling_detects_pairing(self, client, paired_session):
        """Session polling shows paired=True after OTP confirmed"""
        pass


class TestSMSWebhook:
    """Tests for merchant SMS reply parsing"""

    def test_done_command_confirms(self, client, session_with_code):
        """'DONE 4821' confirms session"""
        pass

    def test_done_with_total_creates_billing(self, client, session_with_code):
        """'DONE 4821 $45' confirms with total"""
        pass

    def test_invalid_code_returns_error_sms(self, client, mock_twilio):
        """Invalid code sends error SMS reply"""
        pass
```

---

## Summary

This V0 spec enables:

1. **Zero POS dependency** — merchant uses their existing ordering
2. **Zero Fleet API dependency** — browser + phone + QR are sufficient
3. **Revenue day 1** — billing on merchant confirmation
4. **2-4 day implementation** — scoped to essentials only

### Implementation Order

1. Database migration (30 min)
2. Checkin router: start + pairing (1 hr)
3. Checkin router: verify (45 min)
4. Checkin router: generate-code (45 min)
5. Checkin router: redeem + confirm (45 min)
6. Frontend: car browser UI (2 hrs)
7. Frontend: phone pairing page (1 hr)
8. SMS webhook: merchant reply (30 min)

**Total: ~8 hours of implementation**

### What's NOT in V0

- POS API read/write
- Push notifications
- Native app
- Automated Stripe invoicing
- Fleet Telemetry
- Virtual Key pairing

These are all future optimizations, not prerequisites.
