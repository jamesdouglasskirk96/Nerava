# Tesla Virtual Key Onboarding Implementation

## Overview

Implement an optimized onboarding flow for Tesla drivers using Nerava in the Tesla browser. This enables automatic arrival detection via Tesla Fleet Telemetry, replacing manual geofence confirmation with seamless vehicle-linked tracking.

## User Scenarios

### Scenario A: First-Time User at Charger
1. Driver opens Nerava in Tesla browser
2. Sees nearby restaurants, taps "Order"
3. Prompt: "Enable arrival tracking?"
   - "Your food will be ready when you arrive"
   - [Scan QR to Set Up] [Skip - Use Phone Instead]
4. If they scan:
   - Tesla app opens on their phone
   - Tap "Add Virtual Key"
   - Return to browser → Continue ordering
5. If they skip:
   - Fall back to QR → Phone handoff for THIS order
   - Prompt again next time

### Scenario B: Returning User
1. Driver opens Nerava in Tesla browser
2. Virtual key already installed
3. Order → Drive → Arrive → Food ready (zero friction)

---

## Implementation Tasks

### Phase 1: Backend - Data Models & Migrations

#### 1.1 Create Virtual Key Model
**File:** `backend/app/models/virtual_key.py`

```python
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as UUIDType
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timedelta
from app.database import Base

class VirtualKey(Base):
    __tablename__ = "virtual_keys"

    id = Column(UUIDType(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Tesla Fleet API identifiers
    tesla_vehicle_id = Column(String(100), nullable=True)  # From Fleet API
    vin = Column(String(17), nullable=True)  # Vehicle Identification Number
    vehicle_name = Column(String(100), nullable=True)  # User-friendly name

    # Provisioning state
    provisioning_token = Column(String(255), unique=True, nullable=False)
    qr_code_url = Column(String(500), nullable=True)  # S3 URL for QR image

    # Status: 'pending', 'paired', 'active', 'revoked', 'expired'
    status = Column(String(20), default='pending')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    paired_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    # Metadata
    pairing_attempts = Column(Integer, default=0)
    last_telemetry_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="virtual_keys")

# Add to User model (backend/app/models/user.py):
# virtual_keys = relationship("VirtualKey", back_populates="user")
```

#### 1.2 Create Alembic Migration
**File:** `backend/alembic/versions/065_add_virtual_keys_table.py`

Create migration with:
- `virtual_keys` table with all columns above
- Index on `user_id`
- Index on `provisioning_token`
- Unique constraint on `vin` (one VIN per active virtual key)

#### 1.3 Extend Arrival Session Model
**File:** `backend/app/models/arrival_session.py`

Add columns:
```python
virtual_key_id = Column(UUIDType(as_uuid=True), ForeignKey("virtual_keys.id"), nullable=True)
arrival_source = Column(String(30), nullable=True)  # 'virtual_key', 'geofence', 'manual'
vehicle_soc_at_arrival = Column(Float, nullable=True)  # Battery % from telemetry
```

---

### Phase 2: Backend - Tesla Fleet API Integration

#### 2.1 Tesla Fleet API Client
**File:** `backend/app/services/tesla_fleet_api.py`

Implement Tesla Fleet API client:
```python
class TeslaFleetAPIClient:
    """Tesla Fleet API client for Virtual Key operations."""

    def __init__(self):
        self.base_url = "https://fleet-api.prd.na.vn.cloud.tesla.com"
        self.client_id = settings.TESLA_CLIENT_ID
        self.client_secret = settings.TESLA_CLIENT_SECRET
        self.public_key_url = settings.TESLA_PUBLIC_KEY_URL

    async def generate_partner_token(self) -> str:
        """Get partner authentication token."""
        pass

    async def register_partner(self) -> dict:
        """Register as Fleet API partner (one-time setup)."""
        pass

    async def get_vehicle_data(self, vehicle_id: str, token: str) -> dict:
        """Get vehicle telemetry data."""
        pass

    async def get_vehicle_location(self, vehicle_id: str, token: str) -> dict:
        """Get real-time vehicle location."""
        pass

    async def send_command(self, vehicle_id: str, command: str, token: str) -> bool:
        """Send command to vehicle (flash lights, honk)."""
        pass
```

