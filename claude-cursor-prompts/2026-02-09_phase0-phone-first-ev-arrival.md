# Phase 0: Phone-First EV Arrival Implementation

## Overview

Implement a new phone-first EV arrival flow that replaces the current car-first approach. This flow has lower friction, rides existing intent (Google Maps discovery), and gates promo code visibility behind geofence verification.

## The Flow (Read This Carefully)

### Step 1: Discovery & Entry
- Driver discovers merchant via Google Maps → Google Business Profile
- CTA: "EV Arrival / Charging Credit"
- Link: `app.nerava.network/m/{merchant_id}`

### Step 2: Phone Session Creation
- Driver opens `app.nerava.network/m/{merchant_id}` on their phone
- Sees:
  - Merchant name and logo
  - Charging credit offer (e.g., "$5 charging credit")
  - Simple explanation: "Verify EV arrival to unlock charging credit"
- Taps "Check in" button
- Backend creates session with state: `pending`
- Backend returns a random UUID `session_token` (stored in localStorage)

### Step 3: Car Browser Verification
- Driver opens `link.nerava.network` in Tesla/EV browser
- Car browser:
  - Detects EV User-Agent (Tesla, QtCarBrowser, etc.)
  - Generates and displays a one-time PIN (e.g., `N4X-7Q2`)
  - **PIN is stored in a separate `car_pins` table** (not tied to any session yet)
  - PIN is valid for 5 minutes
- Screen shows:
  ```
  Enter this code on your phone:
  N4X-7Q2
  ```

### Step 4: PIN Pairing
- Driver enters PIN on their phone (in the driver app)
- Backend:
  1. Looks up PIN in `car_pins` table
  2. Validates PIN is not expired and not already used
  3. Copies car metadata (user_agent, IP) to the phone session
  4. Marks PIN as used
  5. Updates session state to `car_verified`
- This is EV proof, not identity proof

### Step 5: Arrival & Geofence
- Driver arrives at merchant
- Phone location enters merchant geofence (100-200m radius)
- Session state: `arrived`

### Step 6: Promo Code Reveal
- **ONLY NOW** does Nerava reveal the promo code
- On phone screen only, large and simple:
  ```
  Show this code to the cashier:
  EV-48291
  ```

### Step 7: Redemption
- Driver shows code to cashier
- Merchant applies charging credit/discount
- POS is unchanged (manual entry)
- Merchant can optionally mark as redeemed in their dashboard via `/v1/arrival/redeem`

---

## Non-Negotiables (DO NOT COMPROMISE)

### 1. Promo Code Visibility Rule
```
Promo codes are ONLY revealed when:
- Car browser verified (PIN entered correctly) AND
- Driver is physically inside merchant geofence

No previews. No early exposure. Ever.
```

### 2. Arrival Truth Hierarchy
Arrival is valid if ANY ONE is true:
- Car browser verified recently (within 30 min) + phone at merchant
- Phone location + dwell time (2+ minutes in geofence)
- QR scan at merchant (future)

### 3. Code Security
- Promo codes are short-lived (10 minutes max)
- Promo codes are single-use
- Promo codes are tied to: `merchant_id`, `session_id`, `timestamp`

---

## Database Changes

### Migration 067: Add Phase 0 Fields to ArrivalSession

**File**: `backend/alembic/versions/067_add_phase0_arrival_fields.py`

Add new columns to existing `arrival_sessions` table:

```python
def upgrade():
    # Phone session token (simple UUID, not fingerprint)
    op.add_column('arrival_sessions', sa.Column('phone_session_token', sa.String(64), unique=True))

    # Car verification (copied from car_pins when PIN is verified)
    op.add_column('arrival_sessions', sa.Column('car_verified_at', sa.DateTime()))
    op.add_column('arrival_sessions', sa.Column('car_user_agent', sa.String(512)))
    op.add_column('arrival_sessions', sa.Column('car_ip', sa.String(45)))
    op.add_column('arrival_sessions', sa.Column('pin_attempts', sa.Integer(), server_default='0'))

    # Promo code (only generated after geofence arrival)
    op.add_column('arrival_sessions', sa.Column('promo_code', sa.String(8)))
    op.add_column('arrival_sessions', sa.Column('promo_code_expires_at', sa.DateTime()))
    op.add_column('arrival_sessions', sa.Column('promo_code_revealed_at', sa.DateTime()))

    # Phase 0 state machine (separate from existing status to avoid conflicts)
    op.add_column('arrival_sessions', sa.Column('phase0_state', sa.String(20), server_default='pending'))
    # States: pending → car_verified → arrived → redeemed | expired

    # Indexes
    op.create_index('ix_arrival_sessions_phone_token', 'arrival_sessions', ['phone_session_token'])
    op.create_index('ix_arrival_sessions_promo_code', 'arrival_sessions', ['promo_code'])
    op.create_index('ix_arrival_sessions_phase0_state', 'arrival_sessions', ['phase0_state'])
```

### Migration 068: Create Car PINs Table

**File**: `backend/alembic/versions/068_create_car_pins_table.py`

