# Cursor Prompt: Smartcar + Canonical EV Arrival Model Implementation

**Date:** 2026-02-06
**Status:** Implementation-ready — 8-phase sprint plan
**Canonical Model Version:** LOCKED

---

## PART 1: CANONICAL MODEL INTERNALIZATION

### Core Principle (Non-Negotiable)

> **Arrival is the invariant. Charging state and order timing are modifiers.**

You are implementing infrastructure for EV Arrival-aware commerce. The system times merchant fulfillment based on **verified driver arrival** (or completion of charging), NOT on order time or estimated prep time.

### Driver Mental Model (Must Preserve)

The driver understands exactly one thing:

> "Nerava times my food to when I arrive or finish charging."

The driver does NOT think about:
- Charger availability
- Kitchen timing
- Fulfillment logistics
- Curbside vs dine-in decision trees

**Those are merchant-side concerns abstracted away.**

### Canonical Flow (Do Not Alter Structure)

```
Step 1 — Before departure (ORDER QUEUED)
├── Driver may order before leaving (e.g., Dallas → San Antonio)
├── Order is created in pending_arrival state
└── Kitchen does NOT fire yet

Step 2 — Arrival-aware trigger (ARRIVAL VERIFIED)
├── Arrival detected via ANY combination of:
│   ├── Smartcar ETA convergence (NEW)
│   ├── Smartcar location within geofence (NEW)
│   ├── Physical presence on site (existing geofence)
│   ├── Charger queue / on-site confirmation
├── Arrival ≠ plugged in
├── Order flips from scheduled → active
└── This is "Ready on Arrival"

Step 3 — Fulfillment (merchant-defined)
├── Walk-in pickup (default)
├── Eat in car (delivery to charger)
└── Dine inside

Step 4 — Ready After Charge (SAME SYSTEM)
├── Trigger fires on charging completion OR target SoC (e.g. 80%)
├── All fulfillment logic identical
└── Symmetry is intentional
```

### Why Arrival Beats Charging or Ordering

| System | Failure Mode |
|--------|--------------|
| Order-time | Cold food, kitchen misalignment, cancellations |
| Charge-time | Charger availability variance, plug-in delays, congestion |
| **Arrival-based** | Observable, verifiable, correlates with intent |

### Constraint Enforcement (CRITICAL)

- **Arrival is the source of truth**
- Merchants CANNOT arbitrarily fire orders early
- No manual overrides that break arrival integrity
- Charging is a timing modifier, not the anchor

---

## PART 2: EXISTING SYSTEM UNDERSTANDING

### Current ArrivalSession Model (`backend/app/models/arrival_session.py`)

```python
class ArrivalSession(Base):
    __tablename__ = "arrival_sessions"

    # Core identifiers
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    charger_id = Column(String, ForeignKey("chargers.id"), nullable=True)

    # Mode: 'ev_curbside' or 'ev_dine_in'
    arrival_type = Column(String(20), nullable=False)

    # Order binding (existing)
    order_number = Column(String(100), nullable=True)
    order_source = Column(String(20), nullable=True)  # 'manual', 'toast', 'square'
    order_total_cents = Column(Integer, nullable=True)
    order_status = Column(String(20), nullable=True)
    driver_estimate_cents = Column(Integer, nullable=True)
    merchant_reported_total_cents = Column(Integer, nullable=True)
    total_source = Column(String(20), nullable=True)

    # Vehicle (copied at session creation)
    vehicle_color = Column(String(30), nullable=True)
    vehicle_model = Column(String(60), nullable=True)

    # Status lifecycle
    status = Column(String(30), nullable=False, default="pending_order")
    # pending_order → awaiting_arrival → arrived → merchant_notified → completed
    # Terminal: expired, canceled, completed_unbillable

    # Timestamps
    created_at, order_bound_at, geofence_entered_at
    merchant_notified_at, merchant_confirmed_at, completed_at, expires_at

    # Geofence (existing)
    arrival_lat, arrival_lng, arrival_accuracy_m

    # Billing
    platform_fee_bps = 500  # 5%
    billable_amount_cents, billing_status
```

### Current API Endpoints (`backend/app/routers/arrival.py`)

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `POST /v1/arrival/create` | Create session | ✅ Implemented |
| `PUT /v1/arrival/{id}/order` | Bind order number | ✅ Implemented |
| `POST /v1/arrival/{id}/confirm-arrival` | Geofence trigger | ✅ Implemented |
| `POST /v1/arrival/{id}/merchant-confirm` | Merchant confirms delivery | ✅ Implemented |
| `POST /v1/arrival/{id}/feedback` | Driver feedback | ✅ Implemented |
| `GET /v1/arrival/active` | Get active session | ✅ Implemented |
| `POST /v1/arrival/{id}/cancel` | Cancel session | ✅ Implemented |

### Current Frontend Components (`apps/driver/src/components/EVArrival/`)

| Component | Built | Wired to App |
|-----------|-------|--------------|
| `ModeSelector.tsx` | ✅ | ❌ Not connected |
| `VehicleSetup.tsx` | ✅ | ❌ Not connected |
| `ConfirmationSheet.tsx` | ✅ | ❌ Not connected |
| `ActiveSession.tsx` | ✅ | ❌ Not connected |
| `CompletionScreen.tsx` | ✅ | ❌ Not connected |

### Gap: Smartcar Integration

Currently, arrival is detected only via:
- Manual "I'm at the charger" button (web)
- Geofence via native iOS bridge

**Smartcar enables:**
1. **Real-time ETA convergence** — Know driver is 5 min away
2. **Battery/SoC monitoring** — Fire order when charging done
3. **Verified vehicle data** — Auto-populate vehicle make/model/color
4. **No GPS spoofing** — Smartcar location is OEM-verified

---

## PART 3: SMARTCAR IMPLEMENTATION PHASES

### Phase 1: Enable Smartcar + Verify OAuth Locally (1 hr)

**Goal:** Smartcar OAuth flow works end-to-end in development.

#### 1.1 Environment Setup

Create/update `backend/.env`:

```bash
# Smartcar credentials (get from dashboard.smartcar.com)
SMARTCAR_CLIENT_ID=your_client_id
SMARTCAR_CLIENT_SECRET=your_client_secret
SMARTCAR_REDIRECT_URI=http://localhost:8000/v1/smartcar/callback

# Mode: 'test' for Smartcar simulator, 'live' for real vehicles
SMARTCAR_MODE=test
```

Add to `backend/app/core/config.py`:

```python
# Smartcar
SMARTCAR_CLIENT_ID: str = ""
SMARTCAR_CLIENT_SECRET: str = ""
SMARTCAR_REDIRECT_URI: str = "http://localhost:8000/v1/smartcar/callback"
SMARTCAR_MODE: str = "test"  # 'test' or 'live'
```

