# Backend Gaps for iOS App "Real" Functionality

**Date**: 2026-01-27  
**Scope**: Missing backend endpoints, data models, and integrations required for full production functionality

---

## Executive Summary

The iOS driver app has **6 critical backend gaps** (P0) and **4 enhancement gaps** (P1/P2) that prevent full production functionality. Most core flows work (auth, exclusive sessions, merchant discovery), but new features (amenity votes, filters) and data sync (favorites) need backend support.

**Overall Status**: Core functionality works, but new features are frontend-only.

---

## 1) Gap List by Category

### Auth & Sessions ✅ MOSTLY COMPLETE
**Status**: Production-ready

- ✅ OTP authentication (`/v1/auth/otp/start`, `/v1/auth/otp/verify`)
- ✅ Token refresh (`/v1/auth/refresh`)
- ✅ Exclusive session activation (`/v1/exclusive/activate`)
- ✅ Exclusive session completion (`/v1/exclusive/complete`)
- ✅ Active exclusive check (`/v1/exclusive/active`)
- ✅ Visit verification (`/v1/exclusive/verify`)

**Gaps**: None (auth flow is complete)

---

### Merchants & Chargers ✅ MOSTLY COMPLETE
**Status**: Production-ready

- ✅ Intent capture (`/v1/intent/capture`) - finds chargers and merchants
- ✅ Merchant details (`/v1/merchants/{merchant_id}`)
- ✅ Merchants for charger (`/v1/drivers/merchants/open`)
- ✅ Location check (`/v1/drivers/location/check`)

**Gaps**: 
- ⚠️ **Merchant amenities field missing** (P1)
  - Frontend expects: `merchant.amenities: { bathroom: { upvotes, downvotes }, wifi: { upvotes, downvotes } }`
  - Backend provides: No amenities field in `MerchantInfo` schema
  - Location: `backend/app/schemas/merchants.py` line 8-23, `apps/driver/src/types/index.ts` line 52-60

---

### Favorites ⚠️ PARTIAL SYNC
**Status**: Backend exists, frontend uses localStorage

- ✅ Backend endpoints exist:
  - `GET /v1/merchants/favorites` - List favorites
  - `POST /v1/merchants/{merchant_id}/favorite` - Add favorite
  - `DELETE /v1/merchants/{merchant_id}/favorite` - Remove favorite
- ✅ Database model: `FavoriteMerchant` table exists
- ⚠️ **Frontend syncs but falls back to localStorage**
  - Location: `apps/driver/src/contexts/FavoritesContext.tsx` lines 14-79
  - Issue: Favorites work offline but don't sync across devices until user authenticates
  - Impact: Low (works but not ideal UX)

**Gaps**: 
- ⚠️ **Favorites sync on app load** (P2 - enhancement)
  - Current: Favorites load from localStorage, sync to backend if authenticated
  - Better: Always sync from backend when authenticated, use localStorage as cache

---

### Amenity Votes ❌ MISSING BACKEND
**Status**: Frontend-only (localStorage)