**IMPORTANT**: PINs are stored separately because the car browser doesn't know about any phone session. The PIN acts as a linking token.

```python
def upgrade():
    op.create_table(
        'car_pins',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('pin', sa.String(7), nullable=False, unique=True),  # Format: XXX-XXX
        sa.Column('user_agent', sa.String(512), nullable=False),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime()),  # NULL = not used yet
        sa.Column('used_by_session_id', sa.UUID(), sa.ForeignKey('arrival_sessions.id')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index('ix_car_pins_pin', 'car_pins', ['pin'])
    op.create_index('ix_car_pins_expires_at', 'car_pins', ['expires_at'])
```

### Migration 069: Add Geofence Radius to Merchants

**File**: `backend/alembic/versions/069_add_merchant_geofence_radius.py`

```python
def upgrade():
    op.add_column('merchants', sa.Column('geofence_radius_m', sa.Integer(), server_default='150'))
```

---

## Backend Implementation

### New Model: CarPin

**File**: `backend/app/models/car_pin.py`

```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid

class CarPin(Base):
    __tablename__ = "car_pins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pin = Column(String(7), unique=True, nullable=False)  # XXX-XXX
    user_agent = Column(String(512), nullable=False)
    ip_address = Column(String(45))
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)  # NULL = available
    used_by_session_id = Column(UUID(as_uuid=True), ForeignKey("arrival_sessions.id"))
    created_at = Column(DateTime, server_default=func.now())

    def is_valid(self) -> bool:
        """Check if PIN is still valid (not expired, not used)"""
        from datetime import datetime
        return self.used_at is None and self.expires_at > datetime.utcnow()
```

### New Service: Arrival Service V2

**File**: `backend/app/services/arrival_service_v2.py`