#### 1.2 Install Smartcar SDK

Add to `backend/requirements.txt`:

```
smartcar==5.5.0
```

#### 1.3 Create Smartcar Service

**File:** `backend/app/services/smartcar_service.py`

```python
"""
Smartcar integration service.

Handles OAuth, vehicle data retrieval, and location/battery polling.
This is the primary signal source for arrival-based triggering.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

import smartcar
from smartcar import AuthClient, Vehicle
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.smartcar_token import SmartcarToken

logger = logging.getLogger(__name__)


class SmartcarService:
    """
    Smartcar vehicle integration.

    Core capabilities:
    1. OAuth flow (connect vehicle)
    2. Location polling (arrival detection)
    3. Battery/SoC polling (charge completion trigger)
    4. Vehicle info (auto-populate make/model)
    """

    def __init__(self):
        self.client = AuthClient(
            client_id=settings.SMARTCAR_CLIENT_ID,
            client_secret=settings.SMARTCAR_CLIENT_SECRET,
            redirect_uri=settings.SMARTCAR_REDIRECT_URI,
            mode=settings.SMARTCAR_MODE,
        )

    def get_auth_url(self, user_id: int, scope: list[str] = None) -> str:
        """
        Generate OAuth URL for user to connect their vehicle.

        Default scope includes location, battery, and vehicle info.
        """
        if scope is None:
            scope = [
                "read_location",      # For arrival detection
                "read_battery",       # For charge completion trigger
                "read_vehicle_info",  # Auto-populate make/model
                "read_odometer",      # Optional: trip tracking
            ]

        return self.client.get_auth_url(scope=scope, state=str(user_id))

    async def exchange_code(self, code: str, db: Session, user_id: int) -> SmartcarToken:
        """
        Exchange OAuth code for access token.
        Store encrypted tokens in database.
        """
        access = self.client.exchange_code(code)

        # Get list of connected vehicles
        vehicle_ids = smartcar.get_vehicles(access.access_token).vehicles

        if not vehicle_ids:
            raise ValueError("No vehicles found on this Smartcar account")

        # For now, use first vehicle (multi-vehicle support is Phase 2+)
        primary_vehicle_id = vehicle_ids[0]

        # Store token
        token = SmartcarToken(
            user_id=user_id,
            access_token=access.access_token,  # TODO: Encrypt with Fernet
            refresh_token=access.refresh_token,
            expires_at=access.expiration,
            vehicle_id=primary_vehicle_id,
        )

        db.add(token)
        db.commit()
        db.refresh(token)

        # Fetch and cache vehicle info
        await self._cache_vehicle_info(token, db, user_id)

        logger.info(f"Smartcar connected for user {user_id}, vehicle {primary_vehicle_id}")
        return token

    async def _cache_vehicle_info(self, token: SmartcarToken, db: Session, user_id: int):
        """
        Fetch vehicle make/model and cache on user profile.
        This auto-populates the vehicle setup screen.
        """
        try:
            vehicle = Vehicle(token.vehicle_id, token.access_token)
            attrs = vehicle.attributes()

            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.vehicle_model = f"{attrs.make} {attrs.model}"
                # Color not available from Smartcar — driver enters manually
                user.vehicle_set_at = datetime.utcnow()
                db.commit()

                logger.info(f"Cached vehicle info for user {user_id}: {attrs.make} {attrs.model}")
        except Exception as e:
            logger.warning(f"Failed to cache vehicle info: {e}")

    async def get_location(self, token: SmartcarToken) -> Optional[dict]:
        """
        Get current vehicle location.
        Returns: {"lat": float, "lng": float, "timestamp": datetime}

        This is the primary signal for geofence-based arrival detection.
        """
        try:
            self._maybe_refresh_token(token)
            vehicle = Vehicle(token.vehicle_id, token.access_token)
            loc = vehicle.location()

            return {
                "lat": loc.latitude,
                "lng": loc.longitude,
                "timestamp": datetime.utcnow(),
            }
        except smartcar.exceptions.SmartcarException as e:
            logger.warning(f"Smartcar location failed: {e}")
            return None

    async def get_battery(self, token: SmartcarToken) -> Optional[dict]:
        """
        Get battery state (SoC and range).
        Returns: {"percent_remaining": float, "range_km": float}

        Used for "Ready After Charge" trigger.
        """
        try:
            self._maybe_refresh_token(token)
            vehicle = Vehicle(token.vehicle_id, token.access_token)
            battery = vehicle.battery()

            return {
                "percent_remaining": battery.percent_remaining,
                "range_km": battery.range,
            }
        except smartcar.exceptions.SmartcarException as e:
            logger.warning(f"Smartcar battery failed: {e}")
            return None

    def _maybe_refresh_token(self, token: SmartcarToken):
        """Refresh access token if expired or expiring soon."""
        if token.expires_at and token.expires_at < datetime.utcnow() + timedelta(minutes=5):
            try:
                new_access = self.client.exchange_refresh_token(token.refresh_token)
                token.access_token = new_access.access_token
                token.refresh_token = new_access.refresh_token
                token.expires_at = new_access.expiration
                # Note: Caller must commit the db session
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                raise


# Singleton instance
_smartcar_service: Optional[SmartcarService] = None

def get_smartcar_service() -> SmartcarService:
    global _smartcar_service
    if _smartcar_service is None:
        _smartcar_service = SmartcarService()
    return _smartcar_service
```

#### 1.4 Create SmartcarToken Model

**File:** `backend/app/models/smartcar_token.py`

```python
"""
SmartcarToken model — stores OAuth tokens for connected vehicles.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from ..db import Base
from ..core.uuid_type import UUIDType


class SmartcarToken(Base):
    """
    Smartcar OAuth tokens for a user's connected vehicle.

    One token per user (multi-vehicle support deferred).
    Tokens are refreshed automatically before expiry.
    """
    __tablename__ = "smartcar_tokens"

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # OAuth tokens (TODO: encrypt with Fernet like POS credentials)
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Primary connected vehicle
    vehicle_id = Column(String(100), nullable=False)  # Smartcar vehicle ID

    # Cached vehicle info (for display)
    vehicle_make = Column(String(50), nullable=True)
    vehicle_model = Column(String(50), nullable=True)
    vehicle_year = Column(Integer, nullable=True)

    # Status
    is_active = Column(String(10), default="active")  # 'active', 'revoked', 'error'
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="smartcar_token")

    __table_args__ = (
        Index("idx_smartcar_user", "user_id"),
        Index("idx_smartcar_vehicle", "vehicle_id"),
    )
```

#### 1.5 Create Smartcar OAuth Endpoints

**File:** `backend/app/routers/smartcar.py`