**Gaps**:
- ❌ **No amenity votes API** (P0 - blocker for production)
  - Frontend stores votes in localStorage: `nerava_amenity_votes_{merchantId}`
  - Location: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx` lines 97-119, 450-470
  - Expected: Votes should sync across devices and aggregate across users
  - Missing:
    - Database model for amenity votes
    - API endpoint to submit vote: `POST /v1/merchants/{merchant_id}/amenities/{amenity}/vote`
    - API endpoint to get aggregated votes: Included in `GET /v1/merchants/{merchant_id}` response
    - Vote aggregation logic (count upvotes/downvotes per merchant+amenity)

**Required Implementation**:
1. Database migration: Create `amenity_votes` table
   ```sql
   CREATE TABLE amenity_votes (
     id SERIAL PRIMARY KEY,
     merchant_id VARCHAR NOT NULL REFERENCES merchants(id),
     user_id INTEGER NOT NULL REFERENCES users(id),
     amenity VARCHAR(20) NOT NULL, -- 'bathroom' or 'wifi'
     vote_type VARCHAR(10) NOT NULL, -- 'up' or 'down'
     created_at TIMESTAMP DEFAULT NOW(),
     UNIQUE(merchant_id, user_id, amenity)
   );
   ```
2. API endpoint: `POST /v1/merchants/{merchant_id}/amenities/{amenity}/vote`
   - Request: `{ vote_type: 'up' | 'down' }`
   - Response: `{ ok: true, upvotes: number, downvotes: number }`
3. Update `MerchantInfo` schema to include `amenities` field
4. Update `get_merchant_details()` to aggregate and return amenity vote counts

---

### Primary Filters ❌ MISSING BACKEND SUPPORT
**Status**: Frontend-only filtering

**Gaps**:
- ❌ **No backend filter support** (P1 - enhancement)
  - Frontend filters merchants client-side by `types` array
  - Location: `apps/driver/src/components/DriverHome/DriverHome.tsx` lines 97-130
  - Current: Filters applied after API response (client-side)
  - Missing:
    - Filter parameters in intent capture: `POST /v1/intent/capture?filters=bathroom,food,wifi`
    - Filter parameters in merchants endpoint: `GET /v1/drivers/merchants/open?filters=bathroom,food`
    - Backend filtering logic (filter by merchant types/categories)

**Required Implementation**:
1. Add `filters` query parameter to intent capture endpoint
2. Add filtering logic in `get_merchants_for_intent()` service
3. Map filter IDs to merchant types:
   - `bathroom` → Check amenity votes (future) or assume all have bathrooms
   - `food` → Filter by `types` containing 'restaurant', 'food', 'cafe', etc.
   - `wifi` → Check amenity votes (future) or filter by type
   - `pets` → Filter by `types` containing 'pet', 'veterinary'
   - `music` → Future enhancement (no backend data yet)
   - `patio` → Future enhancement (no backend data yet)

**Note**: This is P1 (enhancement) because frontend filtering works, but backend filtering would be more efficient and enable filter persistence.

---

### Notifications ⚠️ PARTIAL
**Status**: Backend service exists, no iOS push integration

- ✅ Backend notification service exists (`backend/app/services/notify.py`)
- ✅ Apple Wallet PassKit push exists (`backend/app/services/apple_pass_push.py`)
- ❌ **No iOS app push notifications** (P1 - enhancement)
  - Missing: FCM/APNS integration for iOS app notifications
  - Missing: Device token registration endpoint
  - Missing: Push notification triggers for:
    - Exclusive session expiring soon (15 min warning)
    - New merchants available at charger
    - Favorite merchant has new exclusive offer

**Required Implementation**:
1. Device token registration: `POST /v1/drivers/device-token`
2. FCM/APNS service integration
3. Notification triggers for exclusive expiration, new merchants, etc.

---

### Analytics ✅ COMPLETE
**Status**: Production-ready

- ✅ PostHog integration in frontend (`apps/driver/src/analytics/index.ts`)
- ✅ Backend analytics service (`backend/app/services/analytics.py`)
- ✅ Native events endpoint (`/v1/native/events/session-events`)
- ✅ Event tracking throughout app

**Gaps**: None

---

### Data Models & Schemas ⚠️ MISSING AMENITIES FIELD

**Gaps**:
- ❌ **MerchantInfo schema missing amenities** (P0 - blocker)
  - File: `backend/app/schemas/merchants.py` line 8-23
  - Missing field: `amenities: Optional[Dict[str, Dict[str, int]]]`
  - Required for: AmenityVotes component to display vote counts from API

---

## 2) Exact File Locations

### Frontend Expectations

**Amenity Votes**:
- `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx` lines 97-119 (loads from API)
- `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx` lines 450-470 (handles voting)
- `apps/driver/src/types/index.ts` line 52-60 (expects `amenities` field)

**Primary Filters**:
- `apps/driver/src/components/DriverHome/DriverHome.tsx` lines 97-130 (filtering logic)
- `apps/driver/src/components/shared/PrimaryFilters.tsx` (UI component)

**Favorites**:
- `apps/driver/src/contexts/FavoritesContext.tsx` lines 33-79 (syncs with backend but uses localStorage)

### Backend Missing Pieces

**Amenity Votes**:
- No database model: Need `amenity_votes` table
- No API endpoint: Need `POST /v1/merchants/{merchant_id}/amenities/{amenity}/vote`
- No schema field: `MerchantInfo.amenities` missing in `backend/app/schemas/merchants.py`

**Primary Filters**:
- No filter parameter: `POST /v1/intent/capture` doesn't accept `filters` query param
- No filter logic: `backend/app/services/intent_service.py` doesn't filter by amenities

---

## 3) Missing Endpoints & Data Fields

### P0 Blockers (Must Fix)

#### 1. Amenity Votes API
**Endpoint**: `POST /v1/merchants/{merchant_id}/amenities/{amenity}/vote`
- **Method**: POST
- **Auth**: Required (Bearer token)
- **Path params**: `merchant_id` (string), `amenity` ('bathroom' | 'wifi')
- **Request body**:
  ```json
  {
    "vote_type": "up" | "down"
  }
  ```
- **Response**:
  ```json
  {
    "ok": true,
    "upvotes": 42,
    "downvotes": 3
  }
  ```
- **File**: `backend/app/routers/merchants.py` (add new endpoint)

**Endpoint**: Update `GET /v1/merchants/{merchant_id}` response
- **Add to MerchantInfo schema**:
  ```python
  amenities: Optional[Dict[str, Dict[str, int]]] = None
  # Example: {"bathroom": {"upvotes": 42, "downvotes": 3}, "wifi": {"upvotes": 38, "downvotes": 7}}
  ```
- **File**: `backend/app/schemas/merchants.py` line 8-23

#### 2. Database Migration for Amenity Votes
**Migration file**: `backend/alembic/versions/055_add_amenity_votes_table.py`
```python
def upgrade():
    op.create_table(
        'amenity_votes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amenity', sa.String(20), nullable=False),  # 'bathroom' or 'wifi'
        sa.Column('vote_type', sa.String(10), nullable=False),  # 'up' or 'down'
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('merchant_id', 'user_id', 'amenity', name='uq_amenity_vote')
    )
    op.create_index('idx_amenity_votes_merchant', 'amenity_votes', ['merchant_id', 'amenity'])
