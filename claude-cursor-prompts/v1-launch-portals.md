# Cursor Super-Prompt: Admin + Merchant Portal v1 Launch

## Title
**Nerava Portal v1: Minimum Viable Control Surface**

## Objective

Ship production-ready v1 of Admin Portal and Merchant Portal focused on:
- **Offer management** (CRUD + enable/disable with caps)
- **Verified visits / billable events** visibility
- **Admin kill-switch controls** and auditability
- **Billing readiness** (reporting + billable events list, NOT Stripe UI)

**Timeline:** Admin 5-7 days, Merchant 7-10 days

---

## PLAN MODE

Before making any changes, output a plan listing:
1. All files you will modify
2. All new files you will create
3. All database migrations required
4. All API endpoints to implement

Wait for approval before proceeding.

---

## Allowed Files/Folders to Modify

### Backend (`/Users/jameskirk/Desktop/Nerava/nerava-backend-v9 2/`)
```
app/routers/admin_domain.py       # Add missing admin endpoints
app/routers/auth_domain.py        # Add admin login endpoint
app/routers/merchants_domain.py   # Add visits endpoint
app/services/admin_service.py     # NEW: Admin operations service
app/services/audit.py             # Extend audit logging
app/models/admin.py               # NEW: AdminOverride model (if needed)
app/schemas/admin.py              # Admin request/response schemas
app/schemas/merchant.py           # Merchant visit schemas
alembic/versions/                 # New migration files only
tests/test_admin_v1.py            # NEW: Admin endpoint tests
tests/test_merchant_visits.py     # NEW: Merchant visits test
```

### Admin Frontend (`/Users/jameskirk/Desktop/Nerava/apps/admin/`)
```
src/components/Exclusives.tsx     # Wire to real API
src/components/Overrides.tsx      # Wire to real API
src/components/Logs.tsx           # Wire to real API
src/components/Merchants.tsx      # Add pause/resume actions
src/services/api.ts               # Add new API calls
```

### Merchant Frontend (`/Users/jameskirk/Desktop/Nerava/apps/merchant/`)
```
app/routes/visits.tsx             # Wire to real visits API
app/routes/overview.tsx           # Ensure report API used
app/routes/billing.tsx            # Add "manual invoicing" banner
app/services/api.ts               # Add visits API call
```

---

## Step-by-Step Implementation

### Phase 1: Backend - Admin Endpoints (Days 1-3)

#### 1.1 Admin Login Endpoint

**File:** `app/routers/auth_domain.py`

Add endpoint:
```python
@router.post("/admin/login")
async def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
) -> AdminLoginResponse:
    """
    Admin login with email/password.
    Returns JWT token if user has admin role.
    """
    user = authenticate_user(db, request.email, request.password)
    if not user or "admin" not in (user.role_flags or ""):
        raise HTTPException(401, "Invalid credentials or not an admin")

    token = create_access_token(subject=str(user.public_id))
    log_admin_action(db, user.id, "admin_login", "user", user.id, request.ip)

    return AdminLoginResponse(
        access_token=token,
        token_type="bearer",
        admin_email=user.email
    )
```

**Schemas:**
```python
class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_email: str
```

#### 1.2 Admin Exclusives Endpoints

**File:** `app/routers/admin_domain.py`

