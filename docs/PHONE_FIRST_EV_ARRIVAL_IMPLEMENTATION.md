# Phone-First EV Arrival Implementation Plan

**Date:** 2026-02-08
**Status:** Implementation in Progress

---

## Overview

Ship Phase 0 EV Arrival that works without Smartcar and without POS access:
1. Driver opens Tesla browser → types `link.nerava.network`
2. Enters phone number → receives SMS with session link + 6-char code
3. Opens link on phone → OTP → shows Check-In Card
4. Verifies location (geofence) → card shows "Verified"
5. Shows code to merchant → merchant redeems in portal

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Tesla Browser                                │
│  link.nerava.network                                                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  "Nerava Check-In"                                          │    │
│  │  [Phone Number Input]                                       │    │
│  │  [Text me my check-in link]                                 │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    POST /v1/checkin/phone-start
                    - Validate Tesla User-Agent
                    - Create ArrivalSession
                    - Generate session_code (6 chars)
                    - Generate signed token
                    - Send SMS
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Driver's Phone                               │
│  SMS: "Nerava Check-In: ABC123"                                      │
│       https://app.nerava.network/s/{token}                           │
│                                    │                                 │
│                                    ▼                                 │
│  app.nerava.network/s/{token}                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  OTP Verification (if not authenticated)                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                    │                                 │
│                                    ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  CHECK-IN CARD                                              │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │  Status: ● VERIFIED                                  │    │    │
│  │  │                                                      │    │    │
│  │  │            ABC123                                    │    │    │
│  │  │         (large code)                                 │    │    │
│  │  │                                                      │    │    │
│  │  │  Near: Tesla Supercharger - Canyon Ridge             │    │    │
│  │  │  Valid until: 2:45 PM                                │    │    │
│  │  │                                                      │    │    │
│  │  │  [Verify I'm Charging]  (if not verified)            │    │    │
│  │  │  [Show Proof]           (if verified)                │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Merchant Portal                              │
│  merchant.nerava.network/arrivals                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Redeem Nerava Code: [______] [Redeem]                      │    │
│  │                                                              │    │
│  │  ✓ ABC123 redeemed - Table 5 - $28.50                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Files to Modify/Create

### Backend

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/checkin_service.py` | MODIFY | Add phone-first flow, 6-char codes, rate limiting |
| `backend/app/routers/checkin.py` | MODIFY | Add `/phone-start` endpoint, browser validation |
| `backend/app/utils/ev_browser.py` | MODIFY | Add `require_ev_browser()` validation |
| `backend/app/utils/rate_limit.py` | CREATE | Phone + IP rate limiting |
| `backend/app/utils/session_token.py` | CREATE | HMAC-signed token generation |

### Frontend - Link App (new)

| File | Action | Description |
|------|--------|-------------|
| `apps/link/` | CREATE | New minimal Vite app for link.nerava.network |
| `apps/link/index.html` | CREATE | Minimal HTML |
| `apps/link/src/main.tsx` | CREATE | Phone input form |
| `apps/link/src/App.tsx` | CREATE | Main component |

### Frontend - Driver App (modify)

| File | Action | Description |
|------|--------|-------------|
| `apps/driver/src/components/CheckInCard/` | CREATE | Check-in card component |
| `apps/driver/src/pages/CheckInSession.tsx` | CREATE | /s/:token route |
| `apps/driver/src/App.tsx` | MODIFY | Add route |

### Frontend - Merchant App (modify)

| File | Action | Description |
|------|--------|-------------|
| `apps/merchant/app/components/RedeemCode.tsx` | CREATE | Code redemption input |
| `apps/merchant/app/components/EVArrivals.tsx` | MODIFY | Add redeem section |

---

## API Endpoints

### New/Modified Endpoints

```
POST /v1/checkin/phone-start
  Body: { phone: string, charger_hint?: string }
  Headers: User-Agent (validated for Tesla/EV browser)
  Response: { ok: bool, session_code: string, expires_in: int }
  Rate limit: 3/day per phone, 10/hour per IP

GET /v1/checkin/session/{token}
  Response: { status, session_code, charger_name?, merchant_name?, verified, expires_at }
  Note: Limited data if not authenticated

POST /v1/checkin/verify
  Auth: Required
  Body: { token: string, lat: float, lng: float, accuracy_m?: float }
  Response: { verified: bool, method: string, error?: string }

POST /v1/checkin/redeem
  Auth: Merchant auth OR staff token
  Body: { session_code: string, order_total_cents?: int }
  Response: { redeemed: bool, session_id: string }
```

---

## Session Code Format

**Old (V0):** `NVR-XXXX` (8 chars with prefix)
**New (Phone-First):** `ABC123` (6 alphanumeric, no prefix)

Alphabet: `23456789ABCDEFGHJKMNPQRSTUVWXYZ` (no confusing chars)

---

## Rate Limiting

| Limit | Value | Scope |
|-------|-------|-------|
| Per phone | 3 sessions/day | Rolling 24h window |
| Per IP | 10 requests/hour | Rolling 1h window |
| Verification attempts | 10/session | Per session lifetime |

---

## Security

1. **Tesla Browser Validation**: Require Tesla/EV User-Agent for `/phone-start`
2. **HMAC-Signed Tokens**: Session tokens are signed, 30-min TTL
3. **Single-Use Activation**: Token binds to phone identity on first use
4. **Session Expiry**: 90 minutes max lifetime
5. **Phone Hashing**: Store phone hash, not raw phone where not needed

---

## PostHog Events

```typescript
// Session lifecycle
checkin.session_created { phone_hash, ip, user_agent, source, ev_brand }
checkin.sms_sent { session_id, phone_hash }
checkin.link_opened { session_id, user_agent }
checkin.otp_completed { session_id, user_id }
checkin.verified { session_id, method, accuracy_m, charger_id }
checkin.redeemed { session_id, merchant_id, order_total_cents, total_source }

// Errors
checkin.rate_limited { phone_hash?, ip, limit_type }
checkin.browser_rejected { user_agent, ip }
checkin.verification_failed { session_id, method, error }
```

---

## Verification Rules

Mark session as **VERIFIED** if ANY ONE condition passes:

| Method | Description | Phase |
|--------|-------------|-------|
| `phone_geofence` | Phone location within 250m of known charger | Phase 0 ✓ |
| `qr_scan` | QR code at charger contains charger_id | Phase 0 (stub) |
| `browser_geofence` | Car browser + phone auth (weak, entry only) | Phase 0 (entry) |

Phase 0 implements `phone_geofence` reliably.

---

## Cursor-Ready Implementation Prompts

### Prompt 1: Backend - Rate Limiting + Token Utils

```
Create rate limiting and HMAC token utilities for the phone-first checkin flow.

Files to create:
1. backend/app/utils/rate_limit.py
   - CheckinRateLimiter class
   - check_phone_limit(phone: str) -> bool (3/day per phone)
   - check_ip_limit(ip: str) -> bool (10/hour per IP)
   - Use Redis if available, fallback to in-memory with TTL

2. backend/app/utils/session_token.py
   - generate_session_token(session_id: str, phone_hash: str) -> str
   - verify_session_token(token: str) -> dict | None
   - Use HMAC-SHA256 with SECRET_KEY
   - Token format: base64url(session_id:phone_hash:expires:signature)
   - TTL: 30 minutes

Include tests for both utilities.
```

### Prompt 2: Backend - Update Checkin Service

```
Update checkin_service.py to support phone-first flow:

1. Add generate_session_code() -> str
   - 6 alphanumeric chars (no prefix)
   - Alphabet: 23456789ABCDEFGHJKMNPQRSTUVWXYZ

2. Add async phone_start_checkin():
   - Validate rate limits
   - Create ArrivalSession with flow_type='phone_first'
   - Generate session_code and signed token
   - Send SMS with link + code
   - Return { ok, session_code, expires_in }

3. Modify send_code_sms():
   - New message format for phone-first flow
   - Include both link and code

4. Add get_session_by_token():
   - Verify HMAC signature
   - Return session if valid and not expired

5. Keep existing code generation for backward compat with V0 flow.
```

### Prompt 3: Backend - Update Checkin Router

```
Update checkin.py router:

1. Add POST /v1/checkin/phone-start endpoint:
   - Validate Tesla/EV browser User-Agent (return 403 if not)
   - Accept { phone, charger_hint? }
   - Call phone_start_checkin()
   - Return { ok, session_code, expires_in }

2. Add middleware/dependency for browser validation:
   - require_ev_browser(request: Request) -> EVBrowserInfo
   - Raises HTTPException(403) if not EV browser

3. Modify GET /v1/checkin/session/{token}:
   - Accept token instead of session_id
   - Return limited data if not authenticated
   - Return full data if authenticated and phone matches

4. Add PostHog events to all endpoints.
```

### Prompt 4: Frontend - Link App

```
Create minimal Vite app at apps/link for link.nerava.network:

1. Structure:
   apps/link/
   ├── index.html
   ├── package.json
   ├── vite.config.ts
   ├── src/
   │   ├── main.tsx
   │   ├── App.tsx
   │   └── index.css

2. Features:
   - Single page with phone input
   - Large tap targets (Tesla touchscreen)
   - Minimal JS bundle (<50KB)
   - No framework animations
   - Submit → show success with session code

3. API call:
   POST /v1/checkin/phone-start { phone }

4. Success screen:
   "Sent! Open the link on your phone."
   Session code: ABC123 (large)

5. Error handling:
   - Rate limited: "Too many attempts. Try again later."
   - Invalid browser: "Please open this page in your Tesla browser."
```

### Prompt 5: Frontend - Driver Check-In Card

```
Add check-in card route to driver app at apps/driver:

1. Create src/components/CheckInCard/CheckInCard.tsx:
   - Large session code display
   - Status indicator (pending/verified/redeemed)
   - Charger/merchant context
   - "Verify I'm Charging" button (triggers geolocation)
   - "Show Proof" button (fullscreen code display)
   - Expiry countdown

2. Create src/pages/CheckInSession.tsx:
   - Route: /s/:token
   - Fetch session by token
   - Handle OTP if not authenticated
   - Display CheckInCard

3. Modify src/App.tsx:
   - Add route for /s/:token

4. Create src/components/CheckInCard/ProofScreen.tsx:
   - Fullscreen mode
   - Maximum brightness suggestion
   - Large code + verified badge
   - Merchant name + timestamp
```

### Prompt 6: Frontend - Merchant Redeem UI

```
Add redeem code functionality to merchant portal:

1. Create apps/merchant/app/components/RedeemCode.tsx:
   - Simple input for 6-char code
   - "Redeem" button
   - Optional: order total input
   - Success/error feedback

2. Modify apps/merchant/app/components/EVArrivals.tsx:
   - Add RedeemCode component at top
   - Show recent redemptions list

3. API integration:
   POST /v1/checkin/redeem { session_code, order_total_cents? }

4. Validation:
   - Code format (6 alphanumeric)
   - Show error if code not found or already redeemed
```

---

## Test Plan

### API Tests

```python
# test_phone_first_checkin.py

def test_phone_start_requires_ev_browser():
    """Non-EV browser should get 403."""
    response = client.post("/v1/checkin/phone-start",
        json={"phone": "+15125551234"},
        headers={"User-Agent": "Mozilla/5.0 Safari"})
    assert response.status_code == 403

def test_phone_start_with_tesla_browser():
    """Tesla browser should succeed."""
    response = client.post("/v1/checkin/phone-start",
        json={"phone": "+15125551234"},
        headers={"User-Agent": "Mozilla/5.0 Tesla/2024.44.6"})
    assert response.status_code == 201
    assert "session_code" in response.json()
    assert len(response.json()["session_code"]) == 6

def test_phone_rate_limit():
    """4th request same phone should fail."""
    for i in range(3):
        client.post("/v1/checkin/phone-start", ...)
    response = client.post("/v1/checkin/phone-start", ...)
    assert response.status_code == 429

def test_session_token_verification():
    """Token should be HMAC verified."""
    # Create session, get token
    # Tamper with token
    # Verify it fails

def test_verify_geofence_success():
    """Phone geolocation within radius should verify."""

def test_redeem_valid_code():
    """Merchant can redeem valid verified code."""

def test_redeem_unverified_fails():
    """Cannot redeem unverified session."""
```

### Frontend Smoke Tests

1. **Link App**
   - Load link.nerava.network in Tesla browser simulator
   - Enter phone, submit
   - See success screen with code

2. **Driver Check-In Card**
   - Open /s/{valid_token}
   - Complete OTP
   - See card with code
   - Tap verify, grant location
   - See "Verified" status

3. **Merchant Redeem**
   - Open merchant portal
   - Enter valid code
   - See success feedback

---

## Deployment

1. **DNS**: Add `link.nerava.network` → CloudFront
2. **CloudFront**: New distribution for link app
3. **S3**: New bucket for link app static files
4. **Backend**: Deploy updated checkin endpoints
5. **Driver App**: Deploy with new /s/:token route
6. **Merchant App**: Deploy with redeem UI

---

## Success Metrics

| Metric | Target |
|--------|--------|
| SMS delivery time | <10s |
| Verification success rate | >90% |
| Time from link open to verified | <60s |
| Merchant redeem time | <15s |
| PostHog funnel completion | Tracked |

---

## Timeline

| Day | Deliverable |
|-----|-------------|
| 1 | Backend: rate limiting, tokens, updated service |
| 2 | Backend: updated router, tests passing |
| 3 | Frontend: link app |
| 4 | Frontend: driver check-in card |
| 5 | Frontend: merchant redeem UI |
| 6 | Integration testing, bug fixes |
| 7 | Deploy to production |