```python
"""
Smartcar OAuth Router — /v1/smartcar/*

Handles vehicle connection OAuth flow.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.models.smartcar_token import SmartcarToken
from app.dependencies.driver import get_current_driver
from app.services.smartcar_service import get_smartcar_service
from app.services.analytics import get_analytics_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/smartcar", tags=["smartcar"])


@router.get("/connect")
async def initiate_connect(
    driver: User = Depends(get_current_driver),
):
    """
    Start Smartcar OAuth flow.
    Returns URL to redirect user to Smartcar authorization.
    """
    service = get_smartcar_service()
    auth_url = service.get_auth_url(driver.id)

    return {"auth_url": auth_url}


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),  # user_id
    db: Session = Depends(get_db),
):
    """
    Smartcar OAuth callback.
    Exchanges code for tokens, stores in database.
    Redirects back to app.
    """
    try:
        user_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    service = get_smartcar_service()

    try:
        token = await service.exchange_code(code, db, user_id)

        # Track analytics
        try:
            analytics = get_analytics_client()
            if analytics:
                analytics.capture(
                    distinct_id=str(user_id),
                    event="smartcar.connected",
                    properties={
                        "vehicle_id": token.vehicle_id,
                    },
                )
        except Exception:
            pass

        # Redirect back to app
        # TODO: Use deep link for native app
        return RedirectResponse(
            url="https://app.nerava.network/smartcar-success",
            status_code=302,
        )

    except Exception as e:
        logger.error(f"Smartcar OAuth failed for user {user_id}: {e}")
        return RedirectResponse(
            url="https://app.nerava.network/smartcar-error",
            status_code=302,
        )


@router.get("/status")
async def get_connection_status(
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """
    Check if user has connected a vehicle via Smartcar.
    """
    token = (
        db.query(SmartcarToken)
        .filter(
            SmartcarToken.user_id == driver.id,
            SmartcarToken.is_active == "active",
        )
        .first()
    )

    if not token:
        return {
            "connected": False,
            "vehicle": None,
        }

    return {
        "connected": True,
        "vehicle": {
            "id": token.vehicle_id,
            "make": token.vehicle_make,
            "model": token.vehicle_model,
            "year": token.vehicle_year,
        },
    }


@router.post("/disconnect")
async def disconnect_vehicle(
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """
    Disconnect Smartcar vehicle.
    Revokes tokens and marks as inactive.
    """
    token = (
        db.query(SmartcarToken)
        .filter(SmartcarToken.user_id == driver.id)
        .first()
    )

    if not token:
        raise HTTPException(status_code=404, detail="No connected vehicle")

    token.is_active = "revoked"
    db.commit()

    logger.info(f"Smartcar disconnected for user {driver.id}")

    return {"ok": True}
```

#### 1.6 Database Migration

**File:** `backend/alembic/versions/064_add_smartcar_tokens_table.py`

```python
"""Add smartcar_tokens table

Revision ID: 064
Revises: 063
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '064'
down_revision = '063'  # Update to actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'smartcar_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('access_token', sa.String(500), nullable=False),
        sa.Column('refresh_token', sa.String(500), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('vehicle_id', sa.String(100), nullable=False),
        sa.Column('vehicle_make', sa.String(50), nullable=True),
        sa.Column('vehicle_model', sa.String(50), nullable=True),
        sa.Column('vehicle_year', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.String(10), server_default='active'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    op.create_index('idx_smartcar_user', 'smartcar_tokens', ['user_id'])
    op.create_index('idx_smartcar_vehicle', 'smartcar_tokens', ['vehicle_id'])


def downgrade():
    op.drop_index('idx_smartcar_vehicle')
    op.drop_index('idx_smartcar_user')
    op.drop_table('smartcar_tokens')
```

#### 1.7 Register Router in main.py

Add to `backend/app/main.py`:

```python
from app.routers import smartcar

app.include_router(smartcar.router)
```

---

### Phase 2: CheckinSession Model + Migration (1 hr)

**Goal:** Extend ArrivalSession to support Smartcar-based arrival detection.

#### 2.1 Extend ArrivalSession Model

Add these columns to `ArrivalSession` in `backend/app/models/arrival_session.py`:

```python
# Smartcar integration fields
smartcar_enabled = Column(Boolean, default=False)
smartcar_vehicle_id = Column(String(100), nullable=True)

# Arrival detection method
arrival_source = Column(String(20), nullable=True)  # 'smartcar', 'geofence', 'manual'

# Smartcar polling state
smartcar_last_location_at = Column(DateTime, nullable=True)
smartcar_last_location_lat = Column(Float, nullable=True)
smartcar_last_location_lng = Column(Float, nullable=True)
smartcar_eta_minutes = Column(Integer, nullable=True)

# Ready After Charge fields
target_soc_percent = Column(Integer, nullable=True)  # e.g., 80
smartcar_last_battery_at = Column(DateTime, nullable=True)
smartcar_last_battery_percent = Column(Float, nullable=True)
charge_complete_trigger = Column(Boolean, default=False)  # True = trigger on charge complete
```

#### 2.2 Migration

**File:** `backend/alembic/versions/065_add_smartcar_fields_to_arrival_sessions.py`

```python
"""Add Smartcar fields to arrival_sessions

Revision ID: 065
Revises: 064
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa

revision = '065'
down_revision = '064'
branch_labels = None
depends_on = None


def upgrade():
    # Smartcar integration fields
    op.add_column('arrival_sessions', sa.Column('smartcar_enabled', sa.Boolean(), server_default='false'))
    op.add_column('arrival_sessions', sa.Column('smartcar_vehicle_id', sa.String(100), nullable=True))
    op.add_column('arrival_sessions', sa.Column('arrival_source', sa.String(20), nullable=True))

    # Smartcar polling state
    op.add_column('arrival_sessions', sa.Column('smartcar_last_location_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('smartcar_last_location_lat', sa.Float(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('smartcar_last_location_lng', sa.Float(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('smartcar_eta_minutes', sa.Integer(), nullable=True))

    # Ready After Charge fields
    op.add_column('arrival_sessions', sa.Column('target_soc_percent', sa.Integer(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('smartcar_last_battery_at', sa.DateTime(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('smartcar_last_battery_percent', sa.Float(), nullable=True))
    op.add_column('arrival_sessions', sa.Column('charge_complete_trigger', sa.Boolean(), server_default='false'))

    # Index for polling job
    op.create_index(
        'idx_arrival_smartcar_active',
        'arrival_sessions',
        ['smartcar_enabled', 'status'],
        postgresql_where=sa.text("smartcar_enabled = true AND status IN ('pending_order', 'awaiting_arrival')")
    )


def downgrade():
    op.drop_index('idx_arrival_smartcar_active')
    op.drop_column('arrival_sessions', 'charge_complete_trigger')
    op.drop_column('arrival_sessions', 'smartcar_last_battery_percent')
    op.drop_column('arrival_sessions', 'smartcar_last_battery_at')
    op.drop_column('arrival_sessions', 'target_soc_percent')
    op.drop_column('arrival_sessions', 'smartcar_eta_minutes')
    op.drop_column('arrival_sessions', 'smartcar_last_location_lng')
    op.drop_column('arrival_sessions', 'smartcar_last_location_lat')
    op.drop_column('arrival_sessions', 'smartcar_last_location_at')
    op.drop_column('arrival_sessions', 'arrival_source')
    op.drop_column('arrival_sessions', 'smartcar_vehicle_id')
    op.drop_column('arrival_sessions', 'smartcar_enabled')
```