```python
@router.get("/exclusives")
async def list_all_exclusives(
    status: Optional[str] = None,  # active, paused, all
    merchant_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
) -> AdminExclusivesResponse:
    """List all exclusives across merchants for admin oversight."""
    query = db.query(MerchantExclusive).join(Merchant)

    if status == "active":
        query = query.filter(MerchantExclusive.is_active == True)
    elif status == "paused":
        query = query.filter(MerchantExclusive.is_active == False)

    if merchant_id:
        query = query.filter(MerchantExclusive.merchant_id == merchant_id)

    exclusives = query.offset(offset).limit(limit).all()
    total = query.count()

    return AdminExclusivesResponse(
        exclusives=[AdminExclusiveItem.from_orm(e) for e in exclusives],
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/exclusives/{exclusive_id}/toggle")
async def toggle_exclusive(
    exclusive_id: str,
    request: ToggleExclusiveRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
) -> ToggleExclusiveResponse:
    """Admin toggle exclusive on/off with mandatory reason."""
    exclusive = db.query(MerchantExclusive).filter(
        MerchantExclusive.id == exclusive_id
    ).first()

    if not exclusive:
        raise HTTPException(404, "Exclusive not found")

    previous_state = exclusive.is_active
    exclusive.is_active = not exclusive.is_active
    exclusive.updated_at = datetime.utcnow()

    log_admin_action(
        db, admin.id,
        "exclusive_toggle",
        "exclusive", exclusive_id,
        f"{'enabled' if exclusive.is_active else 'disabled'}: {request.reason}"
    )

    db.commit()

    return ToggleExclusiveResponse(
        exclusive_id=exclusive_id,
        previous_state=previous_state,
        new_state=exclusive.is_active,
        toggled_by=admin.email,
        reason=request.reason
    )
```

**Schemas:**
```python
class ToggleExclusiveRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Mandatory reason for toggle")

class ToggleExclusiveResponse(BaseModel):
    exclusive_id: str
    previous_state: bool
    new_state: bool
    toggled_by: str
    reason: str

class AdminExclusiveItem(BaseModel):
    id: str
    merchant_id: str
    merchant_name: str
    title: str
    description: Optional[str]
    nova_reward: int
    is_active: bool
    daily_cap: Optional[int]
    activations_today: int
    activations_this_month: int
    created_at: datetime
    updated_at: datetime

class AdminExclusivesResponse(BaseModel):
    exclusives: List[AdminExclusiveItem]
    total: int
    limit: int
    offset: int
```

#### 1.3 Merchant Pause/Resume Endpoints

**File:** `app/routers/admin_domain.py`

```python
@router.post("/merchants/{merchant_id}/pause")
async def pause_merchant(
    merchant_id: str,
    request: MerchantActionRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
) -> MerchantActionResponse:
    """Pause a merchant - disables all their exclusives and hides from discovery."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found")

    if merchant.status == "paused":
        raise HTTPException(400, "Merchant already paused")

    previous_status = merchant.status
    merchant.status = "paused"
    merchant.updated_at = datetime.utcnow()

    # Disable all active exclusives
    db.query(MerchantExclusive).filter(
        MerchantExclusive.merchant_id == merchant_id,
        MerchantExclusive.is_active == True
    ).update({"is_active": False, "updated_at": datetime.utcnow()})

    log_admin_action(db, admin.id, "merchant_pause", "merchant", merchant_id, request.reason)
    db.commit()

    return MerchantActionResponse(
        merchant_id=merchant_id,
        action="pause",
        previous_status=previous_status,
        new_status="paused",
        reason=request.reason
    )


@router.post("/merchants/{merchant_id}/resume")
async def resume_merchant(
    merchant_id: str,
    request: MerchantActionRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
) -> MerchantActionResponse:
    """Resume a paused merchant."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found")

    if merchant.status != "paused":
        raise HTTPException(400, "Merchant is not paused")

    merchant.status = "active"
    merchant.updated_at = datetime.utcnow()

    log_admin_action(db, admin.id, "merchant_resume", "merchant", merchant_id, request.reason)
    db.commit()

    return MerchantActionResponse(
        merchant_id=merchant_id,
        action="resume",
        previous_status="paused",
        new_status="active",
        reason=request.reason
    )
```

#### 1.4 Override Endpoints (Force-Close + Emergency Pause)

**File:** `app/routers/admin_domain.py`

