# Nerava Production Gaps Report

**Generated:** January 23, 2026
**Scope:** Admin Portal & Merchant Portal

---

## Executive Summary

Both the Admin Portal and Merchant Portal have significant UI/UX work completed but rely heavily on **mock data** and **incomplete backend integrations**. The primary gaps are:

1. **Admin Portal**: Dashboard, Overrides, Logs, and Exclusives management use mock data
2. **Merchant Portal**: Billing, Settings, and Primary Experience are UI-only with no backend
3. **Missing APIs**: Several frontend components call endpoints that don't exist
4. **Two Admin Implementations**: Redundant admin apps that should be consolidated

---

## Critical Production Gaps

### 🔴 Priority 1: Blocking Features

| Gap | Component | Impact | Effort |
|-----|-----------|--------|--------|
| Admin Overrides API | Admin Portal | Cannot force-close sessions or emergency pause | Medium |
| Merchant Billing Integration | Merchant Portal | No real payment processing | High |
| Admin Login Endpoint | Admin Portal | May not be able to authenticate admins | Low |
| Exclusive Toggle API | Admin Portal | Cannot pause/resume exclusives | Low |

### 🟡 Priority 2: Important but Workaroundable

| Gap | Component | Impact | Effort |
|-----|-----------|--------|--------|
| Audit Log API | Admin Portal | No compliance/audit trail visibility | Medium |
| Settings Save | Merchant Portal | Business info changes not persisted | Low |
| Charging Locations API | Admin Portal | Location management uses mock data | Medium |
| Primary Experience Backend | Merchant Portal | Feature is UI-only | Medium |

### 🟢 Priority 3: Nice to Have

| Gap | Component | Impact | Effort |
|-----|-----------|--------|--------|
| Dashboard Real-Time Alerts | Admin Portal | Alerts are mocked | Medium |
| Square Integration | Merchant Portal | POS sync not implemented | High |
| Notification Preferences | Merchant Portal | Cannot configure notifications | Low |

---

## Admin Portal Gaps

### Missing Backend Endpoints

```
❌ POST /v1/auth/admin/login          - Admin authentication (frontend calls this)
❌ POST /v1/admin/exclusives/{id}/toggle - Toggle exclusive on/off
❌ POST /v1/admin/sessions/force-close   - Force close sessions at location
❌ POST /v1/admin/overrides/emergency-pause - Emergency pause system
❌ POST /v1/admin/overrides/reset-caps   - Reset daily/monthly caps
❌ GET  /v1/admin/logs                   - Retrieve audit logs
❌ GET  /v1/admin/charging-locations     - List charging infrastructure
❌ POST /v1/admin/merchants/{id}/pause   - Pause merchant
❌ POST /v1/admin/merchants/{id}/resume  - Resume merchant
```

### Components Using Mock Data

| Component | Mock Data | Real API Needed |
|-----------|-----------|-----------------|
| Dashboard.tsx | Alerts, Activity Feed | `/v1/admin/alerts`, `/v1/admin/activity` |
| ChargingLocations.tsx | All location data | `/v1/admin/charging-locations` |
| Exclusives.tsx | Stats, Table data | `/v1/admin/exclusives` |
| Logs.tsx | All log entries | `/v1/admin/logs` |
| Overrides.tsx | Recent overrides log | `/v1/admin/overrides/history` |

### Redundant Implementations

**Problem:** Two separate admin frontends exist:
- `/apps/admin/` - Feature-rich with mock data (7 pages)
- `/ui-admin/` - Simpler but API-connected (3 pages)

**Recommendation:** Consolidate into single admin app, using:
- UI/UX from `/apps/admin/`
- API integration patterns from `/ui-admin/`

---

## Merchant Portal Gaps

### Missing Backend Functionality

```
❌ Billing page              - Shows mock data, no Stripe charges
❌ Settings page             - Business info is hardcoded, no save
❌ Primary Experience        - Toggle exists but no backend
❌ Notification preferences  - UI only, not persisted
❌ Exclusive time windows    - Start/end times not implemented
❌ Real-time cap monitoring  - No live cap usage display
❌ Customer-facing redemption - Staff instructions not shown
```

### Onboarding Flow Gaps

| Step | Status | Gap |
|------|--------|-----|
| Google OAuth | Partial | Error handling incomplete |
| Location Selection | Partial | Multi-location support unclear |
| Stripe Setup | Partial | SetupIntent created but not attached |
| Placement Rules | Partial | UI exists but rarely used |

### Integration Gaps

