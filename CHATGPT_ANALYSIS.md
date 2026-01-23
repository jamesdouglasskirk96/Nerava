# Nerava Platform - Current State Analysis for ChatGPT Review

## Executive Summary

The Nerava backend has been successfully deployed to AWS App Runner with a working discovery endpoint. Several issues remain that need to be addressed for production readiness.

---

## Current Infrastructure State

### ✅ Working

| Component | Status | Details |
|-----------|--------|---------|
| **App Runner** | Running | `https://api.nerava.network` |
| **Health Check** | Passing | `/healthz` returns healthy |
| **Discovery API** | Working | Returns chargers and merchants |
| **Photos** | Accessible | Static files serving correctly |
| **Database** | Connected | PostgreSQL RDS |
| **DNS (api)** | Configured | CNAME → App Runner |
| **MX Records** | Configured | Google Workspace |
| **SPF Record** | Added | Includes Google + SendGrid |

### ⚠️ Pending

| Component | Status | Blocker |
|-----------|--------|---------|
| **HTTPS (main site)** | Blocked | CloudFront needs console creation |
| **www subdomain** | Blocked | Depends on CloudFront |

### ❌ Issues to Fix

| Issue | Impact | Priority |
|-------|--------|----------|
| Duplicate Canyon Ridge charger | Data inconsistency | High |
| Generic merchant names (59/60) | Poor UX | Medium |
| API returns max 2 merchants | Missing data | High |

---

## Database State

```
Chargers: 9
Merchants: 60
Charger-Merchant Links: 60
Generic named merchants: 59 (need real names)

Merchants per charger:
  canyon_ridge_supercharger: 1  ← OLD (has Asadas Grill)
  charger_canyon_ridge: 12      ← NEW (has generic merchants)
  charger_ben_white: 12
  charger_mopac: 12
  charger_sunset_valley: 12
  charger_westlake: 11
```

---

## Issue #1: Duplicate Canyon Ridge Charger

### Problem
Two chargers exist for the same physical location:
- `canyon_ridge_supercharger` - Has 1 merchant (Asadas Grill with real name)
- `charger_canyon_ridge` - Has 12 merchants (generic names)

### Impact
- API returns both chargers for same location
- Confusing user experience
- Data inconsistency

### Recommended Fix
```sql
-- 1. Move Asadas Grill to new charger (preserve the real merchant)
INSERT INTO charger_merchants (charger_id, merchant_id, distance_m, walk_duration_s, is_primary, override_mode, exclusive_title, exclusive_description, created_at, updated_at)
SELECT 'charger_canyon_ridge', merchant_id, distance_m, walk_duration_s, is_primary, override_mode, exclusive_title, exclusive_description, NOW(), NOW()
FROM charger_merchants
WHERE charger_id = 'canyon_ridge_supercharger'
ON CONFLICT (charger_id, merchant_id) DO NOTHING;

-- 2. Delete old charger links
DELETE FROM charger_merchants WHERE charger_id = 'canyon_ridge_supercharger';

-- 3. Delete old charger
DELETE FROM chargers WHERE id = 'canyon_ridge_supercharger';
```

---

## Issue #2: Generic Merchant Names

### Problem
59 out of 60 merchants have names like:
- "Merchant 1 near Canyon Ridge Supercharger"
- "Merchant 2 near Tesla Supercharger - Mopac"

### Impact
- Poor user experience
- Unprofessional appearance
- Users can't identify businesses

### Root Cause
Seed script ran without Google Places API key

### Recommended Fix

**Option A: Google Places API (Best)**
```python
# Fetch real names using place_id
import requests

def get_place_name(place_id, api_key):
    url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {"place_id": place_id, "fields": "name,formatted_address", "key": api_key}
    response = requests.get(url, params=params)
    return response.json().get("result", {}).get("name")

# Update each merchant
for merchant in merchants_with_generic_names:
    real_name = get_place_name(merchant.id, GOOGLE_API_KEY)
    UPDATE merchants SET name = real_name WHERE id = merchant.id
```

**Option B: Manual curation**
- Export merchant place_ids
- Look up each on Google Maps manually
- Update database with real names

**Cost Estimate (Option A):**
- 59 Place Details API calls
- ~$0.017 per call = ~$1.00 total