```python
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.arrival_session import ArrivalSession
from app.models.car_pin import CarPin
from app.models.merchant import Merchant

# PIN alphabet: excludes confusing chars (0, O, I, 1, L)
PIN_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
PIN_TTL_MINUTES = 5
PROMO_CODE_TTL_MINUTES = 10
SESSION_TTL_HOURS = 2
MAX_PIN_ATTEMPTS = 5


def generate_pin() -> str:
    """Generate 6-char PIN in format XXX-XXX"""
    part1 = ''.join(secrets.choice(PIN_ALPHABET) for _ in range(3))
    part2 = ''.join(secrets.choice(PIN_ALPHABET) for _ in range(3))
    return f"{part1}-{part2}"


def generate_promo_code() -> str:
    """Generate promo code in format EV-XXXXX"""
    digits = ''.join(secrets.choice(string.digits) for _ in range(5))
    return f"EV-{digits}"


def generate_session_token() -> str:
    """Generate a random session token (simple UUID, not fingerprint)"""
    return secrets.token_urlsafe(32)


def create_phone_session(db: Session, merchant_id: str) -> Tuple[ArrivalSession, str]:
    """
    Create a new phone session in 'pending' state.
    Returns (session, session_token).
    """
    token = generate_session_token()

    session = ArrivalSession(
        merchant_id=merchant_id,
        phone_session_token=token,
        phase0_state="pending",
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session, token


def create_car_pin(db: Session, user_agent: str, ip_address: str) -> CarPin:
    """
    Generate a new PIN for car browser display.
    PIN is NOT tied to any session yet - it's a standalone record.
    """
    # Generate unique PIN (retry if collision)
    for _ in range(10):
        pin = generate_pin()
        existing = db.query(CarPin).filter(CarPin.pin == pin).first()
        if not existing:
            break
    else:
        raise Exception("Failed to generate unique PIN after 10 attempts")

    car_pin = CarPin(
        pin=pin,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=datetime.utcnow() + timedelta(minutes=PIN_TTL_MINUTES),
    )
    db.add(car_pin)
    db.commit()
    db.refresh(car_pin)

    return car_pin


def verify_pin(db: Session, session_token: str, pin: str) -> Tuple[bool, str, Optional[ArrivalSession]]:
    """
    Verify PIN and link car verification to phone session.

    Returns (success, error_message, session).
    """
    # Find phone session
    session = db.query(ArrivalSession).filter(
        ArrivalSession.phone_session_token == session_token,
        ArrivalSession.phase0_state == "pending",
    ).first()

    if not session:
        return False, "Session not found or already verified", None

    # Check attempt limit
    if session.pin_attempts >= MAX_PIN_ATTEMPTS:
        session.phase0_state = "expired"
        db.commit()
        return False, "Too many attempts. Please start over.", None

    # Increment attempts
    session.pin_attempts = (session.pin_attempts or 0) + 1

    # Find PIN (case-insensitive, normalize format)
    normalized_pin = pin.upper().strip()
    if len(normalized_pin) == 6:
        normalized_pin = f"{normalized_pin[:3]}-{normalized_pin[3:]}"

    car_pin = db.query(CarPin).filter(CarPin.pin == normalized_pin).first()

    if not car_pin:
        db.commit()
        return False, "Invalid code. Please check and try again.", None

    if not car_pin.is_valid():
        db.commit()
        return False, "Code expired. Please get a new code from your car.", None

    # Link car verification to session
    session.car_verified_at = datetime.utcnow()
    session.car_user_agent = car_pin.user_agent
    session.car_ip = car_pin.ip_address
    session.phase0_state = "car_verified"

    # Mark PIN as used
    car_pin.used_at = datetime.utcnow()
    car_pin.used_by_session_id = session.id

    db.commit()
    db.refresh(session)

    return True, "", session


def check_location(
    db: Session,
    session_token: str,
    lat: float,
    lng: float
) -> Tuple[bool, dict]:
    """
    Check if driver has arrived at merchant geofence.
    If arrived, generate and return promo code.

    Returns (arrived, response_dict).
    """
    session = db.query(ArrivalSession).filter(
        ArrivalSession.phone_session_token == session_token,
        ArrivalSession.phase0_state == "car_verified",
    ).first()

    if not session:
        return False, {"error": "Session not found or not ready for location check"}

    merchant = db.query(Merchant).filter(Merchant.id == session.merchant_id).first()
    if not merchant:
        return False, {"error": "Merchant not found"}

    # Calculate distance using haversine
    from app.services.geo import haversine_m
    distance = haversine_m(lat, lng, merchant.latitude, merchant.longitude)

    geofence_radius = merchant.geofence_radius_m or 150

    if distance > geofence_radius:
        return False, {
            "state": "car_verified",
            "arrived": False,
            "distance_m": round(distance),
            "message": f"Drive to {merchant.name} to unlock your credit"
        }

    # ARRIVED! Generate promo code
    promo_code = generate_promo_code()
    promo_expires = datetime.utcnow() + timedelta(minutes=PROMO_CODE_TTL_MINUTES)

    session.phase0_state = "arrived"
    session.arrived_at = datetime.utcnow()
    session.arrival_lat = lat
    session.arrival_lng = lng
    session.promo_code = promo_code
    session.promo_code_expires_at = promo_expires
    session.promo_code_revealed_at = datetime.utcnow()

    db.commit()

    return True, {
        "state": "arrived",
        "arrived": True,
        "promo_code": promo_code,
        "promo_code_expires_at": promo_expires.isoformat(),
        "message": "Show this code to the cashier"
    }


def redeem_promo_code(db: Session, promo_code: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Mark a promo code as redeemed (called by merchant).

    Returns (success, error_message, session_info).
    """
    session = db.query(ArrivalSession).filter(
        ArrivalSession.promo_code == promo_code.upper().strip()
    ).first()

    if not session:
        return False, "Promo code not found", None

    if session.redeemed_at:
        return False, "Already redeemed", {
            "session_id": str(session.id),
            "redeemed_at": session.redeemed_at.isoformat(),
        }

    if session.promo_code_expires_at < datetime.utcnow():
        return False, "Promo code expired", None

    session.redeemed_at = datetime.utcnow()
    session.phase0_state = "redeemed"
    db.commit()

    return True, "", {
        "session_id": str(session.id),
        "merchant_id": str(session.merchant_id),
        "redeemed_at": session.redeemed_at.isoformat(),
    }


def get_session_status(db: Session, session_token: str) -> Optional[dict]:
    """Get current session status for polling."""
    session = db.query(ArrivalSession).filter(
        ArrivalSession.phone_session_token == session_token
    ).first()

    if not session:
        return None

    merchant = db.query(Merchant).filter(Merchant.id == session.merchant_id).first()

    result = {
        "session_id": str(session.id),
        "state": session.phase0_state,
        "merchant": {
            "id": str(merchant.id),
            "name": merchant.name,
            "address": merchant.address,
            "lat": merchant.latitude,
            "lng": merchant.longitude,
            "geofence_radius_m": merchant.geofence_radius_m or 150,
        } if merchant else None,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
    }

    # Only include promo code if state is 'arrived' or 'redeemed'
    if session.phase0_state in ("arrived", "redeemed") and session.promo_code:
        result["promo_code"] = session.promo_code
        result["promo_code_expires_at"] = session.promo_code_expires_at.isoformat()

    return result
```

### New Router: Arrival V2