**Environment Variables to add:**
```env
TESLA_CLIENT_ID=
TESLA_CLIENT_SECRET=
TESLA_PUBLIC_KEY_URL=https://api.nerava.com/.well-known/appspecific/com.tesla.3p.public-key.pem
TESLA_FLEET_TELEMETRY_ENDPOINT=wss://fleet-telemetry.nerava.com
```

#### 2.2 Virtual Key Provisioning Service
**File:** `backend/app/services/virtual_key_service.py`

```python
class VirtualKeyService:
    """Service for Virtual Key provisioning and management."""

    async def create_provisioning_request(self, user_id: int, vin: str = None) -> VirtualKey:
        """
        Create a new Virtual Key provisioning request.
        Returns VirtualKey with QR code data for Tesla app scanning.
        """
        pass

    async def check_pairing_status(self, provisioning_token: str) -> dict:
        """
        Check if user has completed pairing in Tesla app.
        Called by frontend polling or webhook.
        """
        pass

    async def confirm_pairing(self, provisioning_token: str, tesla_vehicle_id: str) -> VirtualKey:
        """
        Called by Tesla Fleet API webhook when pairing completes.
        Updates Virtual Key status to 'paired'.
        """
        pass

    async def activate_virtual_key(self, virtual_key_id: UUID) -> VirtualKey:
        """
        Activate Virtual Key for arrival tracking.
        Called after first successful arrival detection.
        """
        pass

    async def revoke_virtual_key(self, virtual_key_id: UUID, user_id: int) -> bool:
        """
        Revoke a Virtual Key (user-initiated or admin).
        """
        pass

    async def get_user_virtual_keys(self, user_id: int) -> List[VirtualKey]:
        """Get all Virtual Keys for a user."""
        pass

    async def get_active_virtual_key(self, user_id: int) -> Optional[VirtualKey]:
        """Get the currently active Virtual Key for arrival tracking."""
        pass
```

#### 2.3 QR Code Generation for Virtual Key
**File:** `backend/app/services/virtual_key_qr.py`

```python
import qrcode
import io
import boto3

class VirtualKeyQRService:
    """Generate Tesla-compatible QR codes for Virtual Key pairing."""

    def generate_pairing_qr(self, provisioning_token: str, callback_url: str) -> str:
        """
        Generate QR code for Tesla app scanning.
        Returns S3 URL to QR code image.

        QR data format (Tesla-specific):
        nerava://pair?token={provisioning_token}&callback={callback_url}
        """
        pass

    def generate_phone_handoff_qr(self, session_id: str, order_url: str) -> str:
        """
        Generate QR code for phone handoff (fallback flow).
        User scans with phone to continue order.
        """
        pass
```

---

### Phase 3: Backend - API Endpoints

#### 3.1 Virtual Key Router
**File:** `backend/app/routers/virtual_key.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import get_current_user
from app.services.virtual_key_service import VirtualKeyService

router = APIRouter(prefix="/v1/virtual-key", tags=["virtual-key"])

@router.post("/provision")
async def provision_virtual_key(
    vin: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Start Virtual Key provisioning process.
    Returns QR code URL for Tesla app scanning.
    """
    pass

@router.get("/status/{provisioning_token}")
async def check_provisioning_status(
    provisioning_token: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if Virtual Key pairing is complete.
    Frontend polls this during QR display.
    """
    pass

@router.get("/active")
async def get_active_virtual_key(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's active Virtual Key (if any).
    Used to determine if user has arrival tracking enabled.
    """
    pass

@router.delete("/{virtual_key_id}")
async def revoke_virtual_key(
    virtual_key_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Revoke a Virtual Key."""
    pass

@router.post("/webhook/tesla")
async def tesla_fleet_webhook(request: Request):
    """
    Webhook endpoint for Tesla Fleet API callbacks.
    Receives pairing confirmations and telemetry updates.
    """
    pass
```