```python
@router.post("/sessions/force-close")
async def force_close_sessions(
    request: ForceCloseRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
) -> ForceCloseResponse:
    """
    Force-close all active exclusive sessions at a location.
    CRITICAL ACTION - requires reason and is logged.
    """
    # Find all active sessions at location
    active_sessions = db.query(ExclusiveSession).filter(
        ExclusiveSession.charger_id.in_(
            db.query(Charger.id).filter(Charger.location_id == request.location_id)
        ),
        ExclusiveSession.status == ExclusiveSessionStatus.ACTIVE
    ).all()

    closed_count = 0
    for session in active_sessions:
        session.status = ExclusiveSessionStatus.FORCE_CLOSED
        session.ended_at = datetime.utcnow()
        session.force_close_reason = request.reason
        session.force_closed_by = admin.id
        closed_count += 1

    log_admin_action(
        db, admin.id,
        "force_close_sessions",
        "location", request.location_id,
        f"Force closed {closed_count} sessions: {request.reason}"
    )

    db.commit()

    return ForceCloseResponse(
        location_id=request.location_id,
        sessions_closed=closed_count,
        closed_by=admin.email,
        reason=request.reason,
        timestamp=datetime.utcnow()
    )


@router.post("/overrides/emergency-pause")
async def emergency_pause(
    request: EmergencyPauseRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
) -> EmergencyPauseResponse:
    """
    EMERGENCY: Pause all exclusive activations system-wide.
    Sets a global flag that prevents new activations.
    CRITICAL ACTION - requires reason and confirmation token.
    """
    # Verify confirmation token (simple: must match "CONFIRM-EMERGENCY-PAUSE")
    if request.confirmation != "CONFIRM-EMERGENCY-PAUSE":
        raise HTTPException(400, "Invalid confirmation. Send confirmation='CONFIRM-EMERGENCY-PAUSE'")

    # Set global emergency pause flag (use Redis or config table)
    # Option 1: Redis key
    # Option 2: SystemConfig table
    from app.cache.redis_client import redis_client

    if request.action == "activate":
        redis_client.set("emergency_pause_active", "1")
        redis_client.set("emergency_pause_reason", request.reason)
        redis_client.set("emergency_pause_by", str(admin.id))
        redis_client.set("emergency_pause_at", datetime.utcnow().isoformat())
        action_taken = "activated"
    else:
        redis_client.delete("emergency_pause_active")
        action_taken = "deactivated"

    log_admin_action(
        db, admin.id,
        f"emergency_pause_{action_taken}",
        "system", "global",
        request.reason
    )

    db.commit()

    return EmergencyPauseResponse(
        action=action_taken,
        activated_by=admin.email,
        reason=request.reason,
        timestamp=datetime.utcnow()
    )
```

**Schemas:**
```python
class ForceCloseRequest(BaseModel):
    location_id: str
    reason: str = Field(..., min_length=10, description="Mandatory reason for force close")

class ForceCloseResponse(BaseModel):
    location_id: str
    sessions_closed: int
    closed_by: str
    reason: str
    timestamp: datetime

class EmergencyPauseRequest(BaseModel):
    action: Literal["activate", "deactivate"]
    reason: str = Field(..., min_length=10)
    confirmation: str = Field(..., description="Must be 'CONFIRM-EMERGENCY-PAUSE'")

class EmergencyPauseResponse(BaseModel):
    action: str
    activated_by: str
    reason: str
    timestamp: datetime
```

#### 1.5 Audit Logs Endpoint

**File:** `app/routers/admin_domain.py`

```python
@router.get("/logs")
async def get_admin_logs(
    type: Optional[str] = None,  # admin, error, system, merchant
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
) -> AdminLogsResponse:
    """Retrieve admin audit logs with filtering."""
    query = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())

    if type:
        query = query.filter(AdminAuditLog.action_type.ilike(f"%{type}%"))

    if search:
        query = query.filter(
            or_(
                AdminAuditLog.action_type.ilike(f"%{search}%"),
                AdminAuditLog.target_id.ilike(f"%{search}%"),
                AdminAuditLog.reason.ilike(f"%{search}%")
            )
        )

    if start_date:
        query = query.filter(AdminAuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AdminAuditLog.created_at <= end_date)

    total = query.count()
    logs = query.offset(offset).limit(limit).all()

    return AdminLogsResponse(
        logs=[AdminLogEntry.from_orm(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset
    )
```

