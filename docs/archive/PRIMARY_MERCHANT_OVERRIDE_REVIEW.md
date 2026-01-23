# Primary Merchant Override + Google Places Enrichment
## Code Review Report

**Review Date:** 2026-01-09
**Reviewer:** Claude Code (Principal Engineer Review)
**Implementation:** Cursor AI
**Feature:** Tesla Supercharger at Canyon Ridge → Asadas Grill Primary Override

---

## 1. High-Level Verdict

### **PASS WITH FIXES**

The implementation correctly delivers the core functionality:
- Primary merchant override logic is sound
- Google Places API (New) integration uses correct endpoints and field masks
- Caching strategy meets spec requirements
- UI properly displays exclusive badge and merchant hierarchy

**However, 1 critical and 1 moderate issue require remediation before production deployment.**

---

## 2. Files Changed

| File | Type | Summary |
|------|------|---------|
| `backend/alembic/versions/049_add_primary_merchant_override.py` | Migration | Adds `place_id`, `photo_urls`, `open_now`, `hours_json` to merchants; `is_primary`, `override_mode`, `suppress_others`, `exclusive_title/description` to charger_merchants |
| `backend/app/models/while_you_charge.py` | Model | SQLAlchemy model updates for new fields |
| `backend/app/services/google_places_new.py` | Service | Google Places API (New) client with field masks |
| `backend/app/services/merchant_enrichment.py` | Service | Enrichment service syncing Places data to Merchant |
| `backend/app/routers/drivers_domain.py` | Router | `/v1/drivers/merchants/open` endpoint with primary override logic |
| `backend/app/scripts/seed_canyon_ridge_override.py` | Script | Seed data for Canyon Ridge charger + Asadas Grill |
| `backend/tests/api/test_primary_merchant_override.py` | Test | Unit tests for primary override scenarios |
| `apps/driver/src/components/WhileYouCharge/FeaturedMerchantCard.tsx` | UI | Exclusive badge and photo fallback display |
| `backend/app/integrations/google_places_client.py` | Legacy | **SECURITY ISSUE: Contains hardcoded API key** |

---

## 3. Primary Merchant Override Validation

### ✅ Pre-charge State Logic
**Location:** `backend/app/routers/drivers_domain.py:403-450`

```python
# Query primary merchant override
primary_override = db.query(ChargerMerchant).filter(
    ChargerMerchant.charger_id == charger_id,
    ChargerMerchant.is_primary == True
).first()

if state == "pre-charge" and primary_override and primary_override.suppress_others:
    # Return only primary merchant
    return [format_merchant_response(primary_override.merchant, primary_override)]
```

**Verdict:** ✅ Correct - Returns only 1 merchant when `suppress_others=True` in pre-charge state

### ✅ Charging State Logic
**Location:** `backend/app/routers/drivers_domain.py:452-480`

```python
if state == "charging":
    merchants = []
    # Primary first
    if primary_override:
        merchants.append(format_merchant_response(primary_override.merchant, primary_override))
    # Secondary merchants (up to 2)
    secondary = db.query(ChargerMerchant).filter(
        ChargerMerchant.charger_id == charger_id,
        ChargerMerchant.is_primary == False
    ).limit(2).all()
    merchants.extend([format_merchant_response(cm.merchant, cm) for cm in secondary])
    return merchants
```

**Verdict:** ✅ Correct - Returns primary + up to 2 secondary (3 total max)

### ✅ Exclusive Badge Fields
**Location:** `backend/app/models/while_you_charge.py`

| Field | Type | Purpose |
|-------|------|---------|
| `exclusive_title` | String(255) | "Free Margarita" |
| `exclusive_description` | Text | "Free Margarita (Charging Exclusive)" |
| `is_primary` | Boolean | Primary merchant flag |
| `suppress_others` | Boolean | Pre-charge exclusivity |
| `override_mode` | String(50) | "PRE_CHARGE_ONLY" / "ALWAYS" |

**Verdict:** ✅ Schema correctly supports exclusive badge requirements

---

## 4. Google Places Integration Validation

### ✅ API Version
**Location:** `backend/app/services/google_places_new.py:15`

```python
PLACES_API_BASE = "https://places.googleapis.com/v1"
```

**Verdict:** ✅ Correct - Uses Google Places API (New), not deprecated Places Web Service

### ✅ Field Masks
**Location:** `backend/app/services/google_places_new.py:45-60`

```python
FIELD_MASKS = {
    "basic": "places.id,places.displayName,places.formattedAddress,places.location",
    "details": "id,displayName,formattedAddress,location,currentOpeningHours,regularOpeningHours,photos,rating,userRatingCount,priceLevel",
    "photos": "photos",
    "status": "currentOpeningHours.openNow"
}
```

| Operation | Field Mask | Quota Impact |
|-----------|------------|--------------|
| Nearby Search | `places.id,places.displayName,...` | Minimal |
| Place Details | `id,displayName,...,photos,rating` | Standard |
| Open Status | `currentOpeningHours.openNow` | Minimal |