**File**: `backend/app/routers/arrival_v2.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_db
from app.utils.ev_browser import require_ev_browser
from app.services import arrival_service_v2 as service
from app.models.merchant import Merchant

router = APIRouter(prefix="/v1/arrival", tags=["arrival"])


class StartRequest(BaseModel):
    merchant_id: str


class VerifyPinRequest(BaseModel):
    session_token: str
    pin: str


class CheckLocationRequest(BaseModel):
    session_token: str
    lat: float
    lng: float


class RedeemRequest(BaseModel):
    promo_code: str


@router.post("/start")
def start_session(request: StartRequest, db: Session = Depends(get_db)):
    """
    Start a new phone session for a merchant.
    Called when driver taps "Check In" on merchant page.
    """
    # Validate merchant exists
    merchant = db.query(Merchant).filter(Merchant.id == request.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    session, token = service.create_phone_session(db, request.merchant_id)

    return {
        "session_id": str(session.id),
        "session_token": token,
        "merchant": {
            "id": str(merchant.id),
            "name": merchant.name,
            "logo_url": merchant.logo_url,
            "offer": merchant.ev_offer_text or "$5 charging credit",
            "address": merchant.address,
        },
        "state": "pending",
        "next_step": "verify_car",
    }


@router.post("/car-pin")
def generate_car_pin(request: Request, db: Session = Depends(get_db)):
    """
    Generate a PIN for display in car browser.
    REQUIRES EV browser User-Agent.
    PIN is NOT tied to any session - it's a standalone linking token.
    """
    # Validate EV browser
    user_agent = request.headers.get("user-agent", "")
    require_ev_browser(user_agent)  # Raises 403 if not EV browser

    ip_address = request.client.host if request.client else None

    car_pin = service.create_car_pin(db, user_agent, ip_address)

    return {
        "pin": car_pin.pin,
        "expires_in_seconds": 300,
        "display_message": "Enter this code on your phone",
    }


@router.post("/verify-pin")
def verify_pin(request: VerifyPinRequest, db: Session = Depends(get_db)):
    """
    Verify PIN entered on phone and link car verification to session.
    """
    success, error, session = service.verify_pin(db, request.session_token, request.pin)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    merchant = db.query(Merchant).filter(Merchant.id == session.merchant_id).first()

    return {
        "session_id": str(session.id),
        "state": "car_verified",
        "next_step": "go_to_merchant",
        "merchant": {
            "id": str(merchant.id),
            "name": merchant.name,
            "address": merchant.address,
            "lat": merchant.latitude,
            "lng": merchant.longitude,
            "geofence_radius_m": merchant.geofence_radius_m or 150,
        } if merchant else None,
    }


@router.post("/check-location")
def check_location(request: CheckLocationRequest, db: Session = Depends(get_db)):
    """
    Check if driver has arrived at merchant geofence.
    Called periodically by phone while driver is en route.
    Generates and returns promo code when driver arrives.
    """
    arrived, result = service.check_location(
        db, request.session_token, request.lat, request.lng
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/status")
def get_status(session_token: str, db: Session = Depends(get_db)):
    """
    Get current session status.
    Used for polling and recovering session state.
    """
    result = service.get_session_status(db, session_token)

    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    return result


@router.post("/redeem")
def redeem_code(request: RedeemRequest, db: Session = Depends(get_db)):
    """
    Mark a promo code as redeemed.
    Called by merchant when driver shows code.
    """
    success, error, info = service.redeem_promo_code(db, request.promo_code)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {
        "redeemed": True,
        **info,
    }
```

### Register Router

**File**: `backend/app/main.py`

Add import and registration:
```python
from app.routers import arrival_v2

# In the router registration section:
app.include_router(arrival_v2.router)
```

---

## Frontend: Driver App (`apps/driver/`)

### New Route

**File**: `apps/driver/src/App.tsx`

Add route for merchant-specific entry:
```tsx
import { MerchantArrivalScreen } from './components/EVArrival/MerchantArrivalScreen';

// In Routes:
<Route path="/m/:merchantId" element={<MerchantArrivalScreen />} />
```

### API Service

**File**: `apps/driver/src/services/arrival.ts`

```typescript
const API_BASE = import.meta.env.VITE_API_URL || '';

export interface Merchant {
  id: string;
  name: string;
  logo_url?: string;
  offer?: string;
  address?: string;
  lat?: number;
  lng?: number;
  geofence_radius_m?: number;
}

export interface ArrivalSession {
  session_id: string;
  session_token: string;
  state: 'pending' | 'car_verified' | 'arrived' | 'redeemed' | 'expired';
  merchant: Merchant;
  promo_code?: string;
  promo_code_expires_at?: string;
  expires_at?: string;
}

const SESSION_TOKEN_KEY = 'nerava_arrival_session_token';

export function getStoredSessionToken(): string | null {
  return localStorage.getItem(SESSION_TOKEN_KEY);
}

export function storeSessionToken(token: string): void {
  localStorage.setItem(SESSION_TOKEN_KEY, token);
}

export function clearSessionToken(): void {
  localStorage.removeItem(SESSION_TOKEN_KEY);
}

export async function startSession(merchantId: string): Promise<ArrivalSession> {
  const response = await fetch(`${API_BASE}/v1/arrival/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ merchant_id: merchantId }),
  });

  if (!response.ok) {
    throw new Error('Failed to start session');
  }

  const data = await response.json();
  storeSessionToken(data.session_token);
  return data;
}