**Schemas:**
```python
class AdminLogEntry(BaseModel):
    id: int
    operator_id: int
    operator_email: Optional[str]
    action_type: str
    target_type: str
    target_id: str
    reason: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

class AdminLogsResponse(BaseModel):
    logs: List[AdminLogEntry]
    total: int
    limit: int
    offset: int
```

---

### Phase 2: Backend - Merchant Endpoints (Days 2-4)

#### 2.1 Merchant Visits / Billable Events Endpoint

**File:** `app/routers/merchants_domain.py`

```python
@router.get("/{merchant_id}/visits")
async def get_merchant_visits(
    merchant_id: str,
    period: str = "week",  # week, month, all
    status: Optional[str] = None,  # VERIFIED, PARTIAL, REJECTED
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MerchantVisitsResponse:
    """
    Get verified visits (billable events) for a merchant.
    This is the core billing proof endpoint.
    """
    # Verify merchant ownership
    merchant = verify_merchant_access(db, merchant_id, current_user)

    # Calculate date range
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = None

    # Query exclusive sessions as "visits"
    query = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id
    )

    if start_date:
        query = query.filter(ExclusiveSession.activated_at >= start_date)

    if status:
        # Map to session status
        status_map = {
            "VERIFIED": [ExclusiveSessionStatus.COMPLETED],
            "PARTIAL": [ExclusiveSessionStatus.ACTIVE, ExclusiveSessionStatus.EXPIRED],
            "REJECTED": [ExclusiveSessionStatus.FORCE_CLOSED, ExclusiveSessionStatus.CANCELLED]
        }
        query = query.filter(ExclusiveSession.status.in_(status_map.get(status, [])))

    query = query.order_by(ExclusiveSession.activated_at.desc())

    total = query.count()
    visits = query.offset(offset).limit(limit).all()

    # Calculate summary stats
    verified_count = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id,
        ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED,
        ExclusiveSession.activated_at >= start_date if start_date else True
    ).count()

    return MerchantVisitsResponse(
        visits=[MerchantVisitItem(
            id=str(v.id),
            timestamp=v.activated_at,
            exclusive_id=str(v.exclusive_id) if v.exclusive_id else None,
            exclusive_title=v.exclusive.title if v.exclusive else "General Visit",
            driver_id_anonymized=f"DRV-{hash(str(v.driver_id)) % 10000:04d}",
            verification_status=map_session_to_verification(v.status),
            duration_minutes=calculate_duration(v),
            charger_id=v.charger_id,
            location_name=v.charger.location.name if v.charger and v.charger.location else None
        ) for v in visits],
        total=total,
        verified_count=verified_count,
        period=period,
        limit=limit,
        offset=offset
    )


def map_session_to_verification(status: ExclusiveSessionStatus) -> str:
    """Map internal session status to billing verification status."""
    mapping = {
        ExclusiveSessionStatus.COMPLETED: "VERIFIED",
        ExclusiveSessionStatus.ACTIVE: "PARTIAL",
        ExclusiveSessionStatus.EXPIRED: "PARTIAL",
        ExclusiveSessionStatus.FORCE_CLOSED: "REJECTED",
        ExclusiveSessionStatus.CANCELLED: "REJECTED"
    }
    return mapping.get(status, "PARTIAL")


def calculate_duration(session: ExclusiveSession) -> Optional[int]:
    """Calculate session duration in minutes."""
    if session.ended_at and session.activated_at:
        delta = session.ended_at - session.activated_at
        return int(delta.total_seconds() / 60)
    return None
```