---

### Phase 3: Backend Checkin Endpoint (2 hr)

**Goal:** Arrival detection via Smartcar polling instead of manual confirmation.

#### 3.1 Add Smartcar-Aware Create Endpoint

Update `POST /v1/arrival/create` in `backend/app/routers/arrival.py`:

```python
class CreateArrivalRequest(BaseModel):
    merchant_id: str
    charger_id: Optional[str] = None
    arrival_type: str = Field(..., pattern="^(ev_curbside|ev_dine_in)$")
    lat: float
    lng: float
    accuracy_m: Optional[float] = None
    idempotency_key: Optional[str] = None

    # NEW: Smartcar options
    use_smartcar: bool = False  # Enable Smartcar polling for this session
    target_soc_percent: Optional[int] = None  # Ready After Charge target (e.g., 80)
    charge_complete_trigger: bool = False  # Fire on charge complete instead of arrival


@router.post("/create", status_code=201, response_model=CreateArrivalResponse)
async def create_arrival(
    req: CreateArrivalRequest,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """Create a new EV Arrival session."""
    # ... existing validation ...

    # Check for Smartcar token if requested
    smartcar_vehicle_id = None
    if req.use_smartcar:
        smartcar_token = (
            db.query(SmartcarToken)
            .filter(
                SmartcarToken.user_id == driver.id,
                SmartcarToken.is_active == "active",
            )
            .first()
        )
        if not smartcar_token:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "SMARTCAR_NOT_CONNECTED",
                    "message": "Connect your vehicle first to use Smartcar tracking",
                },
            )
        smartcar_vehicle_id = smartcar_token.vehicle_id

    # ... existing session creation ...

    session = ArrivalSession(
        # ... existing fields ...

        # NEW: Smartcar fields
        smartcar_enabled=req.use_smartcar,
        smartcar_vehicle_id=smartcar_vehicle_id,
        target_soc_percent=req.target_soc_percent,
        charge_complete_trigger=req.charge_complete_trigger,
    )

    # ... rest of endpoint ...
```

#### 3.2 Add Smartcar Status Check Endpoint

Add to `backend/app/routers/arrival.py`:

```python
class SmartcarStatusResponse(BaseModel):
    session_id: str
    smartcar_enabled: bool
    last_location: Optional[dict] = None
    eta_minutes: Optional[int] = None
    last_battery: Optional[dict] = None
    arrival_detected: bool = False
    charge_complete: bool = False


@router.get("/{session_id}/smartcar-status", response_model=SmartcarStatusResponse)
async def get_smartcar_status(
    session_id: str,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """
    Get Smartcar tracking status for a session.
    Useful for UI to show real-time ETA and battery state.
    """
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    if not session or session.driver_id != driver.id:
        raise HTTPException(status_code=404, detail="Session not found")

    last_location = None
    if session.smartcar_last_location_lat and session.smartcar_last_location_lng:
        last_location = {
            "lat": session.smartcar_last_location_lat,
            "lng": session.smartcar_last_location_lng,
            "timestamp": session.smartcar_last_location_at.isoformat() if session.smartcar_last_location_at else None,
        }

    last_battery = None
    if session.smartcar_last_battery_percent is not None:
        last_battery = {
            "percent": session.smartcar_last_battery_percent,
            "timestamp": session.smartcar_last_battery_at.isoformat() if session.smartcar_last_battery_at else None,
        }

    # Check if arrival or charge complete was triggered
    arrival_detected = session.status in ("arrived", "merchant_notified", "completed", "completed_unbillable")
    charge_complete = (
        session.charge_complete_trigger
        and session.smartcar_last_battery_percent
        and session.target_soc_percent
        and session.smartcar_last_battery_percent >= session.target_soc_percent
    )

    return SmartcarStatusResponse(
        session_id=str(session.id),
        smartcar_enabled=session.smartcar_enabled,
        last_location=last_location,
        eta_minutes=session.smartcar_eta_minutes,
        last_battery=last_battery,
        arrival_detected=arrival_detected,
        charge_complete=charge_complete,
    )
```

---

### Phase 4: Background Polling Job (3 hr)

**Goal:** Celery worker polls Smartcar every 60 seconds for active sessions.

#### 4.1 Install Celery

Add to `backend/requirements.txt`:

```
celery[redis]==5.3.6
redis==5.0.1
```

#### 4.2 Create Celery App

**File:** `backend/app/celery_app.py`

```python
"""
Celery application for background jobs.
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "nerava",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=["app.jobs.smartcar_polling"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Beat schedule for periodic tasks
    beat_schedule={
        "poll-smartcar-every-60s": {
            "task": "app.jobs.smartcar_polling.poll_active_sessions",
            "schedule": 60.0,  # Every 60 seconds
        },
        "expire-stale-sessions-every-60s": {
            "task": "app.jobs.session_expiry.expire_stale_sessions",
            "schedule": 60.0,
        },
    },
)
```

#### 4.3 Create Smartcar Polling Job

**File:** `backend/app/jobs/smartcar_polling.py`

