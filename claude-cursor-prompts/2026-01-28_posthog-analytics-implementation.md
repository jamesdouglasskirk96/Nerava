# CURSOR PROMPT: PostHog Analytics Implementation

**Date:** 2026-01-28
**Goal:** Ensure PostHog events fire correctly and add test endpoint

---

## EXISTING PATTERNS (follow these)

**Frontend:** `apps/driver/src/analytics/index.ts` - uses `capture(eventName, properties)`
**Backend:** `backend/app/services/analytics.py` - uses `get_analytics_client().capture()`
**Events:** `apps/driver/src/analytics/events.ts` - define event constants here

---

## 3 TASKS

### Task 1: Merchant Click Event (Frontend)

Add PostHog event when user clicks on a merchant card.

**Step 1: Add event to `apps/driver/src/analytics/events.ts`:**
```typescript
export const DRIVER_EVENTS = {
  // ... existing events ...

  // Merchant discovery
  MERCHANT_CLICKED: 'driver_merchant_clicked',
  MERCHANT_DETAIL_VIEWED: 'driver_merchant_detail_viewed',
} as const
```

**Step 2: Add capture call in these files:**

**`apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx`** - when card is clicked:
```typescript
import { capture, DRIVER_EVENTS } from '../../analytics'

// In click handler:
const handleMerchantClick = (merchant: Merchant) => {
  capture(DRIVER_EVENTS.MERCHANT_CLICKED, {
    merchant_id: merchant.id,
    merchant_name: merchant.name,
    category: merchant.category,
    source: 'carousel',
    path: window.location.pathname,
  });
  onMerchantSelect?.(merchant);
};
```

**`apps/driver/src/components/WhileYouCharge/FeaturedMerchantCard.tsx`** - same pattern with `source: 'featured'`

**`apps/driver/src/components/DriverHome/DriverHome.tsx`** - if merchants are clickable here, add with `source: 'home_list'`

---

### Task 2: OTP Sent Event (Backend)

Add PostHog event when OTP is sent via Twilio.

**File:** `backend/app/services/otp_service_v2.py`

**Use existing analytics client pattern:**
```python
import hashlib
from app.services.analytics import get_analytics_client

# After successful Twilio send, add:
analytics = get_analytics_client()
analytics.capture(
    event="server.otp.sent",
    distinct_id=user_id or f"phone:{hashlib.sha256(phone_number.encode()).hexdigest()[:16]}",
    properties={
        "phone_hash": hashlib.sha256(phone_number.encode()).hexdigest()[:16],
        "provider": self.provider,  # "twilio_verify" or "twilio_sms"
        "purpose": purpose or "login",  # "login", "merchant_claim", etc.
    }
)
```

**Find the send method and add after success confirmation:**
```python
# In send_otp() or similar method, after Twilio returns success:
if verification.status == "pending":  # or however success is determined
    # Existing success logic...

    # ADD: Track OTP sent
    analytics = get_analytics_client()
    analytics.capture(
        event="server.otp.sent",
        distinct_id=user_id or "anonymous",
        properties={
            "phone_hash": hashlib.sha256(phone_number.encode()).hexdigest()[:16],
            "provider": "twilio_verify",
        }
    )
```

**Also add for OTP verification success:**
```python
# After successful OTP verification:
analytics.capture(
    event="server.otp.verified",
    distinct_id=user_id,
    user_id=user_id,
    properties={
        "provider": "twilio_verify",
    }
)
```

---

### Task 3: Test Endpoint for PostHog Events

Create a Swagger-accessible endpoint to manually fire PostHog events (for testing).

**Create new file: `backend/app/routers/analytics_debug.py`**
```python
"""
Debug endpoint for testing PostHog events.
Only enabled in non-production environments.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os

from app.services.analytics import get_analytics_client

router = APIRouter(prefix="/debug/analytics", tags=["Debug - Analytics"])


class PostHogTestEvent(BaseModel):
    event: str
    distinct_id: Optional[str] = "test-user"
    properties: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "event": "test_event",
                "distinct_id": "user-123",
                "properties": {
                    "button": "merchant_card",
                    "merchant_id": "merch-456"
                }
            }
        }


@router.post("/posthog/test", summary="Fire a test PostHog event")
async def fire_test_posthog_event(payload: PostHogTestEvent):
    """
    Fire a test event to PostHog.

    **Only available in dev/staging environments.**

    Use this to verify PostHog integration is working.
    Check your PostHog dashboard for the event after calling.
    """
    env = os.getenv("ENV", "dev")
    if env == "prod":
        raise HTTPException(
            status_code=403,
            detail="Debug endpoints disabled in production"
        )

    analytics = get_analytics_client()
    if not analytics.enabled:
        raise HTTPException(
            status_code=400,
            detail="PostHog not configured (POSTHOG_KEY missing or ANALYTICS_ENABLED=false)"
        )

    analytics.capture(
        event=payload.event,
        distinct_id=payload.distinct_id or "test-user",
        properties={
            **(payload.properties or {}),
            "is_test": True,
        }
    )

    return {
        "ok": True,
        "message": f"Event '{payload.event}' sent to PostHog",
        "distinct_id": payload.distinct_id,
        "note": "Check PostHog dashboard in ~30 seconds"
    }


@router.get("/posthog/status", summary="Check PostHog configuration")
async def check_posthog_status():
    """Check if PostHog is configured and return safe config info."""
    analytics = get_analytics_client()
    posthog_key = os.getenv("POSTHOG_KEY") or os.getenv("POSTHOG_API_KEY", "")

    return {
        "configured": analytics.enabled,
        "host": analytics.posthog_host,
        "env": analytics.env,
        "key_prefix": posthog_key[:8] + "..." if posthog_key else None,
    }
```

**Register router in `backend/app/main.py`:**
```python
from app.routers import analytics_debug

# Add near other router includes, with env check:
if os.getenv("ENV", "dev") != "prod":
    app.include_router(analytics_debug.router)
```

---

## VERIFICATION CHECKLIST

After implementation:

### Frontend (Driver App)
- [ ] Click a merchant card → check browser console for `capture()` call
- [ ] Check PostHog dashboard for `merchant_clicked` event
- [ ] Verify properties include `merchant_id`, `merchant_name`, `source`

### Backend (OTP)
- [ ] Trigger OTP send (login flow or `/v1/auth/otp/send`)
- [ ] Check PostHog dashboard for `otp_sent` event
- [ ] Verify properties include `provider`, `purpose`, hashed phone

### Test Endpoint
- [ ] Open Swagger UI (`/docs`)
- [ ] Find `POST /debug/analytics/posthog/test`
- [ ] Send test event
- [ ] Verify it appears in PostHog dashboard within 30 seconds

---

## EXPECTED POSTHOG EVENTS

| Event | Source | Trigger |
|-------|--------|---------|
| `merchant_clicked` | Frontend | User taps merchant card |
| `merchant_detail_viewed` | Frontend | Merchant detail modal opens |
| `otp_sent` | Backend | Twilio sends OTP code |
| `otp_verified` | Backend | User enters correct OTP |
| `exclusive_activated` | Backend | User secures a spot |
| `test_event` | Backend | Debug endpoint called |

---

## POSTHOG DASHBOARD VERIFICATION

After events are firing, verify in PostHog:
1. Go to PostHog → Events
2. Filter by `merchant_clicked`, `otp_sent`
3. Verify properties are populated
4. Check "Live Events" stream for real-time verification

---

*Cursor: Implement these 3 tasks. Keep changes surgical. Follow existing patterns in the codebase.*
