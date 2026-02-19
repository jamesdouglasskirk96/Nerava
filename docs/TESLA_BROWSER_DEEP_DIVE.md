# Tesla In-Car Browser Deep Dive

**Date:** 2026-02-06
**Purpose:** Understand Tesla browser capabilities for EV arrival-aware commerce

---

## Executive Summary

**Yes, we can detect Tesla browsers.** The Tesla in-car browser has distinctive user agent strings that uniquely identify it. Combined with the Geolocation API (supported since firmware v5.9), we can:

1. **Know someone is ordering from a Tesla** → User agent detection
2. **Know they're at a charger** → Geolocation API + our charger database
3. **Know when they arrive at the restaurant** → Geolocation when browser is still open

This is **significantly simpler than Smartcar** — no OAuth, no polling, no background jobs. The driver's browser IS the signal.

---

## Part 1: Tesla Browser Detection

### User Agent Strings

Tesla browsers are **definitively identifiable** via user agent:

#### Modern Tesla (2019+)
```
Mozilla/5.0 (X11; GNU/Linux) AppleWebKit/537.36 (KHTML, like Gecko)
Chromium/88.0.4324.150 Chrome/88.0.4324.150 Safari/537.36
Tesla/2024.44.25-c6d521764ab9
       ^^^^^^^^^^^^^^^^^^^^^^^
       This suffix is the key identifier
```

#### Older Tesla (Pre-2019)
```
Mozilla/5.0 (X11; Linux) AppleWebKit/534.34 (KHTML, like Gecko)
QtCarBrowser Safari/534.34
^^^^^^^^^^^^^
This is the key identifier
```

### Detection Code (Backend)

```python
# backend/app/utils/ev_browser_detection.py

import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class EVBrowserInfo:
    is_ev_browser: bool
    brand: Optional[str] = None
    firmware_version: Optional[str] = None
    raw_user_agent: Optional[str] = None


def detect_ev_browser(user_agent: str) -> EVBrowserInfo:
    """
    Detect if request is from an EV in-car browser.

    Returns EVBrowserInfo with brand and firmware version if detected.
    """
    if not user_agent:
        return EVBrowserInfo(is_ev_browser=False)

    ua_lower = user_agent.lower()

    # Tesla detection (modern firmware)
    tesla_match = re.search(r'Tesla/(\d{4}\.\d+\.\d+(?:\.\d+)?(?:-[a-f0-9]+)?)', user_agent, re.IGNORECASE)
    if tesla_match:
        return EVBrowserInfo(
            is_ev_browser=True,
            brand="Tesla",
            firmware_version=tesla_match.group(1),
            raw_user_agent=user_agent,
        )

    # Tesla detection (older QtCarBrowser)
    if 'qtcarbrowser' in ua_lower:
        return EVBrowserInfo(
            is_ev_browser=True,
            brand="Tesla",
            firmware_version="pre-2019",
            raw_user_agent=user_agent,
        )

    # Polestar / Volvo (Android Automotive with Vivaldi)
    if 'polestar' in ua_lower or ('vivaldi' in ua_lower and 'automotive' in ua_lower):
        return EVBrowserInfo(
            is_ev_browser=True,
            brand="Polestar",
            raw_user_agent=user_agent,
        )

    # Android Automotive OS generic detection
    if 'android automotive' in ua_lower:
        return EVBrowserInfo(
            is_ev_browser=True,
            brand="Android Automotive",
            raw_user_agent=user_agent,
        )

    return EVBrowserInfo(is_ev_browser=False)


def is_tesla_browser(user_agent: str) -> bool:
    """Quick check if request is from Tesla browser."""
    if not user_agent:
        return False
    return 'Tesla/' in user_agent or 'QtCarBrowser' in user_agent
```

### Detection Code (Frontend)

```typescript
// apps/driver/src/utils/evBrowserDetection.ts

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

  // Tesla older
  if (ua.includes('QtCarBrowser')) {
    return {
      isEVBrowser: true,
      brand: 'Tesla',
      firmwareVersion: 'pre-2019',
    };
  }

  // Android Automotive (Polestar, Volvo, etc.)
  if (ua.toLowerCase().includes('android automotive')) {
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

// Quick check
export function isTeslaBrowser(): boolean {
  const ua = navigator.userAgent;
  return ua.includes('Tesla/') || ua.includes('QtCarBrowser');
}
```