```

### P1 Enhancements (Should Fix)

#### 3. Filter Support in Intent Capture
**Endpoint**: `POST /v1/intent/capture?filters=bathroom,food,wifi`
- **Query param**: `filters` (comma-separated list)
- **File**: `backend/app/routers/intent.py` line 53-245
- **Service**: `backend/app/services/intent_service.py` - add filter logic

#### 4. Filter Support in Merchants Endpoint
**Endpoint**: `GET /v1/drivers/merchants/open?charger_id=X&filters=bathroom,food`
- **Query param**: `filters` (comma-separated list)
- **File**: `backend/app/routers/drivers_domain.py` or `backend/app/routers/while_you_charge.py`

---

## 4) Prioritized List

### P0 Blockers (Must Fix Before Production)

1. **Amenity Votes Backend API** ⚠️ CRITICAL
   - Impact: Votes don't sync across devices, can't aggregate user feedback
   - Effort: 4-6 hours
   - Files: Database migration, API endpoint, schema update, service logic

2. **MerchantInfo.amenities Field** ⚠️ CRITICAL
   - Impact: Frontend can't display vote counts from API
   - Effort: 1 hour (schema + service update)
   - Files: `backend/app/schemas/merchants.py`, `backend/app/services/merchant_details.py`

### P1 High Priority (Should Fix Soon)

3. **Primary Filters Backend Support** 
   - Impact: More efficient filtering, enables filter persistence
   - Effort: 3-4 hours
   - Files: Intent capture endpoint, merchants endpoint, filtering service

4. **Favorites Sync Improvement**
   - Impact: Better UX (favorites sync on load, not just on toggle)
   - Effort: 1 hour
   - Files: `apps/driver/src/contexts/FavoritesContext.tsx`

### P2 Medium Priority (Nice to Have)

5. **iOS Push Notifications**
   - Impact: Better engagement (session expiration warnings, new merchants)
   - Effort: 8-12 hours (FCM/APNS setup, device token management, notification triggers)
   - Files: New notification service, device token endpoint, notification triggers

6. **Filter Persistence**
   - Impact: Users don't lose filter selections on refresh
   - Effort: 1 hour (localStorage + optional backend sync)
   - Files: `apps/driver/src/components/DriverHome/DriverHome.tsx`

---

## 5) Cursor-Ready Implementation Plan

### Phase 1: Amenity Votes Backend (P0 - 4-6 hours)

#### Step 1: Database Migration
**File**: `backend/alembic/versions/055_add_amenity_votes_table.py`
- Create `amenity_votes` table with columns: id, merchant_id, user_id, amenity, vote_type, created_at
- Add unique constraint on (merchant_id, user_id, amenity)
- Add index on (merchant_id, amenity) for aggregation queries

#### Step 2: Database Model
**File**: `backend/app/models/while_you_charge.py` (add after FavoriteMerchant)
```python
class AmenityVote(Base):
    __tablename__ = "amenity_votes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amenity = Column(String(20), nullable=False)  # 'bathroom' or 'wifi'
    vote_type = Column(String(10), nullable=False)  # 'up' or 'down'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('merchant_id', 'user_id', 'amenity', name='uq_amenity_vote'),
        Index('idx_amenity_votes_merchant', 'merchant_id', 'amenity'),
    )