export async function verifyPin(sessionToken: string, pin: string): Promise<ArrivalSession> {
  const response = await fetch(`${API_BASE}/v1/arrival/verify-pin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_token: sessionToken, pin }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Invalid code');
  }

  return response.json();
}

export async function checkLocation(
  sessionToken: string,
  lat: number,
  lng: number
): Promise<{ arrived: boolean; distance_m?: number; promo_code?: string; message?: string }> {
  const response = await fetch(`${API_BASE}/v1/arrival/check-location`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_token: sessionToken, lat, lng }),
  });

  if (!response.ok) {
    throw new Error('Failed to check location');
  }

  return response.json();
}

export async function getSessionStatus(sessionToken: string): Promise<ArrivalSession | null> {
  const response = await fetch(`${API_BASE}/v1/arrival/status?session_token=${sessionToken}`);

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error('Failed to get session status');
  }

  return response.json();
}
```

### Location Polling Hook

**File**: `apps/driver/src/hooks/useArrivalLocationPolling.ts`

```typescript
import { useEffect, useRef, useState } from 'react';
import { checkLocation } from '../services/arrival';

interface PollingResult {
  arrived: boolean;
  distance_m?: number;
  promo_code?: string;
  promo_code_expires_at?: string;
  error?: string;
}

export function useArrivalLocationPolling(
  sessionToken: string | null,
  isActive: boolean,
  intervalMs: number = 10000
): PollingResult {
  const [result, setResult] = useState<PollingResult>({ arrived: false });
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (!sessionToken || !isActive) {
      return;
    }

    const poll = async () => {
      try {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 10000,
          });
        });

        const response = await checkLocation(
          sessionToken,
          position.coords.latitude,
          position.coords.longitude
        );

        setResult({
          arrived: response.arrived,
          distance_m: response.distance_m,
          promo_code: response.promo_code,
        });
      } catch (error) {
        setResult(prev => ({ ...prev, error: String(error) }));
      }
    };

    // Poll immediately, then on interval
    poll();
    intervalRef.current = window.setInterval(poll, intervalMs);

    // Also poll on visibility change (app comes back to foreground)
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        poll();
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }
      document.removeEventListener('visibilitychange', handleVisibility);
    };
  }, [sessionToken, isActive, intervalMs]);

  return result;
}
```

### Main Screen Component

**File**: `apps/driver/src/components/EVArrival/MerchantArrivalScreen.tsx`

```tsx
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  ArrivalSession,
  getStoredSessionToken,
  getSessionStatus,
  startSession,
} from '../../services/arrival';
import { CheckInPrompt } from './CheckInPrompt';
import { VerifyCarPrompt } from './VerifyCarPrompt';
import { GoToMerchantScreen } from './GoToMerchantScreen';
import { PromoCodeScreen } from './PromoCodeScreen';
import { ThankYouScreen } from './ThankYouScreen';
import { ErrorScreen } from './ErrorScreen';

export function MerchantArrivalScreen() {
  const { merchantId } = useParams<{ merchantId: string }>();
  const [session, setSession] = useState<ArrivalSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check for existing session on mount
  useEffect(() => {
    async function checkExistingSession() {
      const token = getStoredSessionToken();
      if (token) {
        try {
          const existingSession = await getSessionStatus(token);
          if (existingSession && existingSession.merchant?.id === merchantId) {
            setSession(existingSession);
          }
        } catch (e) {
          // Session expired or invalid, continue with new flow
        }
      }
      setLoading(false);
    }
    checkExistingSession();
  }, [merchantId]);

  const handleCheckIn = async () => {
    if (!merchantId) return;

    try {
      setLoading(true);
      const newSession = await startSession(merchantId);
      setSession(newSession);
    } catch (e) {
      setError('Failed to start check-in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePinVerified = (updatedSession: ArrivalSession) => {
    setSession(updatedSession);
  };

  const handleArrived = (promoCode: string, expiresAt: string) => {
    setSession(prev => prev ? {
      ...prev,
      state: 'arrived',
      promo_code: promoCode,
      promo_code_expires_at: expiresAt,
    } : null);
  };

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (error) {
    return <ErrorScreen message={error} onRetry={() => setError(null)} />;
  }

  if (!session) {
    return (
      <CheckInPrompt
        merchantId={merchantId!}
        onCheckIn={handleCheckIn}
      />
    );
  }

  switch (session.state) {
    case 'pending':
      return (
        <VerifyCarPrompt
          session={session}
          onVerified={handlePinVerified}
        />
      );

    case 'car_verified':
      return (
        <GoToMerchantScreen
          session={session}
          onArrived={handleArrived}
        />
      );

    case 'arrived':
      return (
        <PromoCodeScreen
          promoCode={session.promo_code!}
          expiresAt={session.promo_code_expires_at!}
          merchantName={session.merchant.name}
        />
      );

    case 'redeemed':
      return <ThankYouScreen merchantName={session.merchant.name} />;

    case 'expired':
    default:
      return (
        <ErrorScreen
          message="Your session has expired. Please start over."
          onRetry={() => {
            setSession(null);
          }}
        />
      );
  }
}
```

### Component: CheckInPrompt

**File**: `apps/driver/src/components/EVArrival/CheckInPrompt.tsx`

```tsx
import { useEffect, useState } from 'react';
import { Merchant } from '../../services/arrival';

interface Props {
  merchantId: string;
  onCheckIn: () => void;
}

export function CheckInPrompt({ merchantId, onCheckIn }: Props) {
  const [merchant, setMerchant] = useState<Merchant | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch merchant info for display
    async function fetchMerchant() {
      try {
        const response = await fetch(`/v1/merchants/${merchantId}`);
        if (response.ok) {
          setMerchant(await response.json());
        }
      } finally {
        setLoading(false);
      }
    }
    fetchMerchant();
  }, [merchantId]);

  if (loading) {
    return <div className="loading">Loading merchant...</div>;
  }

  return (
    <div className="checkin-prompt">
      {merchant?.logo_url && (
        <img src={merchant.logo_url} alt={merchant.name} className="merchant-logo" />
      )}

      <h1>{merchant?.name || 'Merchant'}</h1>

      <div className="offer-card">
        <span className="offer-label">EV Driver Offer</span>
        <span className="offer-value">{merchant?.offer || '$5 charging credit'}</span>
      </div>

      <p className="instructions">
        Verify your EV arrival to unlock your charging credit
      </p>

      <button onClick={onCheckIn} className="checkin-button">
        Check In
      </button>
    </div>
  );
}
```

### Component: VerifyCarPrompt

**File**: `apps/driver/src/components/EVArrival/VerifyCarPrompt.tsx`

```tsx
import { useState } from 'react';
import { ArrivalSession, verifyPin, getStoredSessionToken } from '../../services/arrival';

interface Props {
  session: ArrivalSession;
  onVerified: (session: ArrivalSession) => void;
}

export function VerifyCarPrompt({ session, onVerified }: Props) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const token = getStoredSessionToken();
      if (!token) throw new Error('Session not found');

      const updatedSession = await verifyPin(token, pin);
      onVerified(updatedSession);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  const formatPin = (value: string): string => {
    // Auto-format as XXX-XXX
    const clean = value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
    if (clean.length > 3) {
      return `${clean.slice(0, 3)}-${clean.slice(3)}`;
    }
    return clean;
  };

  return (
    <div className="verify-car-prompt">
      <h1>Verify Your EV</h1>

      <div className="instructions">
        <div className="step">
          <span className="step-number">1</span>
          <span>Open <strong>link.nerava.network</strong> in your car browser</span>
        </div>
        <div className="step">
          <span className="step-number">2</span>
          <span>Enter the code shown on your car screen below</span>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={pin}
          onChange={(e) => setPin(formatPin(e.target.value))}
          placeholder="XXX-XXX"
          className="pin-input"
          maxLength={7}
          autoComplete="off"
          autoFocus
        />

        {error && <div className="error-message">{error}</div>}

        <button type="submit" disabled={pin.length < 7 || loading}>
          {loading ? 'Verifying...' : 'Verify'}
        </button>
      </form>
    </div>
  );
}
```

### Component: GoToMerchantScreen

**File**: `apps/driver/src/components/EVArrival/GoToMerchantScreen.tsx`

```tsx
import { useEffect } from 'react';
import { ArrivalSession, getStoredSessionToken } from '../../services/arrival';
import { useArrivalLocationPolling } from '../../hooks/useArrivalLocationPolling';

interface Props {
  session: ArrivalSession;
  onArrived: (promoCode: string, expiresAt: string) => void;
}

export function GoToMerchantScreen({ session, onArrived }: Props) {
  const token = getStoredSessionToken();
  const pollingResult = useArrivalLocationPolling(token, true);

  useEffect(() => {
    if (pollingResult.arrived && pollingResult.promo_code) {
      onArrived(pollingResult.promo_code, pollingResult.promo_code_expires_at || '');
    }
  }, [pollingResult.arrived, pollingResult.promo_code]);

  const merchant = session.merchant;

  return (
    <div className="go-to-merchant">
      <div className="verified-badge">
        <span className="checkmark">✓</span>
        EV Verified
      </div>

      <h1>Head to {merchant.name}</h1>

      <p className="address">{merchant.address}</p>

      {pollingResult.distance_m !== undefined && (
        <div className="distance">
          {pollingResult.distance_m < 1000
            ? `${pollingResult.distance_m}m away`
            : `${(pollingResult.distance_m / 1000).toFixed(1)}km away`}
        </div>
      )}

      <div className="waiting-message">
        <div className="spinner" />
        <p>Your charging credit will unlock when you arrive</p>
      </div>

      {merchant.lat && merchant.lng && (
        <a
          href={`https://maps.google.com/?daddr=${merchant.lat},${merchant.lng}`}
          target="_blank"
          rel="noopener noreferrer"
          className="directions-button"
        >
          Get Directions
        </a>
      )}
    </div>
  );
}
```

### Component: PromoCodeScreen

**File**: `apps/driver/src/components/EVArrival/PromoCodeScreen.tsx`

```tsx
import { useEffect, useState } from 'react';

