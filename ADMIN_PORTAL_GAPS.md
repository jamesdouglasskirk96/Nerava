# Admin Portal Gap Analysis

**Date:** 2026-03-24
**Goal:** Make the admin portal the single operational tool for Nico to manage chargers, merchants, exclusives, campaigns/incentives, and monitor the platform — eliminating the need for a separate DB tool.

---

## Current State Summary

The admin portal (`apps/admin`) has 9 screens: Dashboard, Merchants, Charging Locations (stub), Active Sessions, Exclusives, Overrides, Deployments, Logs, and Seed Manager. It provides read-heavy views with some merchant lifecycle actions (pause/ban/verify) and system controls (force-close, emergency pause). Three orphaned pages (Users, Locations, Demo) exist but aren't wired into navigation.

---

## Gap 1: Charger Management (CRITICAL)

**Current:** Chargers are seed-only. The Seed Manager can bulk-import from NREL, and there's a stub "Charging Locations" page that says "Coming soon." No way to view, search, edit, or remove individual chargers.

**What Nico needs:**

| Capability | Status | Priority |
|------------|--------|----------|
| View all chargers (table with search, filters by network/state/city) | MISSING | P0 |
| View charger detail (location, network, connectors, power, pricing, linked merchants) | MISSING | P0 |
| Add a single charger manually (name, lat/lng, network, connectors) | MISSING | P0 |
| Edit charger details (name, network, connectors, power, pricing, status) | MISSING | P0 |
| Remove/deactivate a charger | MISSING | P0 |
| View charger-merchant links (which merchants are walkable from this charger) | MISSING | P1 |
| Add/remove charger-merchant links manually | MISSING | P1 |
| Map view of chargers (Leaflet, click to inspect) | MISSING | P2 |
| Bulk edit chargers (select multiple, update network/status) | MISSING | P3 |

**Backend gaps:**
- No `POST /v1/admin/chargers` (create single charger)
- No `PUT /v1/admin/chargers/{id}` (update charger)
- No `DELETE /v1/admin/chargers/{id}` (remove charger)
- No `GET /v1/admin/chargers` with pagination/search/filters
- No `GET /v1/admin/chargers/{id}` (detail view with linked merchants)
- No CRUD for `charger_merchants` junction table
- `GET /v1/chargers/admin/stats` exists but is read-only aggregate stats, no auth

---

## Gap 2: Merchant Management (PARTIAL)

**Current:** Can search, list, pause/resume/ban/verify merchants, send portal links. Cannot create, edit details, or delete merchants. Cannot manage the WYC merchant ↔ DomainMerchant linkage.

**What Nico needs:**

| Capability | Status | Priority |
|------------|--------|----------|
| Search and list merchants | EXISTS | - |
| View merchant detail (full profile: address, place ID, photos, perk, contact) | PARTIAL (status only) | P0 |
| Create a new merchant manually (name, address, place ID, category) | MISSING | P0 |
| Edit merchant details (name, address, perk label, category, photos) | MISSING | P0 |
| Delete/archive a merchant | MISSING | P1 |
| Pause/resume/ban/verify merchant | EXISTS | - |
| View merchant's exclusive offers | PARTIAL (separate page) | P1 |
| View merchant's visit history (ExclusiveSession records) | MISSING | P1 |
| View merchant's campaign balance / funding status | MISSING | P1 |
| Link DomainMerchant to WYC Merchant records manually | MISSING | P2 |
| Send portal invite link | EXISTS | - |

**Backend gaps:**
- No `POST /v1/admin/merchants` (create merchant)
- No `PUT /v1/admin/merchants/{id}` (edit merchant details)
- No `DELETE /v1/admin/merchants/{id}` (remove merchant)
- `GET /v1/admin/merchants/{id}/status` exists but returns minimal data (status, square connection, nova balance) — needs full profile
- No endpoint to view a merchant's exclusive sessions / visit history
- No endpoint to view or manage merchant campaign balance

---

## Gap 3: Exclusive Offer Management (PARTIAL)

**Current:** Can list all exclusives, toggle active/paused, and ban. Cannot create or edit exclusives. Cannot set offer details (title, description, reward amount, daily cap).

**What Nico needs:**

| Capability | Status | Priority |
|------------|--------|----------|
| List all exclusives with filtering | EXISTS | - |
| Toggle exclusive active/paused | EXISTS | - |
| Ban exclusive | EXISTS | - |
| Create a new exclusive for a merchant (title, description, reward, cap) | MISSING | P0 |
| Edit exclusive details (title, description, reward amount, daily cap) | MISSING | P0 |
| Delete an exclusive | MISSING | P1 |
| Set exclusive on a specific charger-merchant link | MISSING | P0 |
| View activation history per exclusive | MISSING | P1 |
| Duplicate an exclusive to another charger/merchant | MISSING | P3 |