#### 3.2 Extend EV Context Endpoint
**File:** `backend/app/routers/ev_context.py`

Add to `/v1/ev-context` response:
```python
{
    # Existing fields...
    "virtual_key_status": "none" | "pending" | "paired" | "active",
    "virtual_key_id": "uuid" | null,
    "arrival_tracking_enabled": bool,
    "show_virtual_key_prompt": bool  # True if first-time user
}
```

---

### Phase 4: Frontend - Virtual Key Onboarding Components

#### 4.1 Virtual Key Detection Hook
**File:** `apps/driver/src/hooks/useVirtualKey.ts`

```typescript
interface VirtualKeyState {
  status: 'none' | 'pending' | 'paired' | 'active';
  virtualKeyId: string | null;
  arrivalTrackingEnabled: boolean;
  showPrompt: boolean;
}

export function useVirtualKey() {
  // Fetch Virtual Key status from /v1/ev-context or dedicated endpoint
  // Provide methods: startProvisioning, checkStatus, revokeKey
}
```

#### 4.2 Virtual Key Prompt Modal
**File:** `apps/driver/src/components/VirtualKey/VirtualKeyPromptModal.tsx`

Design per user scenario:
```
┌─────────────────────────────────────────┐
│     🚗  Enable Arrival Tracking?        │
├─────────────────────────────────────────┤
│                                         │
│  Your food will be ready when you       │
│  arrive. We'll track your Tesla and     │
│  notify the merchant automatically.     │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   [Scan QR to Set Up]           │    │
│  │   One-time setup (30 seconds)   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   [Skip - Use Phone Instead]    │    │
│  │   Manual check-in this time     │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

#### 4.3 QR Code Pairing Screen
**File:** `apps/driver/src/components/VirtualKey/VirtualKeyPairingScreen.tsx`

```
┌─────────────────────────────────────────┐
│     Scan with Tesla App                 │
├─────────────────────────────────────────┤
│                                         │
│       ┌─────────────────────┐           │
│       │    [QR CODE HERE]   │           │
│       │                     │           │
│       │                     │           │
│       └─────────────────────┘           │
│                                         │
│  1. Open Tesla app on your phone        │
│  2. Tap "Add Virtual Key"               │
│  3. Scan this code                      │
│                                         │
│  ──────────────────────────────────     │
│  Waiting for pairing...                 │
│  [Cancel]                               │
│                                         │
└─────────────────────────────────────────┘
```

Implement:
- Poll `/v1/virtual-key/status/{token}` every 2 seconds
- On success, show confirmation and return to order flow
- Timeout after 5 minutes with retry option

#### 4.4 Pairing Success Confirmation
**File:** `apps/driver/src/components/VirtualKey/VirtualKeySuccessModal.tsx`

```
┌─────────────────────────────────────────┐
│     ✓  Arrival Tracking Enabled         │
├─────────────────────────────────────────┤
│                                         │
│  Your Tesla is now connected. We'll     │
│  track your arrival and have your       │
│  order ready when you get there.        │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   [Continue Ordering]           │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

#### 4.5 Phone Handoff Flow (Fallback)
**File:** `apps/driver/src/components/VirtualKey/PhoneHandoffModal.tsx`

When user selects "Skip - Use Phone Instead":
```
┌─────────────────────────────────────────┐
│     📱  Continue on Phone               │
├─────────────────────────────────────────┤
│                                         │
│  Scan this code with your phone to      │
│  complete your order and check in       │
│  when you arrive.                       │
│                                         │
│       ┌─────────────────────┐           │
│       │   [QR CODE HERE]    │           │
│       │ (links to order)    │           │
│       └─────────────────────┘           │
│                                         │
│  We'll remind you to set up arrival     │
│  tracking next time for a smoother      │
│  experience.                            │
│                                         │
└─────────────────────────────────────────┘
```

---

### Phase 5: Integration with Existing Flows

#### 5.1 Modify Order Flow Entry Point
**File:** `apps/driver/src/components/EVOrder/EVOrderScreen.tsx` (or equivalent)