interface Props {
  promoCode: string;
  expiresAt: string;
  merchantName: string;
}

export function PromoCodeScreen({ promoCode, expiresAt, merchantName }: Props) {
  const [timeLeft, setTimeLeft] = useState<string>('');

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date().getTime();
      const expires = new Date(expiresAt).getTime();
      const diff = expires - now;

      if (diff <= 0) {
        setTimeLeft('Expired');
        return;
      }

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeLeft(`${minutes}:${seconds.toString().padStart(2, '0')}`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [expiresAt]);

  return (
    <div className="promo-code-screen">
      <div className="success-badge">
        <span className="checkmark">✓</span>
        You've arrived!
      </div>

      <h1>Show this code to the cashier</h1>

      <div className="promo-code-display">
        {promoCode}
      </div>

      <p className="expires-label">
        Expires in <strong>{timeLeft}</strong>
      </p>

      <div className="merchant-info">
        <p>At {merchantName}</p>
      </div>
    </div>
  );
}
```

### Component: ThankYouScreen

**File**: `apps/driver/src/components/EVArrival/ThankYouScreen.tsx`

```tsx
interface Props {
  merchantName: string;
}

export function ThankYouScreen({ merchantName }: Props) {
  return (
    <div className="thank-you-screen">
      <div className="success-icon">🎉</div>

      <h1>Credit Applied!</h1>

      <p>Thanks for visiting {merchantName}</p>

      <p className="secondary">Your charging credit has been applied.</p>
    </div>
  );
}
```

### Component: ErrorScreen

**File**: `apps/driver/src/components/EVArrival/ErrorScreen.tsx`

```tsx
interface Props {
  message: string;
  onRetry?: () => void;
}