**Backend gaps:**
- No `POST /v1/admin/exclusives` (create exclusive — must create ChargerMerchant links with `exclusive_title`)
- No `PUT /v1/admin/exclusives/{id}` (edit exclusive details)
- No `DELETE /v1/admin/exclusives/{id}` (remove exclusive)
- No endpoint to view activation history per exclusive
- The current `GET /v1/admin/exclusives` lists exclusives but the data model is indirect (reads from ChargerMerchant links, not a standalone table)

---

## Gap 4: Campaign / Incentive Management (CRITICAL)

**Current:** Campaigns appear only as a count in the dashboard overview. No way to view, create, edit, or manage campaigns from the admin portal. The console app (`apps/console`) has campaign management, but Nico needs this directly in admin.

**What Nico needs:**

| Capability | Status | Priority |
|------------|--------|----------|
| List all campaigns (active, paused, completed, draft) | MISSING | P0 |
| View campaign detail (targeting rules, budget, grants, performance) | MISSING | P0 |
| Create a campaign (sponsor/merchant, budget, targeting rules, reward amount) | MISSING | P0 |
| Edit campaign (rules, budget top-up, reward amount, status) | MISSING | P0 |
| Pause/resume/end a campaign | MISSING | P0 |
| View campaign grants (which sessions matched, amounts) | MISSING | P0 |
| View campaign budget burn rate / remaining budget | MISSING | P1 |
| Add promo codes for merchant trial campaigns | MISSING | P1 |
| Duplicate a campaign | MISSING | P3 |

**Backend gaps:**
- Campaign CRUD endpoints exist in `app/routers/campaigns.py` but are scoped to authenticated sponsor users, not admin
- No `GET /v1/admin/campaigns` (list all campaigns across all sponsors)
- No `POST /v1/admin/campaigns` (create campaign as admin)
- No `PUT /v1/admin/campaigns/{id}` (admin edit)
- No `GET /v1/admin/campaigns/{id}/grants` (view matched grants)
- No admin campaign performance/stats endpoint

---

## Gap 5: Monitoring & Analytics (CRITICAL)

**Current:** Dashboard shows 8 static KPI numbers and a revenue breakdown. No time-series charts, no trend data, no alerting. Recharts is imported but not used.

**What Nico needs:**

| Capability | Status | Priority |
|------------|--------|----------|
| Session volume over time (daily/weekly/monthly chart) | MISSING | P0 |
| Revenue trend chart (campaign funding, fees, payouts over time) | MISSING | P0 |
| Active driver count over time | MISSING | P0 |
| Campaign performance dashboard (grants/day, budget burn, conversion) | MISSING | P0 |
| Charger utilization (sessions per charger, top chargers) | MISSING | P1 |
| Merchant performance (visits, claims, top merchants) | MISSING | P1 |
| Geographic heat map (sessions by region) | MISSING | P2 |
| Tesla API usage / cost tracking | MISSING | P1 |
| Real-time active session count (live ticker) | MISSING | P1 |
| Error rate monitoring (5xx, failed payments, failed Tesla calls) | MISSING | P1 |
| Driver acquisition funnel (signups → Tesla connect → first session) | MISSING | P2 |
| Alerting (threshold-based notifications for anomalies) | MISSING | P2 |
| Payout monitoring (pending, processing, failed payouts) | MISSING | P1 |

**Backend gaps:**
- `GET /v1/admin/overview` returns point-in-time counts, not time-series data
- No `/v1/admin/analytics/sessions` (session counts over time periods)
- No `/v1/admin/analytics/revenue` (revenue breakdown over time)
- No `/v1/admin/analytics/campaigns` (campaign performance metrics)
- No `/v1/admin/analytics/chargers` (utilization stats)
- No `/v1/admin/analytics/merchants` (merchant performance)
- No `/v1/admin/analytics/drivers` (driver funnel metrics)
- No `/v1/admin/analytics/errors` (error rate aggregation)

---

## Gap 6: User/Driver Management (ORPHANED)

**Current:** A Users page exists (`pages/Users.tsx`) with search and wallet adjustment, but it's not wired into the sidebar navigation. Backend endpoints exist and work.

**What Nico needs:**

| Capability | Status | Priority |
|------------|--------|----------|
| Search users by name/email/phone | EXISTS (orphaned) | P0 — just wire it up |
| View user detail (sessions, wallet, Tesla connection, reputation) | PARTIAL (wallet only) | P1 |
| Adjust user wallet balance | EXISTS (orphaned) | P0 — just wire it up |
| Grant Nova points manually | BACKEND EXISTS, no UI | P1 |
| View user's charging session history | MISSING | P1 |
| View user's Tesla connection status | MISSING | P2 |
| Ban/suspend a user | MISSING | P2 |

