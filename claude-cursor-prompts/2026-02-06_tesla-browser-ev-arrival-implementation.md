# Cursor Prompt: Tesla Browser + EV Arrival Implementation

**Date:** 2026-02-06
**Status:** Implementation-ready
**Approach:** In-car browser detection (NOT Smartcar)

---

## Core Insight

> **If someone is ordering from a Tesla browser while at a charger location, we KNOW they're an EV driver charging their car.**

No OAuth. No polling. No API keys. The browser IS the signal.

---

## Part 1: The Canonical Model (Preserved)

### Principle

**Arrival is the invariant. Orders are QUEUED and fire based on arrival triggers.**

Kitchen fires at: `arrival_time - prep_time`

### What DoorDash Doesn't Cover

DoorDash times food to the **delivery driver's arrival**, not the customer's. This scenario is completely unserved:

> **"I'm about to drive somewhere. I want to order food and have it ready when I arrive."**

### The Core Flow: Ready on Arrival

```
Driver at Location A (charging or at home)
    ↓
Opens Nerava in Tesla browser
    ↓
Selects restaurant near DESTINATION (Location B)
    ↓
Places order → ORDER IS QUEUED (kitchen does NOT fire)
    ↓
Driver starts driving (Autopilot, browser stays open)
    ↓
[During drive: geolocation fails — Tesla safety feature]
    ↓
Car parks near destination → Geolocation works again
    ↓
ARRIVAL DETECTED: location near restaurant
    ↓
Calculate: arrival_time - prep_time = fire_time
    ↓
Kitchen fires order
    ↓
Food ready when driver walks in
```

### The Two Fulfillment Options

Both use the same arrival trigger — the difference is WHERE you eat:

| Option | When Order Fires | Who Moves |
|--------|------------------|-----------|
| **🍽️ EV Dine-In** | `arrival_time - prep_time` | Driver walks to restaurant |
| **🚗 EV Curbside** | `arrival_time` (fire immediately on arrival) | Merchant brings food to car |

### Order Timing Math

```
prep_time = 15 min (restaurant-specific, configurable)
walk_time = 5 min (calculated from distance)

For Dine-In:
  fire_order_at = arrival_detected_time - prep_time + walk_time

  Example: Arrival detected, 15 min prep, 5 min walk
  → Fire immediately (driver will arrive in 5 min, food ready in 15 min)
  → Driver walks in at +5 min, food ready at +15 min
  → Driver waits ~10 min (could be better)

  Better: Fire order when arrival_detected - (prep_time - walk_time)
  → If prep_time > walk_time: Fire immediately on arrival
  → If prep_time < walk_time: Fire (walk_time - prep_time) BEFORE arrival

For Curbside:
  fire_order_at = arrival_detected_time
  → Fire immediately when driver arrives
  → Merchant brings food when ready (~15 min)
  → Driver stays in car, eats while charging
```

### Why This Works

| Factor | Traditional Delivery | Nerava Ready on Arrival |
|--------|---------------------|------------------------|
| When is order placed? | At destination | Before driving |
| When does kitchen fire? | Immediately | On arrival trigger |
| Who delivers? | Gig driver | Driver walks OR merchant walks |
| Food temperature | Often cold | Hot (arrival-timed) |
| Wait time at restaurant | Variable | Minimized (timed to arrival) |
| Delivery fee | $5-10 | $0 |

---

## Part 2: Tesla Browser Detection

### User Agent Patterns

**Modern Tesla (2019+):**
```
Mozilla/5.0 (X11; GNU/Linux) AppleWebKit/537.36 ... Tesla/2024.44.25-xxxxx
                                                    ^^^^^^^^^^^^^^^^^^^^^
```

**Older Tesla (Pre-2019):**
```
Mozilla/5.0 (X11; Linux) AppleWebKit/534.34 ... QtCarBrowser Safari/534.34
                                                ^^^^^^^^^^^^^
```

### Detection Code

**File:** `backend/app/utils/ev_browser.py`

```python
"""
EV browser detection utilities.

Detects Tesla and other EV in-car browsers from User-Agent headers.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class EVBrowserInfo:
    """Information about detected EV browser."""
    is_ev_browser: bool
    brand: Optional[str] = None
    firmware_version: Optional[str] = None


# Patterns for detection
TESLA_MODERN_PATTERN = re.compile(r'Tesla/(\d{4}\.\d+\.\d+(?:\.\d+)?)', re.IGNORECASE)
TESLA_LEGACY_PATTERN = re.compile(r'QtCarBrowser', re.IGNORECASE)


def detect_ev_browser(user_agent: str) -> EVBrowserInfo:
    """
    Detect if request is from an EV in-car browser.

    Currently supports:
    - Tesla (modern firmware with Tesla/xxxx.xx.xx)
    - Tesla (legacy with QtCarBrowser)

    Returns EVBrowserInfo with detected brand and firmware.
    """
    if not user_agent:
        return EVBrowserInfo(is_ev_browser=False)

    # Tesla modern detection
    tesla_match = TESLA_MODERN_PATTERN.search(user_agent)
    if tesla_match:
        return EVBrowserInfo(
            is_ev_browser=True,
            brand="Tesla",
            firmware_version=tesla_match.group(1),
        )

    # Tesla legacy detection
    if TESLA_LEGACY_PATTERN.search(user_agent):
        return EVBrowserInfo(
            is_ev_browser=True,
            brand="Tesla",
            firmware_version="legacy",
        )

    # Android Automotive (Polestar, Volvo, etc.)
    if 'android automotive' in user_agent.lower():
        return EVBrowserInfo(
            is_ev_browser=True,
            brand="Android Automotive",
        )

    return EVBrowserInfo(is_ev_browser=False)


def is_tesla_browser(user_agent: str) -> bool:
    """Quick check if request is from Tesla browser."""
    if not user_agent:
        return False
    return bool(TESLA_MODERN_PATTERN.search(user_agent) or
                TESLA_LEGACY_PATTERN.search(user_agent))
```

**File:** `apps/driver/src/utils/evBrowserDetection.ts`