---

## Part 2: Geolocation API

### Capability

The Tesla browser **supports the standard Geolocation API** since firmware v5.9 (circa 2014). This means:

```javascript
navigator.geolocation.getCurrentPosition(
  (position) => {
    console.log(position.coords.latitude, position.coords.longitude);
  },
  (error) => {
    console.error(error);
  },
  { enableHighAccuracy: true }
);
```

### Important Behaviors

| Scenario | Geolocation Behavior |
|----------|---------------------|
| **Parked** | ✅ Full access, updates in real-time |
| **Driving** | ⚠️ Location updates stop (safety feature) |
| **Charging** | ✅ Full access (car is parked) |

### Permission Flow

- User gets a **popup asking for permission** to share location
- Permission is **per-site** (not global)
- Once granted, persists until cleared

### HTTPS Requirement

Geolocation requires HTTPS (Chrome 50+). Nerava already uses HTTPS everywhere, so this is not an issue.

---

## Part 3: Browser Behavior While Driving vs Parked

### Parked (Including Charging)

| Feature | Status |
|---------|--------|
| Browser access | ✅ Full |
| Geolocation | ✅ Works |
| Video playback | ✅ Works |
| Audio | ✅ Works |
| Page navigation | ✅ Works |

### Driving

| Feature | Status |
|---------|--------|
| Browser access | ✅ Allowed |
| Geolocation | ⚠️ Updates stop |
| Video playback | ❌ Blocked (screen goes black) |
| Audio | ✅ Continues if started while parked |
| Page navigation | ✅ Works |

### Key Insight

**If a user is actively using the Tesla browser at a location that matches a charger, they are almost certainly parked and charging.**

There's no scenario where someone drives to a charger, parks, and uses the browser without being at the charger.

---

## Part 4: Two User Flows

### Flow 1: Order While Charging → Walk to Restaurant (Dine-In)

```
Driver charges at Supercharger
         │
         ▼
Opens Nerava in Tesla browser
         │
         ▼
We detect: Tesla browser + location = at charger
         │
         ▼
Driver browses nearby restaurants
         │
         ▼
Driver selects restaurant, sees "EV Dine-In" option
         │
         ▼
Driver places order (order is QUEUED, not sent to kitchen)
         │
         ▼
Driver walks to restaurant (~3-5 min)
         │
         ▼
Order is RELEASED when:
  - Driver taps "I've arrived" in app (phone)
  - OR time-based: 5 min after order
  - OR location-based: driver's phone enters restaurant geofence
         │
         ▼
Kitchen fires order → Food ready on arrival
```

### Flow 2: Order While Charging → Drive to Restaurant (Ready on Arrival)

```
Driver charges at Supercharger (e.g., Austin)
         │
         ▼
Opens Nerava in Tesla browser
         │
         ▼
Driver sees restaurant near DESTINATION (e.g., San Antonio)
         │
         ▼
Driver places order (order is QUEUED)
         │
         ▼
Driver finishes charging, starts driving
         │
         ▼
Browser stays open (Tesla displays route/music)
         │
         ▼
Option A: Browser periodically pings for location
  - If geolocation returns (meaning car stopped/parked near restaurant)
  - RELEASE order
         │
Option B: Driver opens phone app when arriving
  - Phone app confirms arrival
  - RELEASE order
         │
Option C: Driver taps "I'm arriving" in car browser
  - Manual confirmation
  - RELEASE order
         │
         ▼
Kitchen fires order → Food ready on arrival
```

---

## Part 5: What We CAN'T Know From Browser Alone

| Data Point | Can We Get It? | Alternative |
|------------|----------------|-------------|
| Vehicle make/model | ❌ Only "Tesla" | Ask driver once |
| Vehicle color | ❌ No | Ask driver once |
| Battery level | ❌ No | Not needed for this flow |
| Charging status | ❌ Not directly | Infer from location at charger |
| ETA to destination | ❌ No | Use distance calculation |