---

## Issue #3: API Returns Max 2 Merchants

### Problem
Database has 12 merchants per charger, but API only returns 2.

### Evidence
```json
{
  "id": "charger_canyon_ridge",
  "name": "Canyon Ridge Supercharger",
  "merchants": 2  // Should be 12
}
```

### Root Cause
Hardcoded limit in API code (likely `[:2]` slice or `LIMIT 2`)

### Location to Check
```
app/routers/chargers.py
app/services/charger_service.py
app/routers/bootstrap.py (line ~245 based on grep)
```

### Recommended Fix
```python
# Find and change:
nearby_merchants = merchants[:2]
# To:
MAX_MERCHANTS = 12  # or make configurable
nearby_merchants = merchants[:MAX_MERCHANTS]
```

---

## CloudFront Setup (For You to Complete)

### What's Ready
- OAC created: `E21ERN8GGNCK1C`
- S3 bucket policy updated
- ACM certificate available
- Route53 fix script ready

### Console Steps
1. Go to: https://console.aws.amazon.com/cloudfront/v3/home#/distributions/create
2. Origin: `nerava.network.s3.us-east-1.amazonaws.com`
3. OAC: Select `nerava-network-oac`
4. CNAMEs: `nerava.network`, `www.nerava.network`
5. SSL: Select existing certificate
6. Custom errors: 403/404 → `/index.html` → 200
7. Create and wait for "Deployed" status

### After CloudFront
```bash
./FIX_ROUTE53_AFTER_CLOUDFRONT.sh <distribution-id>
```

---

## Recommended Action Priority

### Immediate (Today)
1. ✅ Create CloudFront distribution (you're doing this)
2. ✅ Run Route53 fix script after CloudFront deploys
3. 🔧 Fix API merchant limit (code change + deploy)

### Short-term (This Week)
4. 🔧 Consolidate duplicate Canyon Ridge chargers
5. 🔧 Update merchant names via Google Places API

### Verification After Fixes
```bash
# Test HTTPS
curl -I https://nerava.network
curl -I https://www.nerava.network

# Test API returns all merchants
curl -s "https://api.nerava.network/v1/chargers/discovery?lat=30.3971&lng=-97.6925" | jq '.chargers[] | select(.id == "charger_canyon_ridge") | .nearby_merchants | length'
# Should return: 12 (not 2)

# Test no duplicate chargers
curl -s "https://api.nerava.network/v1/chargers/discovery?lat=30.3971&lng=-97.6925" | jq '[.chargers[] | select(.name | contains("Canyon"))] | length'
# Should return: 1 (not 2)
```

---

## Questions for Decision

1. **Google Places API Key**: Do you have one available for updating merchant names?

2. **Merchant limit**: Should it be configurable per-request or fixed at 12?

3. **Domain consolidation**: Keep `charger_canyon_ridge` or rename to `canyon_ridge_supercharger`?

4. **Email testing**: After CloudFront, should we test email sending/receiving?

---

## Files Reference

| File | Purpose |
|------|---------|
| `EXECUTION_SUMMARY.md` | CloudFront console steps |
| `FIX_ROUTE53_AFTER_CLOUDFRONT.sh` | DNS fix script |
| `scripts/seed_production.py` | Database seeding |
| `scripts/update_merchant_names.py` | Merchant name updater (needs API key) |

---

## Architecture Diagram

```
                    ┌─────────────────┐
                    │   CloudFront    │ ← HTTPS termination
                    │  (pending)      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ nerava.network│   │ www.nerava.   │   │ api.nerava.   │
│ (S3 static)   │   │ network (S3)  │   │ network       │
└───────────────┘   └───────────────┘   └───────┬───────┘
                                                │
                                        ┌───────▼───────┐
                                        │  App Runner   │
                                        │  (FastAPI)    │
                                        └───────┬───────┘
                                                │
                            ┌───────────────────┼───────────────────┐
                            ▼                   ▼                   ▼
                    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
                    │  PostgreSQL   │   │    Redis      │   │  Static Files │
                    │    (RDS)      │   │ (ElastiCache) │   │  (in image)   │
                    └───────────────┘   └───────────────┘   └───────────────┘
```

---

*Generated: 2026-01-22*
*For: ChatGPT review of next steps*