```

#### Step 3: API Endpoint
**File**: `backend/app/routers/merchants.py` (add after favorites endpoints)
```python
@router.post("/{merchant_id}/amenities/{amenity}/vote")
def vote_amenity(
    merchant_id: str,
    amenity: str,  # 'bathroom' or 'wifi'
    request: AmenityVoteRequest,  # { vote_type: 'up' | 'down' }
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    # Validate amenity
    if amenity not in ['bathroom', 'wifi']:
        raise HTTPException(400, "Invalid amenity")
    
    # Check if merchant exists
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(404, "Merchant not found")
    
    # Get or create vote (upsert)
    vote = db.query(AmenityVote).filter(
        AmenityVote.merchant_id == merchant_id,
        AmenityVote.user_id == driver.id,
        AmenityVote.amenity == amenity
    ).first()
    
    if vote:
        # Update existing vote (toggle if same type, change if different)
        if vote.vote_type == request.vote_type:
            # Toggle: remove vote
            db.delete(vote)
        else:
            # Change vote type
            vote.vote_type = request.vote_type
    else:
        # Create new vote
        vote = AmenityVote(
            merchant_id=merchant_id,
            user_id=driver.id,
            amenity=amenity,
            vote_type=request.vote_type
        )
        db.add(vote)
    
    db.commit()
    
    # Aggregate votes for response
    upvotes = db.query(func.count(AmenityVote.id)).filter(
        AmenityVote.merchant_id == merchant_id,
        AmenityVote.amenity == amenity,
        AmenityVote.vote_type == 'up'
    ).scalar()
    
    downvotes = db.query(func.count(AmenityVote.id)).filter(
        AmenityVote.merchant_id == merchant_id,
        AmenityVote.amenity == amenity,
        AmenityVote.vote_type == 'down'
    ).scalar()
    
    return {
        "ok": True,
        "upvotes": upvotes,
        "downvotes": downvotes
    }
```

#### Step 4: Update MerchantInfo Schema
**File**: `backend/app/schemas/merchants.py` line 8-23
```python
class MerchantInfo(BaseModel):
    id: str
    name: str
    category: str
    photo_url: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    description: Optional[str] = None
    hours_today: Optional[str] = None
    address: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None
    activations_today: Optional[int] = 0
    verified_visits_today: Optional[int] = 0
    amenities: Optional[Dict[str, Dict[str, int]]] = None  # NEW: {"bathroom": {"upvotes": 42, "downvotes": 3}, "wifi": {...}}
```

#### Step 5: Update Merchant Details Service
**File**: `backend/app/services/merchant_details.py` line 276-290
```python
# Aggregate amenity votes
from sqlalchemy import func
from app.models.while_you_charge import AmenityVote

amenity_votes = {}
for amenity in ['bathroom', 'wifi']:
    upvotes = db.query(func.count(AmenityVote.id)).filter(
        AmenityVote.merchant_id == merchant.id,
        AmenityVote.amenity == amenity,
        AmenityVote.vote_type == 'up'
    ).scalar() or 0
    
    downvotes = db.query(func.count(AmenityVote.id)).filter(
        AmenityVote.merchant_id == merchant.id,
        AmenityVote.amenity == amenity,
        AmenityVote.vote_type == 'down'
    ).scalar() or 0
    
    amenity_votes[amenity] = {"upvotes": upvotes, "downvotes": downvotes}

merchant_info = MerchantInfo(
    # ... existing fields ...
    amenities=amenity_votes if amenity_votes.get('bathroom') or amenity_votes.get('wifi') else None
)
```

#### Step 6: Update Frontend to Use API
**File**: `apps/driver/src/services/api.ts` (add after verifyVisit)
```typescript
export interface AmenityVoteRequest {
  vote_type: 'up' | 'down'
}

export interface AmenityVoteResponse {
  ok: boolean
  upvotes: number
  downvotes: number
}

export async function voteAmenity(
  merchantId: string,
  amenity: 'bathroom' | 'wifi',
  voteType: 'up' | 'down'
): Promise<AmenityVoteResponse> {
  return fetchAPI<AmenityVoteResponse>(
    `/v1/merchants/${merchantId}/amenities/${amenity}/vote`,
    {
      method: 'POST',
      body: JSON.stringify({ vote_type: voteType }),
    }
  )
}

export function useVoteAmenity() {
  return useMutation({
    mutationFn: ({ merchantId, amenity, voteType }: { merchantId: string; amenity: 'bathroom' | 'wifi'; voteType: 'up' | 'down' }) =>
      voteAmenity(merchantId, amenity, voteType),
  })
}
```

**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`
- Replace localStorage voting with API call
- Use `useVoteAmenity()` hook
- Update local state from API response

### Phase 2: Primary Filters Backend Support (P1 - 3-4 hours)

#### Step 1: Add Filter Parameter to Intent Capture
**File**: `backend/app/routers/intent.py` line 53-58
```python
@router.post("/capture", response_model=CaptureIntentResponse)
async def capture_intent(
    request: CaptureIntentRequest,
    filters: Optional[str] = Query(None, description="Comma-separated filter IDs: bathroom,food,wifi,pets,music,patio"),
    http_request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    # Parse filters
    filter_list = filters.split(',') if filters else []
    # Pass to service
    merchants = await get_merchants_for_intent(db, ..., filters=filter_list)
```

#### Step 2: Add Filtering Logic
**File**: `backend/app/services/intent_service.py`
```python
def filter_merchants_by_amenities(merchants: List[MerchantSummary], filters: List[str]) -> List[MerchantSummary]:
    if not filters:
        return merchants
    
    filtered = []
    for merchant in merchants:
        types_lower = [t.lower() for t in (merchant.types or [])]
        
        matches = []
        for filter_id in filters:
            if filter_id == 'food':
                matches.append(any('restaurant' in t or 'food' in t or 'cafe' in t for t in types_lower))
            elif filter_id == 'pets':
                matches.append(any('pet' in t or 'veterinary' in t for t in types_lower))
            # ... other filters
        
        if all(matches):  # AND logic: merchant must match all selected filters
            filtered.append(merchant)
    
    return filtered
```

---

## Summary

### Critical Path to Production

1. **Amenity Votes Backend** (P0) - 4-6 hours
   - Database migration + model
   - API endpoint
   - Schema update
   - Frontend integration

2. **MerchantInfo.amenities Field** (P0) - 1 hour
   - Schema update
   - Service aggregation logic

**Total P0 Effort**: 5-7 hours

### Post-Launch Enhancements

3. **Primary Filters Backend** (P1) - 3-4 hours
4. **Favorites Sync Improvement** (P1) - 1 hour
5. **iOS Push Notifications** (P2) - 8-12 hours

---

## Testing Checklist

### Amenity Votes
- [ ] Vote endpoint creates/updates vote correctly
- [ ] Vote endpoint toggles vote if same type clicked
- [ ] Vote endpoint aggregates counts correctly
- [ ] Merchant details includes amenity vote counts
- [ ] Frontend displays vote counts from API
- [ ] Frontend submits votes to API (not localStorage)
- [ ] Votes sync across devices for same user

### Primary Filters
- [ ] Intent capture accepts `filters` query param
- [ ] Filtering logic correctly filters merchants
- [ ] Empty result set handled gracefully
- [ ] Filter combinations work (AND logic)

---

## Notes

- **Favorites**: Current implementation works (localStorage + backend sync), but could be improved to always sync from backend on load
- **Analytics**: Complete (PostHog + backend analytics service)
- **Notifications**: Backend service exists but no iOS push integration yet
- **Auth**: Complete and production-ready