```python
"""
Smartcar polling background job.

Polls vehicle location/battery for active sessions with Smartcar enabled.
Triggers arrival or charge-complete when conditions are met.
"""
import logging
from datetime import datetime

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models.arrival_session import ArrivalSession, ACTIVE_STATUSES
from app.models.smartcar_token import SmartcarToken
from app.models.while_you_charge import Charger
from app.services.smartcar_service import get_smartcar_service
from app.services.geo import haversine_m
from app.services.notification_service import notify_merchant
from app.services.analytics import get_analytics_client
from app.models.merchant_notification_config import MerchantNotificationConfig
from app.models.while_you_charge import Merchant

logger = logging.getLogger(__name__)

ARRIVAL_RADIUS_M = 250  # Trigger arrival if within 250m of charger


@celery_app.task(name="app.jobs.smartcar_polling.poll_active_sessions")
def poll_active_sessions():
    """
    Poll Smartcar for all active sessions with smartcar_enabled=True.

    For each session:
    1. Fetch vehicle location
    2. Check if within arrival radius of charger
    3. If arrival detected, trigger arrival flow (notify merchant)
    4. If charge_complete_trigger, also check battery SoC
    """
    db = SessionLocal()
    smartcar_service = get_smartcar_service()

    try:
        # Get all active sessions with Smartcar enabled
        sessions = (
            db.query(ArrivalSession)
            .filter(
                ArrivalSession.smartcar_enabled == True,
                ArrivalSession.status.in_(["pending_order", "awaiting_arrival"]),
            )
            .all()
        )

        logger.info(f"Polling {len(sessions)} Smartcar-enabled sessions")

        for session in sessions:
            try:
                _poll_session(db, smartcar_service, session)
            except Exception as e:
                logger.error(f"Error polling session {session.id}: {e}")

        db.commit()

    finally:
        db.close()


def _poll_session(db, smartcar_service, session: ArrivalSession):
    """Poll a single session's vehicle."""

    # Get Smartcar token for driver
    token = (
        db.query(SmartcarToken)
        .filter(
            SmartcarToken.user_id == session.driver_id,
            SmartcarToken.is_active == "active",
        )
        .first()
    )

    if not token:
        logger.warning(f"No Smartcar token for session {session.id}")
        return

    now = datetime.utcnow()

    # Fetch location
    import asyncio
    location = asyncio.get_event_loop().run_until_complete(
        smartcar_service.get_location(token)
    )

    if location:
        session.smartcar_last_location_at = now
        session.smartcar_last_location_lat = location["lat"]
        session.smartcar_last_location_lng = location["lng"]

        # Check proximity to charger
        if session.charger_id:
            charger = db.query(Charger).filter(Charger.id == session.charger_id).first()
            if charger:
                distance_m = haversine_m(
                    location["lat"], location["lng"],
                    charger.lat, charger.lng
                )

                # Calculate rough ETA (assumes 30 mph average)
                if distance_m > ARRIVAL_RADIUS_M:
                    eta_minutes = int(distance_m / 800)  # ~800m/min at 30mph
                    session.smartcar_eta_minutes = max(eta_minutes, 1)
                else:
                    session.smartcar_eta_minutes = 0

                # Trigger arrival if within radius
                if distance_m <= ARRIVAL_RADIUS_M:
                    logger.info(f"Smartcar arrival detected for session {session.id}")
                    _trigger_arrival(db, session, "smartcar", location["lat"], location["lng"])

    # Check battery if charge_complete_trigger is enabled
    if session.charge_complete_trigger and session.target_soc_percent:
        battery = asyncio.get_event_loop().run_until_complete(
            smartcar_service.get_battery(token)
        )

        if battery:
            session.smartcar_last_battery_at = now
            session.smartcar_last_battery_percent = battery["percent_remaining"]

            # Trigger if SoC target reached
            if battery["percent_remaining"] >= session.target_soc_percent:
                logger.info(f"Charge complete for session {session.id}: {battery['percent_remaining']}%")

                # Only trigger if not already triggered
                if session.status in ("pending_order", "awaiting_arrival"):
                    _trigger_arrival(db, session, "smartcar_charge_complete",
                                    session.smartcar_last_location_lat,
                                    session.smartcar_last_location_lng)

    # Commit token refresh if it happened
    db.commit()


def _trigger_arrival(db, session: ArrivalSession, source: str, lat: float, lng: float):
    """
    Trigger arrival for a session.
    This is the canonical arrival trigger — whether from Smartcar, geofence, or manual.
    """
    now = datetime.utcnow()

    session.arrival_lat = lat
    session.arrival_lng = lng
    session.arrival_source = source
    session.geofence_entered_at = now
    session.status = "arrived"

    # Send merchant notification
    notif_config = (
        db.query(MerchantNotificationConfig)
        .filter(MerchantNotificationConfig.merchant_id == session.merchant_id)
        .first()
    )

    if notif_config:
        merchant = db.query(Merchant).filter(Merchant.id == session.merchant_id).first()
        charger = db.query(Charger).filter(Charger.id == session.charger_id).first()

        # Run notification async
        import asyncio
        notification_method = asyncio.get_event_loop().run_until_complete(
            notify_merchant(
                notify_sms=notif_config.notify_sms,
                notify_email=notif_config.notify_email,
                sms_phone=notif_config.sms_phone,
                email_address=notif_config.email_address,
                order_number=session.order_number or "N/A",
                arrival_type=session.arrival_type,
                vehicle_color=session.vehicle_color,
                vehicle_model=session.vehicle_model,
                charger_name=charger.name if charger else None,
                merchant_name=merchant.name if merchant else "",
                merchant_reply_code=session.merchant_reply_code or "",
            )
        )

        if notification_method != "none":
            session.status = "merchant_notified"
            session.merchant_notified_at = now

    # Analytics
    try:
        analytics = get_analytics_client()
        if analytics:
            analytics.capture(
                distinct_id=str(session.driver_id),
                event="ev_arrival.smartcar_triggered",
                properties={
                    "session_id": str(session.id),
                    "merchant_id": session.merchant_id,
                    "arrival_source": source,
                },
            )
    except Exception:
        pass

    logger.info(f"Arrival triggered for session {session.id} via {source}")
```

#### 4.4 Session Expiry Job

**File:** `backend/app/jobs/session_expiry.py`

```python
"""
Session expiry background job.

Marks stale sessions as expired.
"""
import logging
from datetime import datetime

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models.arrival_session import ArrivalSession, ACTIVE_STATUSES
from app.services.analytics import get_analytics_client

logger = logging.getLogger(__name__)


@celery_app.task(name="app.jobs.session_expiry.expire_stale_sessions")
def expire_stale_sessions():
    """
    Expire sessions that have passed their expires_at timestamp.
    """
    db = SessionLocal()

    try:
        now = datetime.utcnow()

        expired_sessions = (
            db.query(ArrivalSession)
            .filter(
                ArrivalSession.status.in_(ACTIVE_STATUSES),
                ArrivalSession.expires_at < now,
            )
            .all()
        )

        for session in expired_sessions:
            session.status = "expired"
            session.completed_at = now

            logger.info(f"Expired session {session.id}")

            # Analytics
            try:
                analytics = get_analytics_client()
                if analytics:
                    analytics.capture(
                        distinct_id=str(session.driver_id),
                        event="ev_arrival.expired",
                        properties={
                            "session_id": str(session.id),
                            "merchant_id": session.merchant_id,
                        },
                    )
            except Exception:
                pass

        db.commit()
        logger.info(f"Expired {len(expired_sessions)} stale sessions")

    finally:
        db.close()
```

---

### Phase 5: ETA Pre-Notification (1 hr)

**Goal:** Notify merchant when driver is ~5 minutes away (optional feature).

Add to polling job:

```python
ETA_PRENOTIFY_MINUTES = 5

def _poll_session(db, smartcar_service, session: ArrivalSession):
    # ... existing location polling ...

    # Pre-notify merchant when ETA <= 5 minutes
    if (
        session.smartcar_eta_minutes
        and session.smartcar_eta_minutes <= ETA_PRENOTIFY_MINUTES
        and session.status == "awaiting_arrival"
        and not session.merchant_notified_at  # Not already notified
    ):
        logger.info(f"Sending ETA pre-notification for session {session.id}")
        _send_eta_prenotification(db, session)


def _send_eta_prenotification(db, session: ArrivalSession):
    """Send "driver arriving soon" notification to merchant."""
    notif_config = (
        db.query(MerchantNotificationConfig)
        .filter(MerchantNotificationConfig.merchant_id == session.merchant_id)
        .first()
    )

    if not notif_config or not notif_config.notify_sms:
        return

    # Don't mark as merchant_notified yet — that's for actual arrival
    # This is a heads-up notification
    from app.services.notification_service import send_eta_notification

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        send_eta_notification(
            phone=notif_config.sms_phone,
            order_number=session.order_number or "N/A",
            eta_minutes=session.smartcar_eta_minutes,
            vehicle_model=session.vehicle_model,
            vehicle_color=session.vehicle_color,
        )
    )
```

---

### Phase 6: Smartcar-First Onboarding UI (2 hr)

**Goal:** Guide users to connect Smartcar during first session creation.

#### 6.1 Frontend Component

**File:** `apps/driver/src/components/SmartcarConnect/SmartcarConnect.tsx`

```tsx
/**
 * SmartcarConnect — Vehicle connection flow.
 *
 * Shows when user tries to create arrival with Smartcar but hasn't connected.
 * Provides OAuth flow to connect vehicle.
 */
import React, { useState } from 'react';
import { Button } from '../shared/Button';
import { api } from '../../services/api';
import { capture, DRIVER_EVENTS } from '../../analytics';

interface SmartcarConnectProps {
  onConnected: () => void;
  onSkip: () => void;
}

export function SmartcarConnect({ onConnected, onSkip }: SmartcarConnectProps) {
  const [loading, setLoading] = useState(false);

  const handleConnect = async () => {
    setLoading(true);
    capture(DRIVER_EVENTS.SMARTCAR_CONNECT_STARTED, {});

    try {
      const response = await api.get('/v1/smartcar/connect');
      const { auth_url } = response.data;

      // Open Smartcar OAuth in new tab/window
      // On mobile, this will open in-app browser
      window.location.href = auth_url;

    } catch (error) {
      console.error('Smartcar connect error:', error);
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="text-center space-y-2">
        <div className="text-4xl">🚗</div>
        <h2 className="text-xl font-semibold text-gray-900">
          Connect Your Vehicle
        </h2>
        <p className="text-gray-600 text-sm">
          Nerava uses your vehicle's location to time your order perfectly.
          We'll know exactly when you're arriving — no manual check-in needed.
        </p>
      </div>

      <div className="bg-blue-50 rounded-lg p-4 space-y-2">
        <h3 className="font-medium text-blue-900">What we access:</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>✓ Vehicle location (for arrival detection)</li>
          <li>✓ Battery level (for "ready after charge")</li>
          <li>✓ Vehicle make/model (to help merchants find you)</li>
        </ul>
        <p className="text-xs text-blue-700 mt-2">
          We never control your vehicle. Read-only access only.
        </p>
      </div>

      <div className="space-y-3">
        <Button
          onClick={handleConnect}
          loading={loading}
          className="w-full"
        >
          Connect with Smartcar
        </Button>

        <button
          onClick={onSkip}
          className="w-full text-sm text-gray-500 hover:text-gray-700"
        >
          Skip for now (use manual check-in)
        </button>
      </div>

      <p className="text-xs text-gray-400 text-center">
        Works with Tesla, Ford, BMW, Rivian, and 30+ other brands via Smartcar.
      </p>
    </div>
  );
}
```

#### 6.2 Integration in EV Arrival Flow

Update `apps/driver/src/components/EVArrival/ConfirmationSheet.tsx`:

```tsx
import { SmartcarConnect } from '../SmartcarConnect/SmartcarConnect';

export function ConfirmationSheet({ merchant, onConfirm, onCancel }) {
  const [showSmartcarConnect, setShowSmartcarConnect] = useState(false);
  const [smartcarConnected, setSmartcarConnected] = useState(false);
  const [useSmartcar, setUseSmartcar] = useState(true);

  // Check Smartcar status on mount
  useEffect(() => {
    checkSmartcarStatus();
  }, []);

  const checkSmartcarStatus = async () => {
    try {
      const response = await api.get('/v1/smartcar/status');
      setSmartcarConnected(response.data.connected);
    } catch {
      setSmartcarConnected(false);
    }
  };

  const handleConfirm = () => {
    if (useSmartcar && !smartcarConnected) {
      setShowSmartcarConnect(true);
      return;
    }

    onConfirm({ useSmartcar });
  };

  if (showSmartcarConnect) {
    return (
      <SmartcarConnect
        onConnected={() => {
          setSmartcarConnected(true);
          setShowSmartcarConnect(false);
          onConfirm({ useSmartcar: true });
        }}
        onSkip={() => {
          setShowSmartcarConnect(false);
          onConfirm({ useSmartcar: false });
        }}
      />
    );
  }

  return (
    <div className="p-6 space-y-4">
      {/* ... existing confirmation UI ... */}

      {/* Smartcar toggle */}
      <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
        <input
          type="checkbox"
          checked={useSmartcar}
          onChange={(e) => setUseSmartcar(e.target.checked)}
          className="w-4 h-4 text-blue-600"
        />
        <div>
          <div className="text-sm font-medium text-gray-900">
            Auto-detect my arrival
          </div>
          <div className="text-xs text-gray-500">
            {smartcarConnected
              ? "Using connected vehicle"
              : "Connect your vehicle to enable"}
          </div>
        </div>
      </label>

      <Button onClick={handleConfirm} className="w-full">
        {useSmartcar ? "Confirm EV Arrival" : "Confirm (Manual Check-in)"}
      </Button>
    </div>
  );
}
```

---

### Phase 7: CheckInModal Component (2 hr)

**Goal:** Modal showing real-time ETA and battery from Smartcar.

**File:** `apps/driver/src/components/EVArrival/SmartcarStatus.tsx`