**Schemas:**
```python
class MerchantVisitItem(BaseModel):
    id: str
    timestamp: datetime
    exclusive_id: Optional[str]
    exclusive_title: str
    driver_id_anonymized: str
    verification_status: Literal["VERIFIED", "PARTIAL", "REJECTED"]
    duration_minutes: Optional[int]
    charger_id: Optional[str]
    location_name: Optional[str]

class MerchantVisitsResponse(BaseModel):
    visits: List[MerchantVisitItem]
    total: int
    verified_count: int
    period: str
    limit: int
    offset: int
```

#### 2.2 Ensure Merchant Report Endpoint Works

**File:** `app/routers/merchants_domain.py`

Verify existing `GET /v1/merchants/{id}/report` returns:
```python
class MerchantReport(BaseModel):
    merchant_id: str
    merchant_name: str
    period: str  # "week" or "month"
    period_start: datetime
    period_end: datetime

    # Core metrics
    total_visits: int
    verified_visits: int
    unique_drivers: int

    # Financial
    nova_awarded: int
    estimated_revenue_cents: int  # Based on avg ticket
    platform_fee_cents: int

    # Breakdown
    visits_by_exclusive: List[ExclusiveBreakdown]
    top_hours: Dict[int, int]  # hour -> count
```

---

### Phase 3: Database Migrations (Day 2)

#### Migration: Add Exclusive Fields for Caps/Time Windows

**File:** `alembic/versions/050_add_exclusive_cap_fields.py`

```python
"""Add cap and time window fields to merchant exclusives

Revision ID: 050_exclusive_caps
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add fields to merchant_exclusives (or equivalent table)
    op.add_column('merchant_exclusives', sa.Column('daily_cap', sa.Integer(), nullable=True))
    op.add_column('merchant_exclusives', sa.Column('start_time', sa.Time(), nullable=True))
    op.add_column('merchant_exclusives', sa.Column('end_time', sa.Time(), nullable=True))
    op.add_column('merchant_exclusives', sa.Column('days_of_week', sa.String(20), nullable=True))  # "1,2,3,4,5" for Mon-Fri
    op.add_column('merchant_exclusives', sa.Column('staff_notes', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('merchant_exclusives', 'daily_cap')
    op.drop_column('merchant_exclusives', 'start_time')
    op.drop_column('merchant_exclusives', 'end_time')
    op.drop_column('merchant_exclusives', 'days_of_week')
    op.drop_column('merchant_exclusives', 'staff_notes')
```

#### Migration: Ensure Admin Audit Log Table Exists

**File:** `alembic/versions/051_admin_audit_log.py`

```python
"""Create admin_audit_log table if not exists

Revision ID: 051_admin_audit
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Check if table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'admin_audit_log' not in inspector.get_table_names():
        op.create_table(
            'admin_audit_log',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('operator_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('action_type', sa.String(100), nullable=False),
            sa.Column('target_type', sa.String(50), nullable=False),
            sa.Column('target_id', sa.String(100), nullable=False),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('ix_admin_audit_log_action_type', 'admin_audit_log', ['action_type'])
        op.create_index('ix_admin_audit_log_created_at', 'admin_audit_log', ['created_at'])

def downgrade():
    op.drop_table('admin_audit_log')
```

#### Migration: Add Force-Close Fields to Exclusive Sessions

**File:** `alembic/versions/052_session_force_close.py`

```python
"""Add force close tracking to exclusive sessions

Revision ID: 052_force_close
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('exclusive_sessions', sa.Column('force_close_reason', sa.Text(), nullable=True))
    op.add_column('exclusive_sessions', sa.Column('force_closed_by', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('exclusive_sessions', 'force_close_reason')
    op.drop_column('exclusive_sessions', 'force_closed_by')
```

---

### Phase 4: Frontend - Admin Portal (Days 3-5)

#### 4.1 Wire Exclusives Page to Real API

**File:** `apps/admin/src/components/Exclusives.tsx`