### Vehicle Info Solution

On first order from Tesla browser, prompt:

```
"We noticed you're ordering from your Tesla!
What color is your car? This helps the restaurant find you."

[White] [Black] [Blue] [Red] [Silver] [Gray] [Other]
```

Store this once, reuse for all future orders.

---

## Part 6: Implementation Architecture

### Simplified Flow (No Smartcar Needed)

```
┌─────────────────────────────────────────────────────────────────┐
│                    TESLA IN-CAR BROWSER                         │
│                                                                 │
│  1. User visits app.nerava.network                              │
│  2. Frontend detects Tesla browser (user agent)                 │
│  3. Frontend requests geolocation (user grants permission)      │
│  4. Frontend sends to backend: { lat, lng, is_ev_browser: true }│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                                                                 │
│  1. Receive request with User-Agent header                      │
│  2. detect_ev_browser(user_agent) → { brand: "Tesla", ... }     │
│  3. Match lat/lng to charger database                           │
│  4. If match: "Driver is at [Charger Name], charging"           │
│  5. Show nearby merchants for THAT charger                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORDER CREATION                                │
│                                                                 │
│  ArrivalSession:                                                │
│    - source: "tesla_browser"                                    │
│    - charger_id: detected from location                         │
│    - status: "pending_order"                                    │
│    - trigger_method: "location" | "manual" | "time_based"       │
└─────────────────────────────────────────────────────────────────┘
```

### New API Endpoint

```python
# POST /v1/ev-context
# Called when user opens app from EV browser

class EVContextRequest(BaseModel):
    lat: float
    lng: float
    accuracy_m: Optional[float] = None

class EVContextResponse(BaseModel):
    is_ev_browser: bool
    ev_brand: Optional[str] = None
    at_charger: bool
    charger: Optional[ChargerInfo] = None
    nearby_merchants: List[MerchantInfo]
    suggested_flow: str  # "dine_in" | "ready_on_arrival" | "standard"

@router.post("/v1/ev-context")
async def get_ev_context(
    req: EVContextRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Detect EV browser
    user_agent = request.headers.get("User-Agent", "")
    ev_info = detect_ev_browser(user_agent)

    # Find nearest charger
    charger = find_nearest_charger(db, req.lat, req.lng, max_distance_m=100)

    # Get nearby merchants
    merchants = get_nearby_merchants(
        db,
        charger.lat if charger else req.lat,
        charger.lng if charger else req.lng,
    )

    # Suggest flow based on context
    if ev_info.is_ev_browser and charger:
        suggested_flow = "dine_in"  # They're at charger, likely want to walk
    elif ev_info.is_ev_browser:
        suggested_flow = "ready_on_arrival"  # EV but not at charger
    else:
        suggested_flow = "standard"

    return EVContextResponse(
        is_ev_browser=ev_info.is_ev_browser,
        ev_brand=ev_info.brand,
        at_charger=charger is not None,
        charger=ChargerInfo.from_orm(charger) if charger else None,
        nearby_merchants=merchants,
        suggested_flow=suggested_flow,
    )
```

---

## Part 7: UX Differentiation for EV Browser

### When Detected: Tesla Browser + At Charger

Show optimized experience:

```
┌─────────────────────────────────────────┐
│  ⚡ Charging at Tesla Supercharger       │
│     Canyon Ridge, Austin                 │
│                                         │
│  Your food will be ready when you       │
│  arrive or finish charging.             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ [photo]  Asadas Grill           │    │
│  │          3 min walk             │    │
│  │          ★ 4.5 · Mexican · $$   │    │
│  │                                 │    │
│  │  [Order for Dine-In →]         │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ [photo]  Epoch Coffee           │    │
│  │          5 min walk             │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### One-Time Vehicle Setup (First Order)

```
┌─────────────────────────────────────────┐
│                                         │
│  🚗 One quick thing...                  │
│                                         │
│  What color is your Tesla?              │
│  (Helps the restaurant find you)        │
│                                         │
│  [White] [Black] [Blue] [Red]           │
│  [Silver] [Gray] [Other]                │
│                                         │
│           [Continue →]                  │
│                                         │
└─────────────────────────────────────────┘
```

---

## Part 8: Arrival Trigger Options

### Option 1: Time-Based (Simplest)

```
Order placed → Wait 5 minutes → Release order