**Backend gaps:**
- User search and wallet endpoints exist
- Nova grant endpoint exists (`POST /v1/admin/nova/grant`)
- No endpoint for user detail view (sessions, Tesla status, reputation combined)
- No endpoint to ban/suspend users

---

## Gap 7: Partner Management (BACKEND ONLY)

**Current:** Full partner CRUD exists in the backend (`/v1/admin/partners/*`) but there is NO admin portal UI for it.

**What Nico needs:**

| Capability | Status | Priority |
|------------|--------|----------|
| List partners | BACKEND EXISTS, no UI | P2 |
| Create partner | BACKEND EXISTS, no UI | P2 |
| Edit partner | BACKEND EXISTS, no UI | P2 |
| Manage API keys | BACKEND EXISTS, no UI | P2 |
| View partner session volume | MISSING | P2 |

---

## Priority Summary

### P0 — Must have (Nico can't operate without these)

1. **Charger CRUD** — View/add/edit/remove chargers (backend + frontend)
2. **Merchant detail & edit** — View full profile, edit details (backend + frontend)
3. **Create exclusives** — Set up exclusive offers for merchants at chargers (backend + frontend)
4. **Campaign management** — View/create/edit/pause campaigns and see grants (backend + frontend)
5. **Time-series monitoring** — Session volume, revenue, active drivers over time (backend + frontend)
6. **Wire up Users page** — Already built, just add to sidebar nav

### P1 — Should have (operational visibility)

7. **Edit exclusives** — Modify existing offer details
8. **Charger-merchant link management** — Control which merchants appear near which chargers
9. **Merchant visit history** — See ExclusiveSession records per merchant
10. **Campaign performance** — Budget burn, grant rates, conversion metrics
11. **Charger/merchant utilization stats** — Top performers, usage patterns
12. **Error rate monitoring** — Track API failures, payment failures
13. **Payout monitoring** — Pending/failed payout visibility
14. **Tesla API cost tracking** — Monitor API call volume and estimated cost

### P2 — Nice to have

15. **Map views** — Charger and session geographic visualization
16. **Driver detail view** — Combined profile with sessions, wallet, Tesla, reputation
17. **Partner management UI** — Frontend for existing backend endpoints
18. **Driver acquisition funnel** — Signup → connect → first session metrics
19. **Alerting** — Threshold-based anomaly notifications

### P3 — Future

20. **Bulk operations** — Multi-select charger/merchant/campaign edits
21. **Campaign duplication** — Clone campaigns with modified parameters
22. **Exclusive duplication** — Copy offers across charger-merchant links

---

## Estimated Scope by Phase

### Phase 1: Core CRUD (P0 items 1-6)

**Backend work:**
- New admin charger router with full CRUD + charger-merchant link management
- Expand admin merchant endpoints (create, edit, delete, full detail)
- New admin exclusive creation endpoint (creates ChargerMerchant links with offer data)
- New admin campaign router (list all, create, edit, pause, view grants)
- New admin analytics endpoints (time-series session/revenue/driver counts)
- Wire Users page into sidebar (frontend only, ~5 min)

**Frontend work:**
- Build Charger management page (table, detail panel, add/edit forms)
- Expand Merchant page (detail view, edit form, create form)
- Add "Create Exclusive" flow to Exclusives page
- Build Campaign management page (table, detail, create/edit forms)
- Build Monitoring dashboard with Recharts (line charts for sessions, revenue, drivers)

### Phase 2: Operational Visibility (P1 items 7-14)

**Backend work:**
- Exclusive edit endpoint
- Charger-merchant link CRUD
- Merchant visit history endpoint
- Campaign performance/analytics endpoints
- Charger utilization stats endpoint
- Error aggregation endpoint
- Payout monitoring endpoint
- Tesla API usage tracking

**Frontend work:**
- Exclusive edit form
- Charger-merchant link management UI
- Campaign performance dashboard
- Enhanced monitoring with additional chart types
- Payout status view

---

## Architecture Notes

- All new admin endpoints should use `require_admin` dependency for auth
- All state-changing actions should log to `AdminAuditLog` via `log_admin_action()`
- All destructive actions should require a `reason` field and confirmation dialog
- Time-series data should support configurable periods (7d, 30d, 90d) with daily granularity
- Recharts is already installed — use `LineChart`, `BarChart`, `AreaChart` components
- Consider adding a dedicated `admin_chargers.py` router to keep code organized
- Campaign admin endpoints should be separate from sponsor-facing campaign endpoints