Before order submission:
```typescript
// Check if user has Virtual Key
const { status, showPrompt } = useVirtualKey();

if (showPrompt && status === 'none') {
  // Show VirtualKeyPromptModal
  // On "Set Up" → navigate to pairing flow
  // On "Skip" → show phone handoff QR
} else if (status === 'active') {
  // Proceed directly to order
}
```

#### 5.2 Extend Arrival Session Creation
**File:** `apps/driver/src/components/EVArrival/ActiveSession.tsx`

When creating arrival session with Virtual Key:
```typescript
const createSession = async () => {
  const { virtualKeyId } = useVirtualKey();

  await api.post('/v1/arrival/create', {
    charger_id: chargerId,
    merchant_id: selectedMerchant.id,
    virtual_key_id: virtualKeyId,  // NEW: Link Virtual Key
    fulfillment_type: 'ev_curbside'
  });
};
```

#### 5.3 Automatic Arrival Detection
**Backend:** When Fleet Telemetry shows vehicle near merchant location, automatically:
1. Update arrival session status to `arrived`
2. Send merchant notification
3. Push update to frontend via WebSocket or polling

**Frontend:** Show arrival confirmation without user action:
```
┌─────────────────────────────────────────┐
│     ✓  You've Arrived!                  │
├─────────────────────────────────────────┤
│                                         │
│  We've notified [Merchant Name] that    │
│  you're here. Your order will be out    │
│  shortly.                               │
│                                         │
│  Battery: 65%                           │
│  Estimated wait: 3 minutes              │
│                                         │
└─────────────────────────────────────────┘
```

---

### Phase 6: Analytics Events

Add to `apps/driver/src/analytics/events.ts`:

```typescript
export const VIRTUAL_KEY_EVENTS = {
  // Onboarding
  PROMPT_SHOWN: 'virtual_key.prompt_shown',
  PROMPT_ACCEPTED: 'virtual_key.prompt_accepted',
  PROMPT_SKIPPED: 'virtual_key.prompt_skipped',

  // Pairing
  PAIRING_STARTED: 'virtual_key.pairing_started',
  PAIRING_QR_DISPLAYED: 'virtual_key.qr_displayed',
  PAIRING_COMPLETED: 'virtual_key.pairing_completed',
  PAIRING_FAILED: 'virtual_key.pairing_failed',
  PAIRING_TIMEOUT: 'virtual_key.pairing_timeout',

  // Usage
  ARRIVAL_DETECTED: 'virtual_key.arrival_detected',
  ARRIVAL_CONFIRMED: 'virtual_key.arrival_confirmed',

  // Management
  KEY_REVOKED: 'virtual_key.revoked',

  // Fallback
  PHONE_HANDOFF_SHOWN: 'virtual_key.phone_handoff_shown',
  PHONE_HANDOFF_SCANNED: 'virtual_key.phone_handoff_scanned',
};
```

Add backend analytics in `backend/app/services/analytics.py`.

---

### Phase 7: Fleet Telemetry Server (Infrastructure)

#### 7.1 Fleet Telemetry Server Setup
This requires infrastructure work outside the main app:

**Option A: Use Tesla's hosted solution**
- Configure Fleet Telemetry in Tesla Developer Portal
- Receive webhooks at `/v1/virtual-key/webhook/tesla`

**Option B: Self-hosted Fleet Telemetry**
- Deploy Tesla Fleet Telemetry server (Go binary)
- Configure TLS certificates
- Kubernetes deployment or standalone EC2

For MVP, use Option A (webhooks) and upgrade to Option B for real-time data later.

#### 7.2 Webhook Handler
**File:** `backend/app/routers/virtual_key.py`

```python
@router.post("/webhook/tesla")
async def tesla_fleet_webhook(request: Request):
    """
    Handle Tesla Fleet API webhooks:
    - Pairing confirmation
    - Vehicle location updates
    - Charging state changes
    """
    payload = await request.json()
    event_type = payload.get("type")

    if event_type == "vehicle_paired":
        await virtual_key_service.confirm_pairing(
            provisioning_token=payload["token"],
            tesla_vehicle_id=payload["vehicle_id"]
        )
    elif event_type == "vehicle_location":
        await arrival_service.check_geofence_from_telemetry(
            vehicle_id=payload["vehicle_id"],
            lat=payload["latitude"],
            lng=payload["longitude"]
        )
```