```typescript
/**
 * EV browser detection for frontend.
 */

export interface EVBrowserInfo {
  isEVBrowser: boolean;
  brand: string | null;
  firmwareVersion: string | null;
}

export function detectEVBrowser(): EVBrowserInfo {
  const ua = navigator.userAgent;

  // Tesla modern (2019+)
  const teslaMatch = ua.match(/Tesla\/(\d{4}\.\d+\.\d+(?:\.\d+)?)/i);
  if (teslaMatch) {
    return {
      isEVBrowser: true,
      brand: 'Tesla',
      firmwareVersion: teslaMatch[1],
    };
  }

  // Tesla legacy
  if (/QtCarBrowser/i.test(ua)) {
    return {
      isEVBrowser: true,
      brand: 'Tesla',
      firmwareVersion: 'legacy',
    };
  }

  // Android Automotive
  if (/android automotive/i.test(ua)) {
    return {
      isEVBrowser: true,
      brand: 'Android Automotive',
      firmwareVersion: null,
    };
  }

  return {
    isEVBrowser: false,
    brand: null,
    firmwareVersion: null,
  };
}

export function isTeslaBrowser(): boolean {
  const ua = navigator.userAgent;
  return /Tesla\//i.test(ua) || /QtCarBrowser/i.test(ua);
}
```

---

## Part 3: Geolocation in Tesla Browser

### Capability

Tesla browser supports **standard Geolocation API** since firmware v5.9:

```typescript
// This works in Tesla browser!
navigator.geolocation.getCurrentPosition(
  (position) => {
    const { latitude, longitude, accuracy } = position.coords;
    // Send to backend
  },
  (error) => {
    // Handle denial or error
  },
  { enableHighAccuracy: true }
);
```

### Behavior by State

| Car State | Geolocation |
|-----------|-------------|
| Parked | ✅ Works |
| Charging | ✅ Works (car is parked) |
| Driving | ⚠️ Updates stop |
| Parked after driving | ✅ Works again |

### Why This Matters