| Integration | Status | Gap |
|-------------|--------|-----|
| Google Business Profile | Partial | OAuth works, location fetch incomplete |
| Stripe | Partial | SetupIntent exists, no actual charges |
| Square | Not Started | Fields exist in model, no implementation |
| PostHog | Implemented | Working analytics |

---

## Data Model Gaps

### Missing Fields/Tables

```sql
-- Merchant exclusive time windows (not implemented)
ALTER TABLE merchant_exclusives ADD COLUMN start_time TIME;
ALTER TABLE merchant_exclusives ADD COLUMN end_time TIME;
ALTER TABLE merchant_exclusives ADD COLUMN days_of_week VARCHAR(20);

-- Admin audit log (partial - needs query endpoint)
-- Table exists but no API to retrieve logs

-- Override history (not implemented)
CREATE TABLE admin_overrides (
    id SERIAL PRIMARY KEY,
    operator_id INT REFERENCES users(id),
    action_type VARCHAR(50),  -- force_close, emergency_pause, reset_caps
    target_type VARCHAR(50),  -- location, merchant, system
    target_id VARCHAR(100),
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Security Gaps

### Admin Portal

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| No dedicated admin login endpoint | Medium | Create `/v1/auth/admin/login` with MFA |
| Token stored in localStorage | Low | Consider httpOnly cookies |
| No session timeout | Medium | Add token expiration handling |
| Overrides lack confirmation | High | Add 2-person approval for critical actions |

### Merchant Portal

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| API key in query param option | Medium | Deprecate, require header auth only |
| No rate limiting on some endpoints | Low | Add consistent rate limits |
| OAuth state validation partial | Medium | Complete CSRF protection |

---

## Deployment Gaps

### Admin Portal
- **Not deployed** - No production URL configured
- Needs: CloudFront distribution, S3 bucket, API URL configuration

### Merchant Portal
- **Not deployed** - No production URL configured
- Needs: CloudFront distribution, S3 bucket, Google OAuth redirect URLs

---

## Recommended Prioritization

### Phase 1: Critical (Week 1-2)
1. Create admin login endpoint
2. Implement exclusive toggle API
3. Connect admin dashboard to real alerts
4. Deploy admin portal to production

### Phase 2: Important (Week 3-4)
1. Implement merchant billing with Stripe
2. Create audit log retrieval API
3. Implement admin overrides endpoints
4. Add merchant settings persistence

### Phase 3: Enhancement (Week 5+)
1. Consolidate admin frontends
2. Implement Square integration
3. Add exclusive time windows
4. Real-time cap monitoring
5. Two-person approval for critical admin actions

---

## Technical Debt

1. **Two admin implementations** - Should consolidate
2. **Inconsistent API patterns** - Some use `/v1/admin/`, some use `/v1/merchants/`
3. **Mock data mixed with real** - Hard to know what's working
4. **Missing TypeScript types** - API responses not fully typed
5. **No E2E tests** - Admin/merchant flows untested

---

## Appendix: API Endpoint Inventory

### Implemented Admin APIs
- `GET /v1/admin/health`
- `GET /v1/admin/overview`
- `GET /v1/admin/users?query=`
- `GET /v1/admin/users/{id}/wallet`
- `POST /v1/admin/users/{id}/wallet/adjust`
- `GET /v1/admin/merchants`
- `GET /v1/admin/merchants/{id}/status`
- `POST /v1/admin/nova/grant`
- `POST /v1/admin/payments/{id}/reconcile`
- `GET /v1/admin/locations/{id}/google-place/candidates`
- `POST /v1/admin/locations/{id}/google-place/resolve`
- `GET /v1/admin/sessions/active`

### Implemented Merchant APIs
- `GET /v1/merchant/summary`
- `GET /v1/merchant/offers`
- `GET /v1/merchants/{id}/balance`
- `POST /v1/merchants/{id}/credit`
- `POST /v1/merchants/{id}/debit`
- `GET /v1/merchants/{id}/report`
- `POST /v1/merchants/register`
- `GET /v1/merchants/me`
- `POST /v1/merchants/redeem_from_driver`
- `GET /v1/merchants/transactions`
- `GET /v1/merchants/{id}/exclusives`
- `POST /v1/merchants/{id}/exclusives`
- `PUT /v1/merchants/{id}/exclusives/{eid}`
- `POST /v1/merchants/{id}/exclusives/{eid}/enable`
- `GET /v1/merchants/{id}/analytics`
- `PUT /v1/merchants/{id}/brand-image`