---

### Phase 8: Testing & Rollout

#### 8.1 Feature Flag
Add to `backend/app/dependencies/feature_flags.py`:
```python
VIRTUAL_KEY_ENABLED = os.getenv("FEATURE_VIRTUAL_KEY_ENABLED", "false") == "true"
```

#### 8.2 Test Cases
Create tests in:
- `backend/tests/test_virtual_key.py`
- `backend/tests/test_virtual_key_provisioning.py`
- `apps/driver/src/components/VirtualKey/__tests__/`

Test scenarios:
1. First-time user sees prompt → accepts → completes pairing
2. First-time user sees prompt → skips → phone handoff works
3. Returning user with active key → no prompt, automatic tracking
4. Pairing timeout → user can retry
5. Key revocation → user sees prompt again next time
6. Multiple vehicles → user can select which one

#### 8.3 Rollout Plan
1. Deploy behind feature flag (disabled)
2. Enable for internal testing
3. Enable for 10% of Tesla browser users
4. Monitor conversion rates and error rates
5. Expand to 100%

---

## File Structure Summary

```
backend/
├── alembic/versions/
│   └── 065_add_virtual_keys_table.py
├── app/
│   ├── models/
│   │   └── virtual_key.py
│   ├── routers/
│   │   └── virtual_key.py
│   └── services/
│       ├── tesla_fleet_api.py
│       ├── virtual_key_service.py
│       └── virtual_key_qr.py

apps/driver/src/
├── components/
│   └── VirtualKey/
│       ├── VirtualKeyPromptModal.tsx
│       ├── VirtualKeyPairingScreen.tsx
│       ├── VirtualKeySuccessModal.tsx
│       └── PhoneHandoffModal.tsx
└── hooks/
    └── useVirtualKey.ts
```

---

## Key Implementation Notes

1. **Tesla Developer Account Required**: Before starting, ensure Tesla Developer Account is approved and Partner Token is configured.

2. **Public Key Hosting**: Tesla requires hosting a public key at a specific URL for Fleet API authentication. Add to nginx config.

3. **QR Code Format**: Verify exact QR data format required by Tesla app - this may require testing with real vehicles.

4. **Fallback Always Available**: Phone handoff must work even if Virtual Key flow fails.

5. **Rate Limiting**: Limit provisioning attempts to prevent abuse (e.g., 3 attempts per hour per user).

6. **Privacy**: Don't store vehicle location data longer than needed for arrival detection.

7. **Battery Display**: Show SOC in UI when available from telemetry (nice UX touch).

---

## Dependencies to Add

```
# backend/requirements.txt
qrcode[pil]==7.4.2  # QR code generation
```

```
# apps/driver/package.json
# No new dependencies - uses existing React/TypeScript
```

---

## Environment Variables

```env
# Tesla Fleet API
TESLA_CLIENT_ID=your_client_id
TESLA_CLIENT_SECRET=your_client_secret
TESLA_PUBLIC_KEY_URL=https://api.nerava.com/.well-known/appspecific/com.tesla.3p.public-key.pem
TESLA_WEBHOOK_SECRET=your_webhook_secret

# Feature Flag
FEATURE_VIRTUAL_KEY_ENABLED=false
```

---

## Success Metrics

Track these metrics in PostHog:
1. **Conversion rate**: % of users who see prompt and complete pairing
2. **Skip rate**: % of users who skip to phone handoff
3. **Retry rate**: % of pairing attempts that timeout and retry
4. **Active usage**: % of orders using Virtual Key vs manual check-in
5. **Error rate**: Failed pairing attempts, webhook failures

---

## Timeline Reference

- Week 1-2: Backend models, migrations, Tesla API client
- Week 2-3: Provisioning endpoints, QR generation, webhook handler
- Week 3-4: Frontend components, integration with order flow
- Week 4: Testing, feature flag rollout, monitoring
