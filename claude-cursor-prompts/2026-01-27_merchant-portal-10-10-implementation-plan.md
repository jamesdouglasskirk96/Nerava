# Cursor Implementation Plan — Merchant Portal 8.0 → 10/10

## Scope & Priorities

| # | Item | Priority | Impact |
|---|---|---|---|
| 1 | Redirect to `/claim` when `merchant_id` is missing (3 components) | P1 | Prevents 404 API calls with fake ID |
| 2 | Add `GET /v1/exclusive/session/{session_id}` backend endpoint | P1 | Unblocks CustomerExclusiveView |
| 3 | Wire CustomerExclusiveView to return merchant name + exclusive title | P1 | Replaces placeholder strings |
| 4 | Replace Overview "Reserve Primary Experience" no-op button with "Coming Soon" | P2 | Removes misleading CTA |
| 5 | Clean up empty `getStatusColor` TODO block in Exclusives | P2 | Dead code cleanup |

**Guardrails:** No refactors. No new dependencies. No changes to existing API contracts.

---

## Step 1 — Fix `merchant_id` Fallback (P1)

**Problem:** `Overview.tsx:10`, `Exclusives.tsx:23`, `CreateExclusive.tsx:11` fall back to `'current_merchant'` when `localStorage.getItem('merchant_id')` is null. This sends real API requests with a fake ID → 404 errors.

**Pattern to follow:** `Visits.tsx:13` already does this correctly — uses empty string and guards with `if (!merchantId) return`.

### File: `apps/merchant/app/components/Overview.tsx`

**Line 10** — Change:
```typescript
// BEFORE
const merchantId = localStorage.getItem('merchant_id') || 'current_merchant';

// AFTER
const merchantId = localStorage.getItem('merchant_id') || '';
```

**After line 10** — Add guard in `loadData`:
```typescript
const loadData = async () => {
  if (!merchantId) {
    setLoading(false);
    return;
  }
  // ... rest unchanged
```

### File: `apps/merchant/app/components/Exclusives.tsx`

**Line 23** — Same change:
```typescript
const merchantId = localStorage.getItem('merchant_id') || '';
```

**In `loadExclusives` and `loadAnalytics`** — Add early return:
```typescript
const loadExclusives = async () => {
  if (!merchantId) { setLoading(false); return; }
  // ...existing code
```

```typescript
const loadAnalytics = async () => {
  if (!merchantId) return;
  // ...existing code
```

### File: `apps/merchant/app/components/CreateExclusive.tsx`

**Line 11** — Same change:
```typescript
const merchantId = localStorage.getItem('merchant_id') || '';
```

**In `handleSubmit`** — Add guard:
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  if (!merchantId) {
    setError('No merchant ID found. Please complete the claim flow.');
    return;
  }
  // ...existing code
```

---

## Step 2 — Add Backend `GET /v1/exclusive/session/{session_id}` (P1)

**Problem:** `CustomerExclusiveView.tsx` calls `GET /v1/exclusive/{session_id}` but no such endpoint exists. The existing `GET /v1/exclusive/active` requires auth and returns the *driver's* active session — it can't look up a session by ID for staff view.

**File:** `backend/app/routers/exclusive.py`

Add this endpoint after the existing `get_active_exclusive` endpoint (after line 587):

```python
class SessionLookupResponse(BaseModel):
    exclusive_session: Optional[ExclusiveSessionResponse] = None
    merchant_name: Optional[str] = None
    exclusive_title: Optional[str] = None
    staff_instructions: Optional[str] = None


@router.get("/session/{session_id}", response_model=SessionLookupResponse)
async def get_exclusive_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Look up an exclusive session by ID.

    Used by staff-facing CustomerExclusiveView to display session details.
    No auth required — session ID acts as a capability token.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )

    session = db.query(ExclusiveSession).filter(
        ExclusiveSession.id == session_uuid
    ).first()

    if not session:
        return SessionLookupResponse(exclusive_session=None)

    # Check if expired
    if session.status == ExclusiveSessionStatus.ACTIVE and session.expires_at < datetime.now(timezone.utc):
        session.status = ExclusiveSessionStatus.EXPIRED
        session.updated_at = datetime.now(timezone.utc)
        db.commit()

    remaining_seconds = 0
    if session.status == ExclusiveSessionStatus.ACTIVE:
        remaining_seconds = max(0, int((session.expires_at - datetime.now(timezone.utc)).total_seconds()))

    # Get merchant name
    merchant_name = None
    if session.merchant_id:
        merchant = db.query(Merchant).filter(Merchant.id == session.merchant_id).first()
        if merchant:
            merchant_name = merchant.name

    # Get exclusive title from merchant's active perk (if any)
    exclusive_title = None
    staff_instructions = None
    # For now, use generic values — these can be enriched later
    # when we add exclusive_id to the session model

    return SessionLookupResponse(
        exclusive_session=ExclusiveSessionResponse(
            id=str(session.id),
            merchant_id=session.merchant_id,
            charger_id=session.charger_id,
            expires_at=session.expires_at.isoformat(),
            activated_at=session.activated_at.isoformat(),
            remaining_seconds=remaining_seconds,
        ),
        merchant_name=merchant_name,
        exclusive_title=exclusive_title,
        staff_instructions=staff_instructions,
    )