```typescript
// Replace mock data with API calls

import { useEffect, useState } from 'react';
import { adminApi } from '../services/api';

interface Exclusive {
  id: string;
  merchant_id: string;
  merchant_name: string;
  title: string;
  is_active: boolean;
  daily_cap: number | null;
  activations_today: number;
  activations_this_month: number;
}

export function Exclusives() {
  const [exclusives, setExclusives] = useState<Exclusive[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'paused'>('all');

  useEffect(() => {
    loadExclusives();
  }, [filter]);

  async function loadExclusives() {
    setLoading(true);
    try {
      const response = await adminApi.get('/exclusives', {
        params: { status: filter === 'all' ? undefined : filter }
      });
      setExclusives(response.data.exclusives);
    } catch (error) {
      console.error('Failed to load exclusives:', error);
    } finally {
      setLoading(false);
    }
  }

  async function toggleExclusive(id: string, reason: string) {
    try {
      await adminApi.post(`/exclusives/${id}/toggle`, { reason });
      loadExclusives(); // Refresh
    } catch (error) {
      console.error('Failed to toggle exclusive:', error);
    }
  }

  // ... render with real data
}
```

#### 4.2 Wire Overrides Page to Real API

**File:** `apps/admin/src/components/Overrides.tsx`

```typescript
import { useState } from 'react';
import { adminApi } from '../services/api';

export function Overrides() {
  const [selectedLocation, setSelectedLocation] = useState('');
  const [reason, setReason] = useState('');
  const [confirmDialog, setConfirmDialog] = useState<string | null>(null);

  async function forceCloseSessions() {
    if (!selectedLocation || !reason || reason.length < 10) {
      alert('Location and reason (min 10 chars) required');
      return;
    }

    try {
      const response = await adminApi.post('/sessions/force-close', {
        location_id: selectedLocation,
        reason: reason
      });
      alert(`Closed ${response.data.sessions_closed} sessions`);
      setConfirmDialog(null);
      setReason('');
    } catch (error) {
      console.error('Force close failed:', error);
      alert('Failed to force close sessions');
    }
  }

  async function emergencyPause(action: 'activate' | 'deactivate') {
    if (!reason || reason.length < 10) {
      alert('Reason required (min 10 chars)');
      return;
    }

    try {
      await adminApi.post('/overrides/emergency-pause', {
        action,
        reason,
        confirmation: 'CONFIRM-EMERGENCY-PAUSE'
      });
      alert(`Emergency pause ${action}d`);
      setConfirmDialog(null);
    } catch (error) {
      console.error('Emergency pause failed:', error);
    }
  }

  // ... render with confirmation dialogs
}
```

#### 4.3 Wire Logs Page to Real API

**File:** `apps/admin/src/components/Logs.tsx`

```typescript
import { useEffect, useState } from 'react';
import { adminApi } from '../services/api';

interface LogEntry {
  id: number;
  operator_email: string;
  action_type: string;
  target_type: string;
  target_id: string;
  reason: string | null;
  ip_address: string | null;
  created_at: string;
}

export function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadLogs();
  }, [typeFilter, search]);

  async function loadLogs() {
    setLoading(true);
    try {
      const response = await adminApi.get('/logs', {
        params: {
          type: typeFilter || undefined,
          search: search || undefined,
          limit: 100
        }
      });
      setLogs(response.data.logs);
    } catch (error) {
      console.error('Failed to load logs:', error);
    } finally {
      setLoading(false);
    }
  }

  // ... render with real data
}
```

#### 4.4 Add Merchant Pause/Resume to Merchants Page

**File:** `apps/admin/src/components/Merchants.tsx`