Good for: Walk-up dine-in (driver walks to restaurant)
Risk: Driver takes longer than expected
```

### Option 2: Manual Confirmation

```
Driver taps "I'm here" in browser or phone app

Good for: All scenarios
Risk: Driver forgets to tap
```

### Option 3: Phone Geofence (Hybrid)

```
Order placed in Tesla browser
Driver walks with phone in pocket
Phone enters restaurant geofence → Release order

Good for: Dine-in scenarios
Requires: Phone app running in background
```

### Option 4: Browser Location Poll (For Drive-To)

```
Order placed, driver starts driving
Browser periodically requests location (every 30s)
When geolocation succeeds + near restaurant → Release order

Good for: Ready-on-arrival when driver keeps browser open
Risk: Location blocked while driving (Tesla safety feature)
Mitigation: When car parks near restaurant, location becomes available
```

### Recommended Default

**Hybrid approach:**
1. Time-based as fallback (10 min for walk, 30 min for drive)
2. Manual "I'm here" always available
3. Phone geofence if app is installed and running

---

## Part 9: Other EV Browsers

### Currently Detectable

| Brand | Detection Method | Browser Type |
|-------|-----------------|--------------|
| **Tesla** | `Tesla/` or `QtCarBrowser` in UA | Chromium-based |
| **Polestar** | Vivaldi + Automotive identifiers | Chromium-based |
| **Volvo (AAOS)** | Android Automotive identifiers | Chromium-based |

### Not Currently Detectable

| Brand | Reason |
|-------|--------|
| **Rivian** | No built-in browser (as of 2026) |
| **Ford Mach-E** | No accessible browser (captive portal only) |
| **BMW** | Uses CarPlay/Android Auto (runs on phone) |
| **Mercedes** | Proprietary browser, unknown UA |

### Market Reality

Tesla dominates the EV market and has the most capable in-car browser. Starting with Tesla-specific detection covers the majority of use cases. Other brands can be added as their browser capabilities mature.

---

## Part 10: Comparison to Smartcar Approach

| Factor | Tesla Browser | Smartcar |
|--------|--------------|----------|
| Setup required | None | OAuth flow |
| Works offline | No | No |
| Polling needed | No | Yes (every 60s) |
| Backend complexity | Low | High (Celery, Redis) |
| Battery awareness | No | Yes |
| Exact ETA | No | Yes |
| Works while driving | Limited | Yes |
| Cost | Free | $2-5/vehicle/month |
| Privacy concerns | Low | Medium (OAuth scope) |

### Verdict

**Tesla browser detection is the right V1 approach:**
- Zero friction for users
- No OAuth dance
- Works immediately
- Covers majority of EV drivers
- Simple to implement

Smartcar can be added later for:
- Users who want battery-aware triggers
- Users who order from phone but drive Tesla
- Cross-brand EV support

---

## Sources

- [Tesla Browser User Agents - WhatIsMyBrowser.com](https://explore.whatismybrowser.com/useragents/explore/software_name/tesla-browser/)
- [Tesla Car Browser - User Agents.net](https://user-agents.net/browsers/tesla-car-browser)
- [Tesla Forums - Web Browser Geolocation Support](https://forums.tesla.com/forum/forums/web-browser-59-supports-geolocation-api)
- [Tesla Forums - Browser Capabilities](https://forums.tesla.com/forum/forums/tesla-model-s-web-browser-capabilities)
- [Leaflet Issue - Tesla Geolocation](https://github.com/Leaflet/Leaflet/issues/7157)
- [Tesla Motors Club - Browser While Driving](https://teslamotorsclub.com/tmc/threads/useful-browser-websites-while-driving.181669/)
- [Vivaldi for Android Automotive](https://vivaldi.com/android/automotive/)
- [Android Developers - Build Browsers for AAOS](https://developer.android.com/training/cars/parked/browser)