```

**Note:** No auth required on this endpoint. The session UUID (128-bit random) acts as a capability token — only someone with the exact session ID can look it up. This is the same pattern used by verification codes.

---

## Step 3 — Wire CustomerExclusiveView to New Endpoint (P1)

**File:** `apps/merchant/app/components/CustomerExclusiveView.tsx`

Update the response interface and the `loadExclusiveSession` function:

**Lines 15-17** — Update interface:
```typescript
interface ExclusiveSessionResponse {
  exclusive_session: ExclusiveSession | null
  merchant_name: string | null
  exclusive_title: string | null
  staff_instructions: string | null
}
```

**Lines 35-65** — Update load function:
```typescript
const loadExclusiveSession = async (sessionId: string) => {
  try {
    setLoading(true);
    setError(null);

    const data = await fetchAPI<ExclusiveSessionResponse>(`/v1/exclusive/session/${sessionId}`);

    if (!data.exclusive_session) {
      setError('Exclusive session not found or expired');
      setLoading(false);
      return;
    }

    setSession(data.exclusive_session);
    setMerchantName(data.merchant_name || 'Merchant');
    setExclusiveName(data.exclusive_title || 'Active Exclusive');
    setStaffInstructions(data.staff_instructions || 'Verify customer activation');

  } catch (err) {
    console.error('Failed to load exclusive session:', err);
    setError(err instanceof ApiError ? err.message : 'Failed to load exclusive session');
  } finally {
    setLoading(false);
  }
};
```

**Remove** the comment block at lines 40-42 about the backend endpoint not existing.

---

## Step 4 — Replace Overview "Reserve Primary Experience" with Coming Soon (P2)

**File:** `apps/merchant/app/components/Overview.tsx`

**Lines 201-204** — Replace no-op button:
```typescript
// BEFORE
{primaryExperience.status === 'available' && (
  <button className="bg-neutral-900 text-white px-6 py-2 rounded-lg hover:bg-neutral-800 transition-colors">
    Reserve Primary Experience
  </button>
)}

// AFTER
{primaryExperience.status === 'available' && (
  <span className="inline-block px-4 py-2 bg-blue-50 text-blue-700 text-sm rounded-lg">
    Coming Soon
  </span>
)}
```

**Lines 206-209** — Remove "Join Waitlist" no-op button:
```typescript
// BEFORE
{primaryExperience.status === 'taken' && (
  <button className="border border-neutral-300 ...">
    Join Waitlist
  </button>
)}

// AFTER (remove entirely — status is always 'available' with no backend)
```

---

## Step 5 — Clean Up Empty TODO Block in Exclusives (P2)

**File:** `apps/merchant/app/components/Exclusives.tsx`

**Lines 82-91** — Simplify `getStatusColor`:
```typescript
// BEFORE
const getStatusColor = (exclusive: Exclusive) => {
  if (exclusive.daily_cap && exclusive.daily_cap > 0) {
    // TODO: Check activations today from analytics
    // For now, just check is_active
  }
  if (exclusive.is_active) {
    return 'bg-green-100 text-green-700';
  }
  return 'bg-neutral-100 text-neutral-600';
};

// AFTER
const getStatusColor = (exclusive: Exclusive) => {
  if (!exclusive.is_active) {
    return 'bg-neutral-100 text-neutral-600';
  }
  if (analytics && exclusive.daily_cap && analytics.activations >= exclusive.daily_cap) {
    return 'bg-amber-100 text-amber-700';
  }
  return 'bg-green-100 text-green-700';
};
```

**Lines 93-95** — Simplify `getStatusText`:
```typescript
// BEFORE
const getStatusText = (exclusive: Exclusive) => {
  // TODO: Check if cap reached from analytics
  return exclusive.is_active ? 'Active' : 'Paused';
};

// AFTER
const getStatusText = (exclusive: Exclusive) => {
  if (!exclusive.is_active) return 'Paused';
  if (analytics && exclusive.daily_cap && analytics.activations >= exclusive.daily_cap) return 'Cap Reached';
  return 'Active';
};
```

---

## QA Checklist

### Step 1 — merchant_id fallback
- [ ] Open Overview, Exclusives, CreateExclusive without `merchant_id` in localStorage → no API 404s in Network tab
- [ ] Set `merchant_id` in localStorage → pages load real data
- [ ] CreateExclusive form shows error message when merchant_id is missing

### Step 2 — Backend endpoint
- [ ] `GET /v1/exclusive/session/{valid_uuid}` returns session data with merchant name
- [ ] `GET /v1/exclusive/session/{nonexistent_uuid}` returns `{"exclusive_session": null}`
- [ ] `GET /v1/exclusive/session/not-a-uuid` returns 400
- [ ] Expired session returns `remaining_seconds: 0` and updates status to EXPIRED

### Step 3 — CustomerExclusiveView
- [ ] Navigate to `/merchant/exclusive/{session_id}` with valid session → shows merchant name, countdown, staff instructions
- [ ] Navigate with invalid session → shows "Exclusive Not Found" error state
- [ ] Countdown timer decrements every second
- [ ] Timer shows 0:00 when session expires

### Step 4 — Overview Primary Experience
- [ ] "Reserve Primary Experience" button is gone → replaced with "Coming Soon" badge
- [ ] "Join Waitlist" button is removed

### Step 5 — Exclusives status
- [ ] Active exclusive with no cap → green "Active" badge
- [ ] Active exclusive at cap → amber "Cap Reached" badge
- [ ] Paused exclusive → gray "Paused" badge