Add actions column:
```typescript
async function pauseMerchant(merchantId: string) {
  const reason = prompt('Enter reason for pausing merchant:');
  if (!reason || reason.length < 5) return;

  try {
    await adminApi.post(`/merchants/${merchantId}/pause`, { reason });
    loadMerchants(); // Refresh
  } catch (error) {
    console.error('Failed to pause merchant:', error);
  }
}

async function resumeMerchant(merchantId: string) {
  const reason = prompt('Enter reason for resuming merchant:');
  if (!reason || reason.length < 5) return;

  try {
    await adminApi.post(`/merchants/${merchantId}/resume`, { reason });
    loadMerchants();
  } catch (error) {
    console.error('Failed to resume merchant:', error);
  }
}

// In table row actions:
<Button onClick={() => merchant.status === 'paused'
  ? resumeMerchant(merchant.id)
  : pauseMerchant(merchant.id)}>
  {merchant.status === 'paused' ? 'Resume' : 'Pause'}
</Button>
```

---

### Phase 5: Frontend - Merchant Portal (Days 4-6)

#### 5.1 Wire Visits Page to Real API

**File:** `apps/merchant/app/routes/visits.tsx`

```typescript
import { useEffect, useState } from 'react';
import { merchantApi } from '../services/api';

interface Visit {
  id: string;
  timestamp: string;
  exclusive_id: string | null;
  exclusive_title: string;
  driver_id_anonymized: string;
  verification_status: 'VERIFIED' | 'PARTIAL' | 'REJECTED';
  duration_minutes: number | null;
}

export default function Visits() {
  const [visits, setVisits] = useState<Visit[]>([]);
  const [period, setPeriod] = useState<'week' | 'month'>('week');
  const [verifiedCount, setVerifiedCount] = useState(0);

  useEffect(() => {
    loadVisits();
  }, [period]);

  async function loadVisits() {
    const merchantId = getMerchantId(); // From context or auth
    const response = await merchantApi.get(`/merchants/${merchantId}/visits`, {
      params: { period }
    });
    setVisits(response.data.visits);
    setVerifiedCount(response.data.verified_count);
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Verified Visits</h1>
        <select value={period} onChange={(e) => setPeriod(e.target.value as any)}>
          <option value="week">Last 7 Days</option>
          <option value="month">Last 30 Days</option>
        </select>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
        <p className="text-green-800">
          <strong>{verifiedCount}</strong> verified visits this {period} = billable events
        </p>
      </div>

      <table className="w-full">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Offer</th>
            <th>Driver</th>
            <th>Status</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {visits.map(visit => (
            <tr key={visit.id}>
              <td>{new Date(visit.timestamp).toLocaleString()}</td>
              <td>{visit.exclusive_title}</td>
              <td>{visit.driver_id_anonymized}</td>
              <td>
                <span className={`badge ${
                  visit.verification_status === 'VERIFIED' ? 'bg-green-100 text-green-800' :
                  visit.verification_status === 'PARTIAL' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {visit.verification_status}
                </span>
              </td>
              <td>{visit.duration_minutes ? `${visit.duration_minutes} min` : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

#### 5.2 Add Manual Billing Banner

**File:** `apps/merchant/app/routes/billing.tsx`

Add at top of component:
```typescript
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
  <h3 className="font-semibold text-blue-900">Pilot Billing</h3>
  <p className="text-blue-800 text-sm mt-1">
    During the pilot period, invoices are issued based on your verified visits.
    Payments are handled separately by our team.
    View your <a href="/visits" className="underline">verified visits</a> to see billable events.
  </p>
</div>
```

---

## API Contracts Summary

### Admin Endpoints

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| POST | `/v1/auth/admin/login` | `{email, password}` | `{access_token, admin_email}` |
| GET | `/v1/admin/exclusives` | `?status=&merchant_id=&limit=&offset=` | `{exclusives[], total}` |
| POST | `/v1/admin/exclusives/{id}/toggle` | `{reason}` | `{exclusive_id, previous_state, new_state}` |
| POST | `/v1/admin/merchants/{id}/pause` | `{reason}` | `{merchant_id, action, new_status}` |
| POST | `/v1/admin/merchants/{id}/resume` | `{reason}` | `{merchant_id, action, new_status}` |
| POST | `/v1/admin/sessions/force-close` | `{location_id, reason}` | `{sessions_closed, timestamp}` |
| POST | `/v1/admin/overrides/emergency-pause` | `{action, reason, confirmation}` | `{action, timestamp}` |
| GET | `/v1/admin/logs` | `?type=&search=&limit=&offset=` | `{logs[], total}` |

### Merchant Endpoints

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| GET | `/v1/merchants/{id}/visits` | `?period=&status=&limit=&offset=` | `{visits[], verified_count, total}` |
| GET | `/v1/merchants/{id}/report` | `?period=week\|month` | `{verified_visits, nova_awarded, ...}` |

---

## Test Plan

### Admin API Tests (`tests/test_admin_v1.py`)

```python
def test_admin_login_success():
    """Admin with valid credentials gets token"""

def test_admin_login_non_admin_rejected():
    """Non-admin user rejected with 401"""

def test_toggle_exclusive():
    """Toggle changes state and logs action"""

def test_toggle_exclusive_requires_reason():
    """Toggle without reason returns 400"""

def test_force_close_sessions():
    """Force close updates sessions and logs"""

def test_emergency_pause_requires_confirmation():
    """Emergency pause without confirmation returns 400"""

def test_get_logs_filtering():
    """Logs endpoint filters by type and search"""

def test_pause_merchant():
    """Pause merchant updates status and disables exclusives"""

def test_resume_merchant():
    """Resume merchant updates status"""
```

### Merchant API Tests (`tests/test_merchant_visits.py`)

```python
def test_get_visits_returns_sessions():
    """Visits endpoint returns exclusive sessions as visits"""

def test_visits_filters_by_period():
    """Period parameter filters date range correctly"""

def test_visits_anonymizes_driver_id():
    """Driver IDs are anonymized in response"""

def test_verification_status_mapping():
    """Session statuses map to correct verification status"""
```

---

## Rollout Plan

### Day 1-2: Backend
1. Run migrations (050, 051, 052)
2. Deploy admin endpoints
3. Deploy merchant visits endpoint
4. Verify with curl tests

### Day 3-4: Admin Frontend
1. Wire Exclusives page
2. Wire Overrides page
3. Wire Logs page
4. Add merchant pause/resume
5. Test in staging

### Day 5-6: Merchant Frontend
1. Wire Visits page
2. Add billing banner
3. Verify report endpoint
4. Test in staging

### Day 7: Production
1. Deploy backend
2. Deploy admin frontend
3. Deploy merchant frontend
4. Smoke test all critical paths
5. Monitor logs for errors

---

## DO NOT List

- ❌ Do NOT consolidate admin apps (apps/admin + ui-admin)
- ❌ Do NOT implement Stripe billing UI
- ❌ Do NOT implement Settings save functionality
- ❌ Do NOT implement Primary Experience backend
- ❌ Do NOT implement Pickup Packages
- ❌ Do NOT refactor existing working code
- ❌ Do NOT change existing API response shapes (backwards compatibility)
- ❌ Do NOT remove mock data from Dashboard stats (label as "beta" if needed)
- ❌ Do NOT add new dependencies without approval
- ❌ Do NOT modify authentication for driver app endpoints

---

## Success Criteria

### Admin Portal v1 Complete When:
- [ ] Admin can log in and get token
- [ ] Admin can view all exclusives across merchants
- [ ] Admin can toggle any exclusive on/off with reason
- [ ] Admin can pause/resume merchants
- [ ] Admin can force-close sessions at a location
- [ ] Admin can activate/deactivate emergency pause
- [ ] Admin can view audit logs with filtering
- [ ] All admin actions are logged

### Merchant Portal v1 Complete When:
- [ ] Merchant can view verified visits list
- [ ] Visits show: timestamp, offer, anonymized driver, status, duration
- [ ] Merchant can filter visits by period
- [ ] Merchant can view report with verified visits count
- [ ] Billing page shows manual invoicing banner
- [ ] Exclusives CRUD still works with new cap fields