export function ErrorScreen({ message, onRetry }: Props) {
  return (
    <div className="error-screen">
      <div className="error-icon">⚠️</div>

      <h1>Something went wrong</h1>

      <p>{message}</p>

      {onRetry && (
        <button onClick={onRetry} className="retry-button">
          Try Again
        </button>
      )}
    </div>
  );
}
```

---

## Frontend: Link App (`apps/link/`)

### Complete Rewrite

**File**: `apps/link/src/App.tsx`

```tsx
import { useEffect, useState } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface PinResponse {
  pin: string;
  expires_in_seconds: number;
  display_message: string;
}

export default function App() {
  const [pin, setPin] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expiresIn, setExpiresIn] = useState<number>(300);
  const [loading, setLoading] = useState(true);

  const generatePin = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/v1/arrival/car-pin`, {
        method: 'POST',
      });

      if (response.status === 403) {
        setError('This page only works in your car browser');
        setLoading(false);
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to generate code');
      }

      const data: PinResponse = await response.json();
      setPin(data.pin);
      setExpiresIn(data.expires_in_seconds);
    } catch (e) {
      setError('Failed to generate code. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  // Generate PIN on mount
  useEffect(() => {
    generatePin();
  }, []);

  // Countdown timer
  useEffect(() => {
    if (!pin || expiresIn <= 0) return;

    const timer = setInterval(() => {
      setExpiresIn((prev) => {
        if (prev <= 1) {
          // Auto-refresh when expired
          generatePin();
          return 300;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [pin]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading && !pin) {
    return (
      <div className="container">
        <img src="/nerava-logo.png" alt="Nerava" className="logo" />
        <div className="loading">Generating code...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container error-container">
        <img src="/nerava-logo.png" alt="Nerava" className="logo" />
        <h1>EV Browser Required</h1>
        <p className="error-message">{error}</p>
        <p className="help-text">
          Open this page in your Tesla or EV car browser to get your check-in code.
        </p>
      </div>
    );
  }

  return (
    <div className="container">
      <img src="/nerava-logo.png" alt="Nerava" className="logo" />

      <h1>Enter this code on your phone</h1>

      <div className="pin-display">{pin}</div>

      <p className="expires">
        Expires in {formatTime(expiresIn)}
      </p>

      <button onClick={generatePin} className="refresh-button" disabled={loading}>
        {loading ? 'Generating...' : 'Get New Code'}
      </button>
    </div>
  );
}
```

### Styling

**File**: `apps/link/src/App.css`

```css
/* Tesla browser optimized: dark theme, high contrast, large touch targets */

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: #000;
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  min-height: 100vh;
}

.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.logo {
  width: 120px;
  height: auto;
  margin-bottom: 40px;
}

h1 {
  font-size: 28px;
  font-weight: 500;
  margin-bottom: 40px;
  color: #fff;
}

.pin-display {
  font-size: 96px;
  font-weight: 700;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  letter-spacing: 8px;
  color: #00D4AA;
  margin-bottom: 24px;
  padding: 20px 40px;
  background: rgba(0, 212, 170, 0.1);
  border-radius: 16px;
  border: 2px solid rgba(0, 212, 170, 0.3);
}

.expires {
  font-size: 18px;
  color: #888;
  margin-bottom: 40px;
}

.refresh-button {
  padding: 16px 40px;
  font-size: 18px;
  font-weight: 500;
  background: #333;
  color: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.refresh-button:hover:not(:disabled) {
  background: #444;
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Error state */
.error-container h1 {
  color: #ff6b6b;
}

.error-message {
  font-size: 20px;
  color: #ff6b6b;
  margin-bottom: 20px;
}

.help-text {
  font-size: 16px;
  color: #888;
  max-width: 400px;
  line-height: 1.5;
}

/* Loading state */
.loading {
  font-size: 20px;
  color: #888;
}

/* Responsive for smaller car screens */
@media (max-width: 600px) {
  .pin-display {
    font-size: 64px;
    letter-spacing: 4px;
    padding: 16px 24px;
  }

  h1 {
    font-size: 22px;
  }
}
```