```tsx
/**
 * SmartcarStatus — Real-time vehicle tracking display.
 *
 * Shows:
 * - Current ETA to charger
 * - Battery level / charging progress
 * - Arrival status
 */
import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';

interface SmartcarStatusProps {
  sessionId: string;
  onArrivalDetected?: () => void;
}

interface StatusData {
  smartcar_enabled: boolean;
  eta_minutes: number | null;
  last_location: { lat: number; lng: number; timestamp: string } | null;
  last_battery: { percent: number; timestamp: string } | null;
  arrival_detected: boolean;
  charge_complete: boolean;
}

export function SmartcarStatus({ sessionId, onArrivalDetected }: SmartcarStatusProps) {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Poll status every 10 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await api.get(`/v1/arrival/${sessionId}/smartcar-status`);
        setStatus(response.data);

        if (response.data.arrival_detected && onArrivalDetected) {
          onArrivalDetected();
        }
      } catch (err) {
        console.error('Smartcar status error:', err);
        setError('Unable to get vehicle status');
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // 10s polling

    return () => clearInterval(interval);
  }, [sessionId, onArrivalDetected]);

  if (!status || !status.smartcar_enabled) {
    return null;
  }

  return (
    <div className="bg-blue-50 rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-blue-600">🚗</span>
        <span className="text-sm font-medium text-blue-900">
          Vehicle Tracking Active
        </span>
      </div>

      {/* ETA Display */}
      {status.eta_minutes !== null && status.eta_minutes > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-blue-800">ETA to charger</span>
          <span className="text-lg font-semibold text-blue-900">
            {status.eta_minutes} min
          </span>
        </div>
      )}

      {status.eta_minutes === 0 && !status.arrival_detected && (
        <div className="text-sm text-green-600 font-medium">
          📍 Near charger — detecting arrival...
        </div>
      )}

      {status.arrival_detected && (
        <div className="text-sm text-green-600 font-medium">
          ✅ Arrival confirmed — merchant notified
        </div>
      )}

      {/* Battery Display */}
      {status.last_battery && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-blue-800">Battery</span>
          <div className="flex items-center gap-2">
            <div className="w-20 h-2 bg-blue-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all duration-500"
                style={{ width: `${status.last_battery.percent}%` }}
              />
            </div>
            <span className="text-sm font-medium text-blue-900">
              {Math.round(status.last_battery.percent)}%
            </span>
          </div>
        </div>
      )}

      {status.charge_complete && (
        <div className="text-sm text-green-600 font-medium">
          ⚡ Charge complete — order ready!
        </div>
      )}

      {error && (
        <div className="text-xs text-red-600">{error}</div>
      )}
    </div>
  );
}
```

Update `ActiveSession.tsx` to include `SmartcarStatus`:

```tsx
import { SmartcarStatus } from './SmartcarStatus';

export function ActiveSession({ session, onOrderBound, onComplete }) {
  // ... existing code ...

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-xl font-semibold">EV Arrival Active</h2>
        <p className="text-gray-600">{session.merchant_name} · {session.arrival_type}</p>
      </div>

      {/* Smartcar Status (NEW) */}
      {session.smartcar_enabled && (
        <SmartcarStatus
          sessionId={session.session_id}
          onArrivalDetected={() => {
            // Refresh session to get updated status
            refreshSession();
          }}
        />
      )}

      {/* ... rest of existing UI ... */}
    </div>
  );
}
```

---

### Phase 8: Wire EVArrival Components to App (2 hr)

**Goal:** Connect all EVArrival components to the driver app.

#### 8.1 Add Route

Update `apps/driver/src/App.tsx`:

```tsx
import { EVArrivalFlow } from './components/EVArrival/EVArrivalFlow';

// Add route
<Route path="/arrival" element={<EVArrivalFlow />} />
<Route path="/arrival/:sessionId" element={<EVArrivalFlow />} />
```

#### 8.2 Create Flow Orchestrator

**File:** `apps/driver/src/components/EVArrival/EVArrivalFlow.tsx`

```tsx
/**
 * EVArrivalFlow — Main orchestrator for EV Arrival UX.
 *
 * Manages state machine:
 * 1. Mode selection (curbside/dine-in)
 * 2. Vehicle setup (if needed)
 * 3. Confirmation
 * 4. Active session
 * 5. Completion + feedback
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ModeSelector } from './ModeSelector';
import { VehicleSetup } from './VehicleSetup';
import { ConfirmationSheet } from './ConfirmationSheet';
import { ActiveSession } from './ActiveSession';
import { CompletionScreen } from './CompletionScreen';
import { api } from '../../services/api';
import { capture, DRIVER_EVENTS } from '../../analytics';

type FlowStep = 'mode' | 'vehicle' | 'confirm' | 'active' | 'complete';

export function EVArrivalFlow() {
  const { sessionId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [step, setStep] = useState<FlowStep>('mode');
  const [arrivalType, setArrivalType] = useState<'ev_curbside' | 'ev_dine_in'>('ev_curbside');
  const [merchantId, setMerchantId] = useState<string | null>(searchParams.get('merchant'));
  const [merchant, setMerchant] = useState<any>(null);
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Check for existing active session on mount
  useEffect(() => {
    checkActiveSession();
  }, []);

  const checkActiveSession = async () => {
    try {
      const response = await api.get('/v1/arrival/active');
      if (response.data.session) {
        setSession(response.data.session);
        setStep('active');
      }
    } catch (error) {
      console.error('Check active session error:', error);
    }
  };

  // Load merchant details if merchantId provided
  useEffect(() => {
    if (merchantId) {
      loadMerchant(merchantId);
    }
  }, [merchantId]);

  const loadMerchant = async (id: string) => {
    try {
      const response = await api.get(`/v1/merchants/${id}`);
      setMerchant(response.data);
    } catch (error) {
      console.error('Load merchant error:', error);
    }
  };

  const handleModeSelected = (mode: 'ev_curbside' | 'ev_dine_in') => {
    setArrivalType(mode);
    setStep('confirm');
  };

  const handleConfirm = async ({ useSmartcar }: { useSmartcar: boolean }) => {
    if (!merchantId) return;

    setLoading(true);
    capture(DRIVER_EVENTS.EV_ARRIVAL_CONFIRM_STARTED, { merchant_id: merchantId });

    try {
      // Get current location
      const position = await getCurrentPosition();

      const response = await api.post('/v1/arrival/create', {
        merchant_id: merchantId,
        arrival_type: arrivalType,
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        accuracy_m: position.coords.accuracy,
        use_smartcar: useSmartcar,
      });

      setSession(response.data);

      // Check if vehicle setup needed
      if (response.data.vehicle_required) {
        setStep('vehicle');
      } else {
        setStep('active');
      }

      capture(DRIVER_EVENTS.EV_ARRIVAL_CREATED, {
        session_id: response.data.session_id,
        merchant_id: merchantId,
        use_smartcar: useSmartcar,
      });

    } catch (error: any) {
      console.error('Create arrival error:', error);

      if (error.response?.data?.error === 'ACTIVE_SESSION_EXISTS') {
        // Load existing session
        await checkActiveSession();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVehicleSaved = () => {
    setStep('active');
  };

  const handleSessionComplete = () => {
    setStep('complete');
  };

  const handleFeedbackComplete = () => {
    setSession(null);
    navigate('/');
  };

  // Render current step
  switch (step) {
    case 'mode':
      return (
        <ModeSelector
          onSelect={handleModeSelected}
          selectedMode={arrivalType}
        />
      );

    case 'vehicle':
      return (
        <VehicleSetup
          onSaved={handleVehicleSaved}
          onSkip={handleVehicleSaved}
        />
      );

    case 'confirm':
      return (
        <ConfirmationSheet
          merchant={merchant}
          arrivalType={arrivalType}
          onConfirm={handleConfirm}
          onCancel={() => setStep('mode')}
          loading={loading}
        />
      );

    case 'active':
      return (
        <ActiveSession
          session={session}
          onComplete={handleSessionComplete}
          onCancel={() => {
            setSession(null);
            navigate('/');
          }}
        />
      );

    case 'complete':
      return (
        <CompletionScreen
          session={session}
          onDone={handleFeedbackComplete}
        />
      );
  }
}

// Helper to get current position
function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
    });
  });
}
```