**Verdict:** ✅ Correct - Field masks properly limit returned data and reduce API quota usage

### ✅ Server-Side Only Calls
**Verification:** Grep for `VITE_.*GOOGLE|VITE_.*PLACES|VITE_.*API_KEY` returned **no matches**

**Verdict:** ✅ Correct - No client-side Places API exposure. All calls go through backend services.

---

## 5. Caching Validation

### ✅ Cache TTLs
**Location:** `backend/app/core/config.py`

| Cache Type | TTL | Spec Requirement | Status |
|------------|-----|------------------|--------|
| Place Details | 86400s (24h) | 24 hours | ✅ |
| Open Status | 300s (5min) | 5-10 minutes | ✅ |
| Photos | 604800s (7d) | 7 days | ✅ |

**Implementation:** `backend/app/services/google_places_new.py` uses `LayeredCache` with these TTLs:

```python
class GooglePlacesClient:
    def __init__(self):
        self.details_cache = LayeredCache(ttl_seconds=settings.MERCHANT_CACHE_TTL_SECONDS)  # 24h
        self.status_cache = LayeredCache(ttl_seconds=settings.MERCHANT_STATUS_CACHE_TTL_SECONDS)  # 5min
        self.photo_cache = LayeredCache(ttl_seconds=settings.MERCHANT_PHOTO_CACHE_TTL_SECONDS)  # 7d
```

**Verdict:** ✅ Correct - All TTLs meet spec requirements

---

## 6. Security Validation

### 🔴 CRITICAL: Hardcoded API Key
**Location:** `backend/app/integrations/google_places_client.py:21`

```python
# Hardcoded API key (no longer reads from environment variables)
GOOGLE_PLACES_API_KEY = "AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg"
```

**Risk:** HIGH
**Impact:** API key exposed in source control. If repo is public or compromised, key can be abused for unauthorized API calls, potentially incurring significant billing.

**Required Fix:**
```python
# Move to environment variable
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
```

### ✅ No Client-Side API Keys
Verified: No `VITE_GOOGLE_*` or `VITE_PLACES_*` environment variables in frontend code.

### ⚠️ MODERATE: No Places API Rate Limiting
**Analysis:** `backend/app/services/auth/rate_limit.py` only covers OTP authentication. No rate limiting exists for Google Places API calls.

**Risk:** MEDIUM
**Impact:** A compromised or misbehaving client could trigger excessive Places API calls, leading to:
- API quota exhaustion
- Unexpected billing
- Service degradation

**Recommended Fix:** Add per-user/per-IP rate limiting for `/v1/drivers/merchants/open` endpoint.

---

## 7. Data Model & Migrations Validation

### ✅ Migration 049
**Location:** `backend/alembic/versions/049_add_primary_merchant_override.py`

**Merchants Table Additions:**
| Column | Type | Purpose |
|--------|------|---------|
| `place_id` | String(255) | Google Places ID |
| `photo_urls` | JSON | Array of photo URLs |
| `open_now` | Boolean | Current open status |
| `hours_json` | JSON | Operating hours |
| `rating` | Float | Google rating |
| `user_rating_count` | Integer | Number of reviews |

**ChargerMerchant Table Additions:**
| Column | Type | Purpose |
|--------|------|---------|
| `is_primary` | Boolean | Primary merchant flag |
| `override_mode` | String(50) | Override behavior mode |
| `suppress_others` | Boolean | Pre-charge exclusivity |
| `exclusive_title` | String(255) | Badge title |
| `exclusive_description` | Text | Badge description |

**Verdict:** ✅ Schema correctly supports all feature requirements

---

## 8. Driver UI Validation

### ✅ FeaturedMerchantCard Component
**Location:** `apps/driver/src/components/WhileYouCharge/FeaturedMerchantCard.tsx`

**Exclusive Badge Logic:**
```tsx
{(merchant.is_primary || merchant.badges?.includes('Exclusive')) && (
  <Badge variant="exclusive">
    {merchant.exclusive_title || 'Exclusive'}
  </Badge>
)}
```

**Open/Closed Badge:**
```tsx
<Badge variant={merchant.open_now ? 'success' : 'muted'}>
  {merchant.open_now ? 'Open' : 'Closed'}
</Badge>
```

**Photo Fallback Chain:**
```tsx
const photoUrl = merchant.photo_urls?.[0] || merchant.photo_url;
// Falls back to PhotoPlaceholder component if no photos
```

**Verdict:** ✅ UI correctly implements exclusive badge, open/closed status, and photo fallback

---

## 9. Merchant Onboarding Validation

### ✅ Enrichment Service
**Location:** `backend/app/services/merchant_enrichment.py`

- `enrich_from_google_places()` - Full sync on merchant creation/update
- `refresh_open_status()` - Lightweight status refresh (5-10 min intervals)

**Verdict:** ✅ Enrichment properly separates full sync from lightweight status refresh

---

## 10. Tests & CI

### ✅ Unit Tests Present
**Location:** `backend/tests/api/test_primary_merchant_override.py`