### API Contract Validation (Optional)

**File**: `apps/link/src/contract.ts`

```typescript
// Simple runtime validation for API responses

export interface CarPinResponse {
  pin: string;
  expires_in_seconds: number;
  display_message: string;
}

export function validateCarPinResponse(data: unknown): data is CarPinResponse {
  if (typeof data !== 'object' || data === null) return false;

  const obj = data as Record<string, unknown>;

  return (
    typeof obj.pin === 'string' &&
    obj.pin.length === 7 &&
    typeof obj.expires_in_seconds === 'number' &&
    obj.expires_in_seconds > 0 &&
    typeof obj.display_message === 'string'
  );
}
```

---

## Security Considerations

### 1. PIN Security
- PIN alphabet: 32 chars (excludes 0, O, I, 1, L)
- 6 characters = 32^6 = ~1 billion combinations
- Max 5 verification attempts per phone session
- PIN expires in 5 minutes
- PIN is single-use (marked as `used_at` after verification)

### 2. Session Token Security
- Simple random UUID (not browser fingerprint - more reliable)
- Stored in localStorage
- 2-hour expiration
- Tied to specific merchant

### 3. Promo Code Security
- Generated server-side ONLY after geofence verification
- Format: EV-XXXXX (5 digits = 100,000 combinations)
- Expires in 10 minutes
- Single-use (marked as `redeemed_at`)
- Tied to session_id

### 4. Rate Limiting
- `/car-pin`: 10 PINs per hour per IP
- `/verify-pin`: 5 attempts per session
- `/start`: 10 sessions per hour per IP

### 5. EV Browser Validation
- Requires `Tesla/` or `QtCarBrowser` in User-Agent
- Returns 403 for non-EV browsers
- Logs all User-Agents for fraud analysis

---

## Testing Checklist

### Unit Tests
- [ ] PIN generation produces valid XXX-XXX format
- [ ] PIN alphabet excludes confusing characters
- [ ] Promo code generation produces valid EV-XXXXX format
- [ ] Geofence calculation is accurate (test with known coordinates)
- [ ] State transitions are valid (pending → car_verified → arrived → redeemed)
- [ ] PIN expiry is enforced
- [ ] Promo code expiry is enforced

### Integration Tests
- [ ] Full flow: start → car_verified → arrived → redeemed
- [ ] PIN attempt limiting (6th attempt fails session)
- [ ] Promo code not revealed before geofence arrival
- [ ] Session expiry after 2 hours
- [ ] EV browser detection (Tesla UA passes, Chrome UA fails)
- [ ] PIN uniqueness (no collisions)

### E2E Tests
- [ ] Driver app flow on mobile Safari
- [ ] Driver app flow on mobile Chrome
- [ ] Link app in simulated Tesla browser (custom User-Agent)
- [ ] Location polling updates state correctly
- [ ] Promo code display only after geofence
- [ ] Session recovery on page refresh

---

## Files to Create/Modify

### Backend
- [ ] `backend/alembic/versions/067_add_phase0_arrival_fields.py` - Migration
- [ ] `backend/alembic/versions/068_create_car_pins_table.py` - Migration
- [ ] `backend/alembic/versions/069_add_merchant_geofence_radius.py` - Migration
- [ ] `backend/app/models/car_pin.py` - New model
- [ ] `backend/app/services/arrival_service_v2.py` - Core business logic
- [ ] `backend/app/routers/arrival_v2.py` - New endpoints
- [ ] `backend/app/main.py` - Register router

### Driver App (`apps/driver/`)
- [ ] `src/App.tsx` - Add `/m/:merchantId` route
- [ ] `src/services/arrival.ts` - API client
- [ ] `src/hooks/useArrivalLocationPolling.ts` - Location polling hook
- [ ] `src/components/EVArrival/MerchantArrivalScreen.tsx` - Main screen
- [ ] `src/components/EVArrival/CheckInPrompt.tsx` - Check-in prompt
- [ ] `src/components/EVArrival/VerifyCarPrompt.tsx` - PIN entry
- [ ] `src/components/EVArrival/GoToMerchantScreen.tsx` - Directions + polling
- [ ] `src/components/EVArrival/PromoCodeScreen.tsx` - Promo code display
- [ ] `src/components/EVArrival/ThankYouScreen.tsx` - Confirmation
- [ ] `src/components/EVArrival/ErrorScreen.tsx` - Error handling

### Link App (`apps/link/`)
- [ ] `src/App.tsx` - Complete rewrite to PIN display
- [ ] `src/App.css` - Tesla-optimized styling
- [ ] `src/contract.ts` - API response validation

---

## Success Criteria

1. Driver can complete full flow in < 2 minutes
2. Promo code is NEVER visible before geofence arrival
3. PIN entry has < 3% error rate
4. Session expiry and fraud prevention work correctly
5. Works on Safari iOS, Chrome Android
6. Works in Tesla browser (verified User-Agent)
7. PIN linking works correctly (car PIN → phone session)