#### 8.3 Add "Add EV Arrival" CTA to Merchant Cards

Update `apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx`:

```tsx
import { useNavigate } from 'react-router-dom';

function MerchantCard({ merchant }) {
  const navigate = useNavigate();

  const handleAddArrival = () => {
    navigate(`/arrival?merchant=${merchant.id}`);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      {/* ... existing card content ... */}

      <div className="p-4">
        <button
          onClick={handleAddArrival}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg
                     font-medium hover:bg-blue-700 transition-colors"
        >
          Add EV Arrival →
        </button>
      </div>
    </div>
  );
}
```

---

## PART 4: TESTING & VALIDATION

### Required Tests

**File:** `backend/tests/test_smartcar_integration.py`

```python
"""
Tests for Smartcar integration.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.models.arrival_session import ArrivalSession
from app.models.smartcar_token import SmartcarToken


class TestSmartcarOAuth:
    def test_connect_returns_auth_url(self, client, auth_headers):
        response = client.get("/v1/smartcar/connect", headers=auth_headers)
        assert response.status_code == 200
        assert "auth_url" in response.json()
        assert "smartcar" in response.json()["auth_url"]

    def test_status_returns_not_connected(self, client, auth_headers):
        response = client.get("/v1/smartcar/status", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["connected"] == False


class TestSmartcarArrival:
    def test_create_arrival_with_smartcar(self, client, auth_headers, db, test_user):
        # First connect Smartcar
        token = SmartcarToken(
            user_id=test_user.id,
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            vehicle_id="vehicle_123",
            is_active="active",
        )
        db.add(token)
        db.commit()

        # Create arrival with Smartcar
        response = client.post(
            "/v1/arrival/create",
            json={
                "merchant_id": "test_merchant",
                "arrival_type": "ev_curbside",
                "lat": 30.2672,
                "lng": -97.7431,
                "use_smartcar": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201

        # Verify session has Smartcar enabled
        session = db.query(ArrivalSession).filter(
            ArrivalSession.id == response.json()["session_id"]
        ).first()
        assert session.smartcar_enabled == True
        assert session.smartcar_vehicle_id == "vehicle_123"

    def test_create_arrival_without_smartcar_connected_fails(self, client, auth_headers):
        response = client.post(
            "/v1/arrival/create",
            json={
                "merchant_id": "test_merchant",
                "arrival_type": "ev_curbside",
                "lat": 30.2672,
                "lng": -97.7431,
                "use_smartcar": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "SMARTCAR_NOT_CONNECTED"


class TestSmartcarPolling:
    @patch("app.services.smartcar_service.SmartcarService.get_location")
    def test_polling_detects_arrival(self, mock_location, db, test_user):
        # Create Smartcar-enabled session
        session = ArrivalSession(
            driver_id=test_user.id,
            merchant_id="test_merchant",
            charger_id="test_charger",
            arrival_type="ev_curbside",
            status="awaiting_arrival",
            smartcar_enabled=True,
            smartcar_vehicle_id="vehicle_123",
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        db.add(session)
        db.commit()

        # Mock location near charger
        mock_location.return_value = {
            "lat": 30.2672,
            "lng": -97.7431,
            "timestamp": datetime.utcnow(),
        }

        # Run polling job
        from app.jobs.smartcar_polling import poll_active_sessions
        poll_active_sessions()

        # Verify arrival detected
        db.refresh(session)
        assert session.status in ("arrived", "merchant_notified")
        assert session.arrival_source == "smartcar"
```

---

## PART 5: DEPLOYMENT CHECKLIST

```markdown
## Pre-Deploy
- [ ] Environment variables set (SMARTCAR_CLIENT_ID, SMARTCAR_CLIENT_SECRET, SMARTCAR_REDIRECT_URI)
- [ ] Redis running for Celery
- [ ] Database migrations applied (064, 065)
- [ ] Smartcar webhook URLs configured in Smartcar dashboard

## Deploy Backend
- [ ] Run migrations: `alembic upgrade head`
- [ ] Start Celery worker: `celery -A app.celery_app worker --loglevel=info`
- [ ] Start Celery beat: `celery -A app.celery_app beat --loglevel=info`
- [ ] Verify Smartcar OAuth flow works

## Deploy Frontend
- [ ] Build driver app: `npm run build`
- [ ] Verify /arrival route loads
- [ ] Test Smartcar connect flow
- [ ] Test EV Arrival end-to-end

## Smoke Tests
- [ ] Create arrival with Smartcar disabled (manual check-in)
- [ ] Create arrival with Smartcar enabled
- [ ] Verify polling job runs every 60s
- [ ] Verify arrival is detected when within 250m
- [ ] Verify merchant receives SMS notification
- [ ] Verify session completes with billing event
```

---

## Summary: What This Implements

1. **Smartcar OAuth** — Connect driver's vehicle for location/battery data
2. **Smartcar-enabled sessions** — Flag sessions to use Smartcar polling
3. **Background polling** — Celery job polls location every 60s
4. **Arrival detection** — Trigger when vehicle within 250m of charger
5. **Charge complete trigger** — Optional: trigger when battery reaches target SoC
6. **ETA pre-notification** — Notify merchant when driver ~5 min away
7. **Frontend integration** — Connect flow in driver app with Smartcar toggle
8. **Real-time status** — Show ETA and battery in active session UI

**Total effort:** ~16 hours of development

**Canonical model preserved:**
- Arrival remains the invariant
- Smartcar is just another arrival detection signal
- Kitchen fires on arrival, not on order time
- System works without Smartcar (manual fallback)