| Test Case | Status |
|-----------|--------|
| `test_primary_override_pre_charge` | ✅ Covered |
| `test_primary_override_charging` | ✅ Covered |
| `test_no_primary_override` | ✅ Covered |

**Test Coverage:**
- Pre-charge state returns only primary merchant ✅
- Charging state returns primary first ✅
- Non-primary fallback behavior ✅
- Exclusive title/description in response ✅

### ⚠️ Missing Tests
- E2E test for full flow (charger → primary merchant → exclusive badge on UI)
- Integration test for Google Places API caching behavior
- Load test for Places API rate limiting

---

## 11. Bugs / Risks / Edge Cases

| Issue | Severity | Description |
|-------|----------|-------------|
| Hardcoded API Key | 🔴 CRITICAL | API key in source code at `google_places_client.py:21` |
| No Places Rate Limiting | ⚠️ MODERATE | No per-user/per-IP rate limit on Places API calls |
| Cache Stampede | ⚠️ LOW | Multiple simultaneous requests could bypass cache on expiry |
| Missing E2E Tests | ⚠️ LOW | No end-to-end test coverage for primary override flow |

### Edge Cases Handled
- ✅ No primary merchant: Falls back to normal merchant search
- ✅ Multiple primary merchants: Query returns first match
- ✅ Missing photos: Fallback to placeholder
- ✅ Closed merchant: Still displayed with "Closed" badge

### Edge Cases Not Handled
- ⚠️ Primary merchant deleted: No cascade handling
- ⚠️ Google Places API failure: No circuit breaker

---

## 12. Required Fixes

### 🔴 CRITICAL (Must Fix Before Deploy)

1. **Remove hardcoded API key**
   - **File:** `backend/app/integrations/google_places_client.py:21`
   - **Action:** Replace hardcoded key with environment variable
   - **Priority:** P0 - Security vulnerability

```python
# BEFORE (INSECURE)
GOOGLE_PLACES_API_KEY = "AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg"

# AFTER (SECURE)
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
if not GOOGLE_PLACES_API_KEY:
    raise ValueError("GOOGLE_PLACES_API_KEY environment variable is required")
```

2. **Rotate compromised API key**
   - **Action:** Generate new API key in Google Cloud Console
   - **Action:** Restrict new key to Places API only
   - **Action:** Add IP/referrer restrictions

### ⚠️ RECOMMENDED (Should Fix)

3. **Add Places API rate limiting**
   - **File:** `backend/app/routers/drivers_domain.py`
   - **Action:** Add rate limit decorator to `/v1/drivers/merchants/open`
   - **Limit:** 30 requests per minute per user

4. **Add circuit breaker for Places API**
   - **File:** `backend/app/services/google_places_new.py`
   - **Action:** Implement circuit breaker pattern for API failures

---

## 13. Verification Checklist

### Pre-Deployment Checklist

| Check | Status | Notes |
|-------|--------|-------|
| API key moved to environment variable | ⬜ TODO | Critical security fix |
| API key rotated in Google Cloud | ⬜ TODO | Old key compromised |
| Places API field masks verified | ✅ PASS | Correctly implemented |
| Caching TTLs match spec | ✅ PASS | 24h/5min/7d |
| No client-side API key exposure | ✅ PASS | All calls server-side |
| Primary override returns 1 merchant (pre-charge) | ✅ PASS | Verified in code |
| Charging state returns 3 merchants max | ✅ PASS | Primary + 2 secondary |
| Exclusive badge displays correctly | ✅ PASS | UI component verified |
| Unit tests passing | ✅ PASS | 3 test cases |
| Migration applied successfully | ✅ PASS | Schema changes verified |

### Seed Data Verification (Canyon Ridge)

| Item | Expected | Status |
|------|----------|--------|
| Charger | Tesla Supercharger, 500 W Canyon Ridge Dr | ✅ Seeded |
| Primary Merchant | Asadas Grill, 501 W Canyon Ridge Dr | ✅ Seeded |
| Exclusive Title | "Free Margarita" | ✅ Configured |
| Exclusive Description | "Free Margarita (Charging Exclusive)" | ✅ Configured |
| suppress_others | true | ✅ Configured |
| override_mode | "PRE_CHARGE_ONLY" | ✅ Configured |

---

## Summary

**Implementation Quality:** 8/10

The Cursor AI implementation correctly delivers the core functionality for primary merchant override and Google Places enrichment. The architecture is sound, field masks are properly configured, and caching meets spec requirements.

**However, the hardcoded API key is a critical security vulnerability that must be addressed immediately before any production deployment.**

| Category | Score | Notes |
|----------|-------|-------|
| Functionality | 9/10 | Core feature works correctly |
| Security | 5/10 | Hardcoded API key is critical |
| Testing | 7/10 | Good unit tests, missing E2E |
| Code Quality | 8/10 | Clean, well-structured |
| Documentation | 7/10 | Adequate inline comments |

**Final Verdict: PASS WITH FIXES** - Deploy after addressing critical security issue.