If someone is using the Tesla browser and geolocation returns a location at a charger:
- ✅ They are definitely at a charger (can't spoof this easily)
- ✅ They are parked (geolocation works when parked)
- ✅ They are an EV driver (it's a Tesla browser)

**This is all we need to enable Ready on Arrival ordering.**

---

## Part 4: New API Endpoint

### `/v1/ev-context` — EV Browser Context

**File:** `backend/app/routers/ev_context.py`

```python
"""
EV Context Router — /v1/ev-context

Detects EV browser and returns context-aware merchant recommendations.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.models.while_you_charge import Charger, Merchant
from app.dependencies.auth import get_optional_driver
from app.utils.ev_browser import detect_ev_browser, EVBrowserInfo
from app.services.geo import haversine_m
from app.services.analytics import get_analytics_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/ev-context", tags=["ev-context"])

CHARGER_MATCH_RADIUS_M = 150  # Must be within 150m to count as "at charger"


class EVContextRequest(BaseModel):
    lat: float
    lng: float
    accuracy_m: Optional[float] = None


class ChargerInfo(BaseModel):
    id: str
    name: str
    network: Optional[str] = None
    address: Optional[str] = None
    stall_count: Optional[int] = None


class MerchantInfo(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    rating: Optional[float] = None
    photo_url: Optional[str] = None
    distance_m: int
    walk_minutes: int
    ordering_url: Optional[str] = None


class EVContextResponse(BaseModel):
    # Browser detection
    is_ev_browser: bool
    ev_brand: Optional[str] = None
    ev_firmware: Optional[str] = None

    # Location context
    at_charger: bool
    charger: Optional[ChargerInfo] = None

    # Recommendations
    nearby_merchants: List[MerchantInfo]

    # Fulfillment options (both are Ready on Arrival)
    fulfillment_options: List[str]  # ['ev_dine_in', 'ev_curbside']

    # Vehicle setup needed
    vehicle_setup_needed: bool = False


@router.post("", response_model=EVContextResponse)
async def get_ev_context(
    req: EVContextRequest,
    request: Request,
    driver: Optional[User] = Depends(get_optional_driver),
    db: Session = Depends(get_db),
):
    """
    Get EV-aware context for ordering.

    Detects:
    1. Is this an EV in-car browser? (Tesla, Polestar, etc.)
    2. Is the driver at a charger?
    3. What merchants are nearby?

    Returns optimized flow suggestion.
    """
    # Detect EV browser from User-Agent
    user_agent = request.headers.get("User-Agent", "")
    ev_info = detect_ev_browser(user_agent)

    # Find nearest charger
    charger = _find_nearest_charger(db, req.lat, req.lng)
    at_charger = charger is not None

    # Get nearby merchants (relative to charger if at one)
    anchor_lat = charger.lat if charger else req.lat
    anchor_lng = charger.lng if charger else req.lng
    merchants = _get_nearby_merchants(db, anchor_lat, anchor_lng)

    # Determine fulfillment options
    # Both are "Ready on Arrival" — difference is WHERE you eat
    if ev_info.is_ev_browser and at_charger:
        fulfillment_options = ["ev_dine_in", "ev_curbside"]
    else:
        fulfillment_options = ["standard"]

    # Check if vehicle setup needed (for authenticated users)
    vehicle_setup_needed = False
    if driver and ev_info.is_ev_browser:
        vehicle_setup_needed = not bool(getattr(driver, 'vehicle_color', None))

    # Track analytics
    _capture_ev_context_event(driver, ev_info, at_charger, charger)

    return EVContextResponse(
        is_ev_browser=ev_info.is_ev_browser,
        ev_brand=ev_info.brand,
        ev_firmware=ev_info.firmware_version,
        at_charger=at_charger,
        charger=ChargerInfo(
            id=charger.id,
            name=charger.name,
            network=getattr(charger, 'network', None),
            address=getattr(charger, 'address', None),
            stall_count=getattr(charger, 'stall_count', None),
        ) if charger else None,
        nearby_merchants=merchants,
        fulfillment_options=fulfillment_options,
        vehicle_setup_needed=vehicle_setup_needed,
    )


def _find_nearest_charger(db: Session, lat: float, lng: float) -> Optional[Charger]:
    """Find charger within CHARGER_MATCH_RADIUS_M of location."""
    chargers = db.query(Charger).all()

    for charger in chargers:
        distance = haversine_m(lat, lng, charger.lat, charger.lng)
        if distance <= CHARGER_MATCH_RADIUS_M:
            return charger

    return None


def _get_nearby_merchants(
    db: Session,
    lat: float,
    lng: float,
    limit: int = 10
) -> List[MerchantInfo]:
    """Get merchants near location, sorted by distance."""
    merchants = db.query(Merchant).filter(Merchant.is_active == True).all()

    results = []
    for merchant in merchants:
        distance = haversine_m(lat, lng, merchant.lat, merchant.lng)
        if distance <= 2000:  # Within 2km
            walk_minutes = max(1, int(distance / 80))  # ~80m/min walking
            results.append(MerchantInfo(
                id=merchant.id,
                name=merchant.name,
                category=getattr(merchant, 'category', None),
                rating=getattr(merchant, 'rating', None),
                photo_url=getattr(merchant, 'photo_url', None),
                distance_m=int(distance),
                walk_minutes=walk_minutes,
                ordering_url=getattr(merchant, 'ordering_url', None),
            ))

    # Sort by distance
    results.sort(key=lambda m: m.distance_m)
    return results[:limit]


def _capture_ev_context_event(
    driver: Optional[User],
    ev_info: EVBrowserInfo,
    at_charger: bool,
    charger: Optional[Charger],
):
    """Track EV context analytics."""
    try:
        analytics = get_analytics_client()
        if analytics:
            analytics.capture(
                distinct_id=str(driver.id) if driver else "anonymous",
                event="ev_context.loaded",
                properties={
                    "is_ev_browser": ev_info.is_ev_browser,
                    "ev_brand": ev_info.brand,
                    "at_charger": at_charger,
                    "charger_id": charger.id if charger else None,
                },
            )
    except Exception as e:
        logger.warning(f"Analytics failed: {e}")
```

---

## Part 5: Updated ArrivalSession Model

### New Fields

Add to `backend/app/models/arrival_session.py`:

```python
# Browser detection fields
browser_source = Column(String(30), nullable=True)  # 'tesla_browser', 'web', 'ios_app'
ev_brand = Column(String(30), nullable=True)  # 'Tesla', 'Polestar', etc.
ev_firmware = Column(String(50), nullable=True)

# Fulfillment type (both are Ready on Arrival)
fulfillment_type = Column(String(20), nullable=True)  # 'ev_dine_in', 'ev_curbside'
# ev_dine_in = Driver walks to restaurant, food ready when they arrive
# ev_curbside = Driver stays at car, merchant brings food to charger

# Order queuing and release
order_status = Column(String(20), default="queued")
# 'queued' — Order placed, waiting for arrival trigger
# 'released' — Arrival detected, order sent to kitchen
# 'preparing' — Kitchen acknowledged, cooking
# 'ready' — Food ready for pickup/delivery
# 'completed' — Order fulfilled

# Destination (restaurant location for arrival detection)
destination_merchant_id = Column(String, ForeignKey("merchants.id"), nullable=True)
destination_lat = Column(Float, nullable=True)
destination_lng = Column(Float, nullable=True)

# Arrival detection timestamps
arrival_detected_at = Column(DateTime, nullable=True)
order_released_at = Column(DateTime, nullable=True)
order_ready_at = Column(DateTime, nullable=True)

# Distance when arrival was detected
arrival_distance_m = Column(Float, nullable=True)
```

### Order Status Flow

```
QUEUED ──────────────────────────────────────────────────────────────►
   │                                                                  │
   │ arrival_detected (geolocation near restaurant)                   │
   ▼                                                                  │
RELEASED ─────────────────────────────────────────────────────────────►
   │                                                                  │
   │ merchant confirms receipt                                        │
   ▼                                                                  │
PREPARING ────────────────────────────────────────────────────────────►
   │                                                                  │
   │ Toast status = ready OR merchant replies READY                   │
   ▼                                                                  │
READY ────────────────────────────────────────────────────────────────►
   │                                                                  │
   │ merchant confirms delivery OR driver confirms pickup             │
   ▼                                                                  │
COMPLETED ────────────────────────────────────────────────────────────►
```

### Migration

**File:** `backend/alembic/versions/064_add_queued_order_fields.py`

```python
"""Add queued order fields to arrival_sessions

Revision ID: 064
"""
from alembic import op
import sqlalchemy as sa

revision = '064'
down_revision = '063'


def upgrade():
    # Browser detection
    op.add_column('arrival_sessions',
        sa.Column('browser_source', sa.String(30), nullable=True))
    op.add_column('arrival_sessions',
        sa.Column('ev_brand', sa.String(30), nullable=True))
    op.add_column('arrival_sessions',
        sa.Column('ev_firmware', sa.String(50), nullable=True))

    # Fulfillment
    op.add_column('arrival_sessions',
        sa.Column('fulfillment_type', sa.String(20), nullable=True))

    # Order queuing
    op.add_column('arrival_sessions',
        sa.Column('order_status', sa.String(20), server_default='queued'))

    # Destination for arrival detection
    op.add_column('arrival_sessions',
        sa.Column('destination_merchant_id', sa.String(), nullable=True))
    op.add_column('arrival_sessions',
        sa.Column('destination_lat', sa.Float(), nullable=True))
    op.add_column('arrival_sessions',
        sa.Column('destination_lng', sa.Float(), nullable=True))

    # Timestamps
    op.add_column('arrival_sessions',
        sa.Column('arrival_detected_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions',
        sa.Column('order_released_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions',
        sa.Column('order_ready_at', sa.DateTime(), nullable=True))

    # Distance
    op.add_column('arrival_sessions',
        sa.Column('arrival_distance_m', sa.Float(), nullable=True))

    # Index for finding queued orders
    op.create_index(
        'idx_arrival_queued',
        'arrival_sessions',
        ['order_status', 'destination_merchant_id'],
    )


def downgrade():
    op.drop_index('idx_arrival_queued')
    op.drop_column('arrival_sessions', 'arrival_distance_m')
    op.drop_column('arrival_sessions', 'order_ready_at')
    op.drop_column('arrival_sessions', 'order_released_at')
    op.drop_column('arrival_sessions', 'arrival_detected_at')
    op.drop_column('arrival_sessions', 'destination_lng')
    op.drop_column('arrival_sessions', 'destination_lat')
    op.drop_column('arrival_sessions', 'destination_merchant_id')
    op.drop_column('arrival_sessions', 'order_status')
    op.drop_column('arrival_sessions', 'fulfillment_type')
    op.drop_column('arrival_sessions', 'ev_firmware')
    op.drop_column('arrival_sessions', 'ev_brand')
    op.drop_column('arrival_sessions', 'browser_source')
```

---

## Part 6: Order Queuing & Arrival Triggers

### Order States

```
QUEUED → RELEASED → PREPARING → READY → COMPLETED
```

| State | Kitchen Status | Driver Status |
|-------|---------------|---------------|
| `QUEUED` | Hasn't seen order | Driving to destination |
| `RELEASED` | Order fired to kitchen | Arrived or arriving soon |
| `PREPARING` | Cooking | Walking to restaurant or waiting at car |
| `READY` | Food ready | Picking up or receiving delivery |
| `COMPLETED` | Done | Eating |

### Arrival Detection

The Tesla browser provides the arrival signal:

```typescript
// Frontend: Poll for location during drive
async function checkArrival(sessionId: string, merchantLat: number, merchantLng: number) {
  try {
    // This will FAIL while driving (Tesla safety feature)
    // This will SUCCEED when car is parked
    const position = await getCurrentPosition();

    const distance = haversine(
      position.coords.latitude,
      position.coords.longitude,
      merchantLat,
      merchantLng
    );

    // Within 500m of restaurant = ARRIVAL
    if (distance < 500) {
      await api.post(`/v1/arrival/${sessionId}/trigger-arrival`, {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      });
      return true;
    }
  } catch (error) {
    // Geolocation failed — still driving, keep polling
    return false;
  }
  return false;
}
```

### Backend: Arrival Trigger Endpoint

**File:** `backend/app/routers/arrival.py`

```python
class TriggerArrivalRequest(BaseModel):
    lat: float
    lng: float
    accuracy_m: Optional[float] = None


class TriggerArrivalResponse(BaseModel):
    status: str
    order_released: bool
    estimated_ready_minutes: Optional[int] = None


@router.post("/{session_id}/trigger-arrival", response_model=TriggerArrivalResponse)
async def trigger_arrival(
    session_id: str,
    req: TriggerArrivalRequest,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """
    Arrival trigger — called when driver arrives near restaurant.

    This releases the queued order based on:
    - Fulfillment type (dine-in vs curbside)
    - Restaurant prep time
    - Walk time (for dine-in)
    """
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    if not session or session.driver_id != driver.id:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.order_status != "queued":
        return TriggerArrivalResponse(
            status=session.order_status,
            order_released=session.order_status in ("released", "preparing", "ready"),
        )

    # Verify location is near merchant
    merchant = db.query(Merchant).filter(Merchant.id == session.merchant_id).first()
    distance_m = haversine_m(req.lat, req.lng, merchant.lat, merchant.lng)

    if distance_m > 500:  # Must be within 500m
        return TriggerArrivalResponse(
            status="queued",
            order_released=False,
        )

    # Record arrival
    session.arrival_lat = req.lat
    session.arrival_lng = req.lng
    session.arrival_accuracy_m = req.accuracy_m
    session.arrival_detected_at = datetime.utcnow()

    # Calculate when to fire order
    prep_time_minutes = merchant.prep_time_minutes or 15  # Default 15 min
    walk_time_minutes = max(1, int(distance_m / 80))  # ~80m/min walking

    if session.fulfillment_type == "ev_dine_in":
        # For dine-in: Fire so food is ready when driver walks in
        # If prep_time > walk_time, fire immediately
        # If prep_time < walk_time, we'd need to fire BEFORE arrival (not possible here)
        # So: always fire immediately on arrival for dine-in
        delay_minutes = 0
        estimated_ready = prep_time_minutes
    else:
        # For curbside: Fire immediately, merchant will bring when ready
        delay_minutes = 0
        estimated_ready = prep_time_minutes

    # Release the order
    session.order_status = "released"
    session.order_released_at = datetime.utcnow()

    # Notify merchant
    await _send_order_to_merchant(db, session, merchant, estimated_ready)

    db.commit()

    _capture_event("ev_arrival.order_released", driver.id, {
        "session_id": session_id,
        "merchant_id": session.merchant_id,
        "fulfillment_type": session.fulfillment_type,
        "distance_m": int(distance_m),
        "prep_time_minutes": prep_time_minutes,
    })

    return TriggerArrivalResponse(
        status="released",
        order_released=True,
        estimated_ready_minutes=estimated_ready,
    )


async def _send_order_to_merchant(
    db: Session,
    session: ArrivalSession,
    merchant: Merchant,
    estimated_ready_minutes: int,
):
    """Send the order to the merchant (via Toast, SMS, or dashboard)."""

    notif_config = (
        db.query(MerchantNotificationConfig)
        .filter(MerchantNotificationConfig.merchant_id == merchant.id)
        .first()
    )

    charger = db.query(Charger).filter(Charger.id == session.charger_id).first()

    if session.fulfillment_type == "ev_dine_in":
        message = f"""NERAVA EV DINE-IN 🍽️

Order #{session.order_number} — ${session.order_total_cents / 100:.2f}

Driver arriving NOW from {charger.name if charger else 'nearby charger'}
Walking over — ETA ~{max(1, int(session.arrival_distance_m / 80))} minutes

Vehicle: {session.vehicle_color} Tesla

Reply READY when order is prepared."""

    else:  # ev_curbside
        message = f"""NERAVA EV CURBSIDE 🚗

Order #{session.order_number} — ${session.order_total_cents / 100:.2f}

DELIVER TO CHARGER when ready

{session.vehicle_color} Tesla
{charger.name if charger else 'Nearby charger'}
{charger.address if charger else ''}

Bring order to the driver's car when ready.
Reply DELIVERED when complete."""

    if notif_config and notif_config.notify_sms and notif_config.sms_phone:
        await send_sms(notif_config.sms_phone, message)

    # Also push to merchant dashboard
    # ... (existing notification logic)
```

### Frontend: Location Polling During Drive

**File:** `apps/driver/src/hooks/useArrivalPolling.ts`

```typescript
import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';

interface UseArrivalPollingOptions {
  sessionId: string;
  merchantLat: number;
  merchantLng: number;
  enabled: boolean;
  onArrival: (response: ArrivalResponse) => void;
}

interface ArrivalResponse {
  status: string;
  order_released: boolean;
  estimated_ready_minutes?: number;
}

export function useArrivalPolling({
  sessionId,
  merchantLat,
  merchantLng,
  enabled,
  onArrival,
}: UseArrivalPollingOptions) {
  const [polling, setPolling] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    setPolling(true);

    const checkArrival = async () => {
      try {
        // Try to get location (fails while driving, succeeds when parked)
        const position = await new Promise<GeolocationPosition>(
          (resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
              resolve,
              reject,
              { enableHighAccuracy: true, timeout: 10000 }
            );
          }
        );

        setLastCheck(new Date());

        // Calculate distance to restaurant
        const distance = haversine(
          position.coords.latitude,
          position.coords.longitude,
          merchantLat,
          merchantLng
        );

        console.log(`Distance to restaurant: ${distance}m`);

        // If within 500m, trigger arrival
        if (distance < 500) {
          const response = await api.post(
            `/v1/arrival/${sessionId}/trigger-arrival`,
            {
              lat: position.coords.latitude,
              lng: position.coords.longitude,
              accuracy_m: position.coords.accuracy,
            }
          );

          if (response.data.order_released) {
            setPolling(false);
            if (intervalRef.current) clearInterval(intervalRef.current);
            onArrival(response.data);
          }
        }

      } catch (error) {
        // Geolocation failed — probably still driving
        // This is expected behavior, keep polling
        console.log('Still driving, geolocation unavailable...');
        setLastCheck(new Date());
      }
    };

    // Poll every 30 seconds
    checkArrival(); // Check immediately
    intervalRef.current = setInterval(checkArrival, 30000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [sessionId, merchantLat, merchantLng, enabled, onArrival]);

  return { polling, lastCheck };
}

// Haversine formula for distance calculation
function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000; // Earth's radius in meters
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function toRad(deg: number): number {
  return deg * (Math.PI / 180);
}
```

### Toast Integration for Order Status

With Toast read integration, we can notify driver when food is ready:

```python
# Background job: Poll Toast for order status
async def poll_order_status(session_id: str):
    """Check if order is ready and notify driver."""
    session = get_session(session_id)

    if session.order_status not in ("released", "preparing"):
        return

    if session.order_source == "toast":
        toast_adapter = get_pos_adapter("toast", get_merchant_creds(session.merchant_id))
        status = await toast_adapter.get_order_status(session.order_number)

        if status == "ready" and session.order_status != "ready":
            session.order_status = "ready"
            session.order_ready_at = datetime.utcnow()

            # Notify driver
            if session.fulfillment_type == "ev_dine_in":
                await send_driver_notification(
                    session.driver_id,
                    title="Your order is ready! 🎉",
                    body=f"Head to {session.merchant.name} to pick up order #{session.order_number}",
                )
            else:
                await send_driver_notification(
                    session.driver_id,
                    title="Food on the way! 🚗",
                    body=f"Your order is being brought to your car",
                )
```

---

## Part 7: Frontend — Tesla Browser Experience

### Entry Point Detection

**File:** `apps/driver/src/hooks/useEVContext.ts`

```typescript
import { useState, useEffect } from 'react';
import { detectEVBrowser, EVBrowserInfo } from '../utils/evBrowserDetection';
import { api } from '../services/api';

interface EVContext {
  loading: boolean;
  error: string | null;

  // Browser info
  isEVBrowser: boolean;
  evBrand: string | null;

  // Location context
  atCharger: boolean;
  charger: ChargerInfo | null;

  // Recommendations
  nearbyMerchants: MerchantInfo[];

  // Fulfillment options (both are Ready on Arrival)
  fulfillmentOptions: ('ev_dine_in' | 'ev_curbside' | 'standard')[];

  // Setup
  vehicleSetupNeeded: boolean;
}

export function useEVContext(): EVContext {
  const [context, setContext] = useState<EVContext>({
    loading: true,
    error: null,
    isEVBrowser: false,
    evBrand: null,
    atCharger: false,
    charger: null,
    nearbyMerchants: [],
    fulfillmentOptions: ['standard'],
    vehicleSetupNeeded: false,
  });

  useEffect(() => {
    async function loadContext() {
      // First, detect browser locally
      const browserInfo = detectEVBrowser();

      try {
        // Get location
        const position = await getCurrentPosition();

        // Call backend for full context
        const response = await api.post('/v1/ev-context', {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy_m: position.coords.accuracy,
        });

        setContext({
          loading: false,
          error: null,
          isEVBrowser: response.data.is_ev_browser,
          evBrand: response.data.ev_brand,
          atCharger: response.data.at_charger,
          charger: response.data.charger,
          nearbyMerchants: response.data.nearby_merchants,
          fulfillmentOptions: response.data.fulfillment_options,
          vehicleSetupNeeded: response.data.vehicle_setup_needed,
        });

      } catch (error) {
        setContext(prev => ({
          ...prev,
          loading: false,
          error: 'Failed to load context',
          isEVBrowser: browserInfo.isEVBrowser,
          evBrand: browserInfo.brand,
        }));
      }
    }

    loadContext();
  }, []);

  return context;
}

function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
    });
  });
}
```

### Tesla-Optimized Home Screen

**File:** `apps/driver/src/components/EVHome/EVHome.tsx`

```tsx
/**
 * EVHome — Optimized experience for Tesla browser users at chargers.
 */
import React from 'react';
import { useEVContext } from '../../hooks/useEVContext';
import { MerchantCard } from './MerchantCard';
import { VehicleSetupPrompt } from './VehicleSetupPrompt';
import { LoadingSpinner } from '../shared/LoadingSpinner';

export function EVHome() {
  const context = useEVContext();

  if (context.loading) {
    return <LoadingSpinner />;
  }

  // Show vehicle setup if needed (first time EV browser user)
  if (context.vehicleSetupNeeded) {
    return <VehicleSetupPrompt onComplete={() => window.location.reload()} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with charger info */}
      {context.atCharger && context.charger && (
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⚡</span>
            <span className="text-sm font-medium opacity-90">
              Charging at
            </span>
          </div>
          <h1 className="text-xl font-semibold">
            {context.charger.name}
          </h1>
          {context.charger.address && (
            <p className="text-sm opacity-80 mt-1">
              {context.charger.address}
            </p>
          )}
        </div>
      )}

      {/* Value proposition */}
      <div className="px-4 py-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Hot food, ready on arrival
        </h2>
        <p className="text-sm text-gray-600">
          Order now — your food will be ready when you walk in,
          or we'll bring it to your car.
        </p>
      </div>

      {/* Merchant list */}
      <div className="px-4 space-y-4">
        {context.nearbyMerchants.map((merchant) => (
          <MerchantCard
            key={merchant.id}
            merchant={merchant}
            fulfillmentOptions={context.fulfillmentOptions}
          />
        ))}

        {context.nearbyMerchants.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No nearby restaurants found
          </div>
        )}
      </div>
    </div>
  );
}
```

### Merchant Card with Fulfillment Options

```tsx
interface MerchantCardProps {
  merchant: MerchantInfo;
  fulfillmentOptions: ('ev_dine_in' | 'ev_curbside' | 'standard')[];
}

export function MerchantCard({ merchant, fulfillmentOptions }: MerchantCardProps) {
  const navigate = useNavigate();

  const handleOrder = (fulfillment: string) => {
    navigate(`/order?merchant=${merchant.id}&fulfillment=${fulfillment}`);
  };

  const showEVOptions = fulfillmentOptions.includes('ev_dine_in');

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      {/* Photo */}
      {merchant.photo_url && (
        <img
          src={merchant.photo_url}
          alt={merchant.name}
          className="w-full h-32 object-cover"
        />
      )}

      <div className="p-4">
        {/* Name and rating */}
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-900">
            {merchant.name}
          </h3>
          {merchant.rating && (
            <span className="text-sm text-gray-600">
              ★ {merchant.rating.toFixed(1)}
            </span>
          )}
        </div>

        {/* Category and distance */}
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
          {merchant.category && <span>{merchant.category}</span>}
          <span>·</span>
          <span>{merchant.walk_minutes} min walk</span>
        </div>

        {/* Fulfillment options — both are Ready on Arrival */}
        {showEVOptions ? (
          <div className="space-y-2">
            <button
              onClick={() => handleOrder('ev_dine_in')}
              className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg
                         font-medium hover:bg-blue-700 transition-colors"
            >
              🍽️ Walk In & Dine
            </button>
            <button
              onClick={() => handleOrder('ev_curbside')}
              className="w-full py-3 px-4 bg-white text-blue-600 border-2 border-blue-600
                         rounded-lg font-medium hover:bg-blue-50 transition-colors"
            >
              🚗 Eat in Car
            </button>
          </div>
        ) : (
          <button
            onClick={() => handleOrder('standard')}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg
                       font-medium hover:bg-blue-700 transition-colors"
          >
            Order Now →
          </button>
        )}
      </div>
    </div>
  );
}
```

### What Each Option Means

| Option | Driver Does | Merchant Does |
|--------|-------------|---------------|
| **🍽️ Walk In & Dine** | Walks to restaurant | Has food ready when driver arrives |
| **🚗 Eat in Car** | Stays at charger | Brings food to driver's car |

**Both are "Ready on Arrival"** — the only difference is WHO walks.

---

## Part 8: Order Flow Component (With Queuing)

After selecting a merchant and fulfillment type, the driver goes through the order flow. The order is **QUEUED** until arrival is detected.

**File:** `apps/driver/src/components/EVOrder/EVOrderFlow.tsx`

```tsx
/**
 * EVOrderFlow — Order placement for EV drivers.
 *
 * Flow:
 * 1. Confirm fulfillment type (dine-in vs eat-in-car)
 * 2. Open merchant's ordering page (Toast, Square, etc.)
 * 3. Return and enter order number
 * 4. Order is QUEUED — start polling for arrival
 * 5. On arrival detection → Order RELEASED to kitchen
 * 6. Show "Order ready" notification
 */
import React, { useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { capture, DRIVER_EVENTS } from '../../analytics';
import { useArrivalPolling } from '../../hooks/useArrivalPolling';

type FulfillmentType = 'ev_dine_in' | 'ev_curbside';
type Step = 'confirm' | 'ordering' | 'order_number' | 'queued' | 'released' | 'ready';

export function EVOrderFlow() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const merchantId = searchParams.get('merchant');
  const fulfillment = searchParams.get('fulfillment') as FulfillmentType;

  const [step, setStep] = useState<Step>('confirm');
  const [orderNumber, setOrderNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<any>(null);
  const [merchant, setMerchant] = useState<any>(null);
  const [estimatedReady, setEstimatedReady] = useState<number | null>(null);

  // Start polling for arrival when order is queued
  const handleArrival = useCallback((response: any) => {
    setStep('released');
    setEstimatedReady(response.estimated_ready_minutes);

    capture(DRIVER_EVENTS.EV_ORDER_RELEASED, {
      session_id: session?.session_id,
      estimated_ready_minutes: response.estimated_ready_minutes,
    });
  }, [session]);

  const { polling } = useArrivalPolling({
    sessionId: session?.session_id || '',
    merchantLat: merchant?.lat || 0,
    merchantLng: merchant?.lng || 0,
    enabled: step === 'queued' && !!session && !!merchant,
    onArrival: handleArrival,
  });

  const handleConfirmAndOrder = async () => {
    setLoading(true);

    try {
      // Get current location
      const position = await getCurrentPosition();

      // Load merchant details for arrival detection
      const merchantResponse = await api.get(`/v1/merchants/${merchantId}`);
      setMerchant(merchantResponse.data);

      // Create the arrival session with QUEUED status
      const response = await api.post('/v1/arrival/create', {
        merchant_id: merchantId,
        fulfillment_type: fulfillment,
        destination_lat: merchantResponse.data.lat,
        destination_lng: merchantResponse.data.lng,
        current_lat: position.coords.latitude,
        current_lng: position.coords.longitude,
        accuracy_m: position.coords.accuracy,
      });

      setSession(response.data);

      capture(DRIVER_EVENTS.EV_ORDER_STARTED, {
        merchant_id: merchantId,
        fulfillment_type: fulfillment,
      });

      // Open merchant's ordering URL
      if (response.data.ordering_url) {
        window.open(response.data.ordering_url, '_blank');
      }

      setStep('order_number');

    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitOrderNumber = async () => {
    if (!orderNumber.trim() || !session) return;

    setLoading(true);

    try {
      // Bind order number — order remains QUEUED
      await api.put(`/v1/arrival/${session.session_id}/order`, {
        order_number: orderNumber.trim(),
      });

      capture(DRIVER_EVENTS.EV_ORDER_QUEUED, {
        session_id: session.session_id,
        fulfillment_type: fulfillment,
      });

      // Move to queued state — start polling for arrival
      setStep('queued');

    } catch (error) {
      console.error('Failed to bind order:', error);
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Confirm fulfillment type
  if (step === 'confirm') {
    return (
      <div className="min-h-screen bg-white p-6">
        <div className="max-w-md mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            {fulfillment === 'ev_dine_in' ? '🍽️ Walk In & Dine' : '🚗 Eat in Car'}
          </h1>

          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            {fulfillment === 'ev_dine_in' ? (
              <p className="text-blue-800">
                Your food will be <strong>hot and ready</strong> when you walk in.
                We'll notify the restaurant when you arrive.
              </p>
            ) : (
              <p className="text-blue-800">
                Stay at your car — the restaurant will <strong>bring your food
                to the charger</strong> when you arrive.
              </p>
            )}
          </div>

          <button
            onClick={handleConfirmAndOrder}
            disabled={loading}
            className="w-full py-4 bg-blue-600 text-white rounded-lg font-semibold
                       disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Continue to Order →'}
          </button>
        </div>
      </div>
    );
  }

  // Step 2: Enter order number after ordering
  if (step === 'order_number') {
    return (
      <div className="min-h-screen bg-white p-6">
        <div className="max-w-md mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Almost done!
          </h1>
          <p className="text-gray-600 mb-6">
            Enter your order number from the receipt.
          </p>

          <input
            type="text"
            value={orderNumber}
            onChange={(e) => setOrderNumber(e.target.value)}
            placeholder="Order #"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg
                       mb-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />

          <button
            onClick={handleSubmitOrderNumber}
            disabled={!orderNumber.trim() || loading}
            className="w-full py-4 bg-blue-600 text-white rounded-lg font-semibold
                       disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Queue My Order'}
          </button>

          <button
            onClick={() => session?.ordering_url && window.open(session.ordering_url, '_blank')}
            className="w-full py-3 text-blue-600 mt-4"
          >
            Open menu again
          </button>
        </div>
      </div>
    );
  }

  // Step 3: Order queued, waiting for arrival
  if (step === 'queued') {
    return (
      <div className="min-h-screen bg-white p-6">
        <div className="max-w-md mx-auto text-center">
          <div className="text-6xl mb-4">🚗</div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Order Queued
          </h1>

          <p className="text-gray-600 mb-6">
            Drive to <strong>{merchant?.name}</strong>.
            <br />
            We'll release your order when you arrive.
          </p>

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-gray-500">Order</div>
            <div className="text-xl font-bold mb-2">#{orderNumber}</div>

            <div className="flex items-center justify-center gap-2 text-sm text-blue-600">
              {polling && (
                <>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                  <span>Detecting arrival...</span>
                </>
              )}
            </div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4 text-sm text-yellow-800">
            <strong>Keep this browser open</strong> while you drive.
            We'll detect when you arrive.
          </div>
        </div>
      </div>
    );
  }

  // Step 4: Order released to kitchen
  if (step === 'released') {
    return (
      <div className="min-h-screen bg-white p-6">
        <div className="max-w-md mx-auto text-center">
          <div className="text-6xl mb-4">✅</div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Order Sent!
          </h1>

          <p className="text-gray-600 mb-6">
            {fulfillment === 'ev_dine_in' ? (
              <>
                Your food is being prepared.
                <br />
                Head to <strong>{merchant?.name}</strong> now!
              </>
            ) : (
              <>
                Your food is being prepared.
                <br />
                Stay at your car — they'll bring it to you.
              </>
            )}
          </p>

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-gray-500">Order #{orderNumber}</div>
            {estimatedReady && (
              <div className="text-lg font-semibold text-green-600 mt-1">
                Ready in ~{estimatedReady} minutes
              </div>
            )}
          </div>

          <button
            onClick={() => navigate('/')}
            className="w-full py-4 bg-gray-100 text-gray-700 rounded-lg font-semibold"
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  return null;
}

function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
    });
  });
}
```

---

## Part 9: Vehicle Color Prompt

One-time setup for Tesla browser users.

**File:** `apps/driver/src/components/EVHome/VehicleSetupPrompt.tsx`

```tsx
import React, { useState } from 'react';
import { api } from '../../services/api';
import { capture, DRIVER_EVENTS } from '../../analytics';

const COLORS = [
  { value: 'white', label: 'White', emoji: '⬜' },
  { value: 'black', label: 'Black', emoji: '⬛' },
  { value: 'blue', label: 'Blue', emoji: '🟦' },
  { value: 'red', label: 'Red', emoji: '🟥' },
  { value: 'silver', label: 'Silver', emoji: '🔘' },
  { value: 'gray', label: 'Gray', emoji: '🩶' },
  { value: 'other', label: 'Other', emoji: '🎨' },
];

interface VehicleSetupPromptProps {
  onComplete: () => void;
}

export function VehicleSetupPrompt({ onComplete }: VehicleSetupPromptProps) {
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!selectedColor) return;

    setLoading(true);
    capture(DRIVER_EVENTS.VEHICLE_COLOR_SET, { color: selectedColor });

    try {
      await api.put('/v1/account/vehicle', {
        color: selectedColor,
        model: 'Tesla', // We know it's a Tesla from browser
      });
      onComplete();
    } catch (error) {
      console.error('Failed to save vehicle:', error);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col justify-center p-6">
      <div className="max-w-md mx-auto text-center">
        <div className="text-5xl mb-4">🚗</div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          One quick thing...
        </h1>

        <p className="text-gray-600 mb-8">
          What color is your Tesla?
          <br />
          <span className="text-sm">
            This helps restaurants find you at the charger.
          </span>
        </p>

        <div className="grid grid-cols-4 gap-3 mb-8">
          {COLORS.map((color) => (
            <button
              key={color.value}
              onClick={() => setSelectedColor(color.value)}
              className={`p-3 rounded-lg border-2 transition-all ${
                selectedColor === color.value
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-1">{color.emoji}</div>
              <div className="text-xs text-gray-600">{color.label}</div>
            </button>
          ))}
        </div>

        <button
          onClick={handleSave}
          disabled={!selectedColor || loading}
          className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg
                     font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Saving...' : 'Continue'}
        </button>
      </div>
    </div>
  );
}
```

---

## Part 10: Implementation Checklist

### Backend Tasks

- [ ] Create `backend/app/utils/ev_browser.py` with detection logic
- [ ] Create `backend/app/routers/ev_context.py` endpoint
- [ ] Add order queuing fields to ArrivalSession model (`order_status`, `destination_lat/lng`, timestamps)
- [ ] Run migration `064_add_queued_order_fields.py`
- [ ] Add `/v1/arrival/{id}/trigger-arrival` endpoint
- [ ] Update merchant notification to include fulfillment type
- [ ] Add Toast polling for order status (optional enhancement)
- [ ] Register new routers in `main.py`
- [ ] Add PostHog events for queuing and arrival

### Frontend Tasks

- [ ] Create `apps/driver/src/utils/evBrowserDetection.ts`
- [ ] Create `useEVContext` hook
- [ ] Create `useArrivalPolling` hook (polls geolocation every 30s)
- [ ] Create `EVHome` component for Tesla-optimized experience
- [ ] Create `VehicleSetupPrompt` component
- [ ] Create `MerchantCard` with fulfillment options (Dine-In / Eat in Car)
- [ ] Create `EVOrderFlow` component with queued state UI
- [ ] Wire up routes in `App.tsx`

### Testing

- [ ] Test user agent detection for Tesla browsers
- [ ] Test order queuing (order not sent to kitchen until arrival)
- [ ] Test arrival polling (geolocation fails while driving, succeeds when parked)
- [ ] Test arrival trigger (order released when within 500m of restaurant)
- [ ] Test EV Dine-In flow end-to-end
- [ ] Test EV Curbside flow end-to-end
- [ ] Test merchant notification content for each flow

---

## Summary

### The Core Flow

```
ORDER PLACED → QUEUED → [DRIVING] → ARRIVAL DETECTED → RELEASED → READY
```

| Stage | What Happens |
|-------|-------------|
| **Order Placed** | Driver selects merchant, places order via Toast/Square |
| **Queued** | Order saved but NOT sent to kitchen |
| **Driving** | Geolocation fails (Tesla safety), browser polls every 30s |
| **Arrival Detected** | Geolocation succeeds + within 500m = arrival |
| **Released** | Order fired to kitchen, merchant notified |
| **Ready** | Food ready, driver picks up or merchant delivers |

### What DoorDash Doesn't Cover

> "I'm about to drive somewhere. I want to order food and have it **ready when I arrive**."

DoorDash times food to delivery driver arrival. We time food to **customer arrival**.

### The Two Fulfillment Options

| Option | Arrival Trigger | Who Moves |
|--------|-----------------|-----------|
| **🍽️ EV Dine-In** | Geolocation within 500m | Driver walks to restaurant |
| **🚗 EV Curbside** | Geolocation within 500m | Merchant brings food to car |

### Technical Approach

| Signal | Source |
|--------|--------|
| **Is it a Tesla?** | User agent (`Tesla/` or `QtCarBrowser`) |
| **Is driver moving?** | Geolocation fails while driving |
| **Has driver arrived?** | Geolocation succeeds + near restaurant |

**The Tesla browser provides all the signals we need.**

### Why This Beats Smartcar

| Aspect | Tesla Browser | Smartcar |
|--------|--------------|----------|
| User friction | Zero | OAuth flow |
| Backend complexity | Moderate (polling hook) | High (Celery, Redis, background jobs) |
| Cost | Free | $2-5/vehicle/month |
| Works immediately | Yes | After OAuth |
| Arrival detection | Geolocation in browser | API polling from server |

### Key Implementation Details

1. **Order is QUEUED** until arrival — kitchen never sees it early
2. **Browser polls every 30 seconds** for geolocation
3. **Geolocation fails while driving** (Tesla safety feature) — this is expected
4. **Geolocation succeeds when parked** — this IS the arrival signal
5. **Within 500m = arrived** — fire order to kitchen
6. **Toast integration** can notify driver when food is ready
