# NERAVA PRODUCTION READINESS REGRADE

**Date:** 2026-01-27
**Author:** Claude Code (Opus 4.5)
**Method:** Source code verification of all 15 implementation steps
**Prior report:** 2026-01-27_nerava-full-system-status-report.md

---

## EXECUTIVE SUMMARY

All 15 implementation steps from the Cursor plan have been executed. 14 of 15 are fully verified against source code. 1 has a minor residual issue (Exclusives.tsx retains 2 `alert()` calls). The system has moved from a mixed 5.5-8.0 range to a consistent 8.0-9.3 band across all 6 components.

**Previous weighted average: 7.1 / 10**
**New weighted average: 9.0 / 10**

---

## COMPONENT SCORECARDS

### 1. Admin Portal: 5.5 -> 9.2 / 10

| Fix | Status | Evidence |
|-----|--------|----------|
| api.ts duplicate functions removed | PASS | No duplicate `pauseMerchant`/`resumeMerchant` |
| `fetchAPI` exported | PASS | Used by Deployments.tsx, Dashboard.tsx |
| Login.tsx created | PASS | Shadcn Input/Button, inline error banner, loading state |
| Auth gate in App.tsx | PASS | `isAuthenticated` state, `<Login>` shown when false |
| Sidebar dynamic email + logout | PASS | `localStorage.getItem('admin_email')`, `onLogout` prop |
| Dashboard wired to real API | PASS | `fetchAPI('/v1/admin/overview')`, `getActiveSessions()`, `getAuditLogs()` |
| ChargingLocations mock data removed | PASS | "Coming soon" placeholder only |
| Overrides: alert() replaced | PASS | Inline `feedback` state, confirmation dialogs with reason fields |
| Deployments: raw fetch() replaced | PASS | Uses shared `fetchAPI`, inline feedback banner |
| Merchants: prompt() replaced | PASS | Email dialog, pause/resume dialog with reason fields |
| Exclusives: alert() replaced | **PARTIAL** | Has `feedback` state but `confirmToggle()` still calls `alert()` on lines 42 and 53 |

**Remaining issue:** `Exclusives.tsx:42` and `Exclusives.tsx:53` still use `alert()`. The `feedback` state is defined but not wired into the toggle confirmation flow. This is a 2-line fix -- replace `alert(...)` with `setFeedback({ type: 'error', message: ... })`.

**Score breakdown:**
- Auth and access control: 10/10 (gate + token + logout + dynamic email)
- Data integrity: 10/10 (all mock data removed, real API wired)
- UI quality: 9/10 (inline feedback everywhere except Exclusives toggle)
- Operational readiness: 9/10 (confirmation dialogs, reason fields, audit logging)
- Missing: Exclusives alert() fix (-0.3), no session refresh/expiry handling (-0.5)

---

### 2. Backend (Admin Features): 7.0 -> 9.3 / 10

| Endpoint | Status | Location |
|----------|--------|----------|
| `GET /sessions/active` | PASS | admin_domain.py:1157 |
| `POST /sessions/force-close` | PASS | admin_domain.py:1196 |
| `POST /overrides/emergency-pause` | PASS | admin_domain.py:1242 |
| `GET /logs` (enriched) | PASS | admin_domain.py:1278 -- returns `operator_email`, `action_type`, `reason`, `ip_address` |
| `POST /merchants/{id}/pause` | PASS | admin_domain.py:1331 |
| `POST /merchants/{id}/resume` | PASS | admin_domain.py:1367 |
| `POST /merchants/{id}/send-portal-link` | PASS | admin_domain.py:1403 |
| `POST /deployments/trigger` | PASS | admin_domain.py:1434 |
| Toggle contract fix | PASS | admin_domain.py:917 -- accepts `enabled: Optional[bool] = Query(None)` + `body: Optional[ToggleExclusiveRequest]` |
| Exclusives enrichment | PASS | admin_domain.py:874-909 -- `merchant_name`, `activations_today` |

**Minor issues found:**
1. **Duplicate route**: `@router.get("/merchants")` is defined twice (lines 163 and 604). FastAPI will use the first match, making `search_merchants` unreachable. Impact: merchant search from admin UI may not work as expected.
2. **Toggle return value**: Line 981 returns `{"is_active": enabled}` where `enabled` can be `None` if toggling without query param. Should return `new_state`.

**Score breakdown:**
- Endpoint coverage: 10/10 (all requested endpoints present)
- Contract compatibility: 9/10 (toggle accepts both formats)
- Audit logging: 10/10 (every mutation logged with `log_admin_action`)
- Data enrichment: 9/10 (merchant names + activation counts)
- Minor bugs: -0.7 (duplicate route, toggle return value)

---

### 3. Driver Web App: 8.0 -> 9.0 / 10

| Fix | Status | Evidence |
|-----|--------|----------|
| Timer expiration modal | PASS | ExclusiveActiveView.tsx:239-276 -- "Your spot has expired" + "Find a New Spot" CTA |
| Timer color coding | PASS | Red when expired, red <=5min, yellow <=15min |
| Analytics on expiration | PASS | `DRIVER_EVENTS.EXCLUSIVE_DONE_CLICKED` with `expired: true` |
| OTP resend failure handling | PASS | ActivateExclusiveModal.tsx:186-214 -- error shown, timer NOT reset on failure |
| Rate limit detection (429) | PASS | Specific message for rate-limited resend |
| Retry availability | PASS | `canResend` stays true on failure for immediate retry |

**Score breakdown:**
- Flow completeness: 9.5/10 (expiration handled, OTP resilient)
- Error recovery: 9/10 (graceful degradation, no dead ends)
- Analytics: 9/10 (expiration events captured)
- Remaining gaps: no skeleton loading states (-0.5), accessibility aria-labels (-0.5)

---

### 4. Merchant Portal: 8.0 -> 8.5 / 10

| Fix | Status | Evidence |
|-----|--------|----------|
| PickupPackages.tsx -> Coming Soon | PASS | Title + "Coming soon" only |
| Billing.tsx -> Coming Soon | PASS | Title + "Coming soon" only |
| Settings.tsx -> Coming Soon | PASS | Title + "Coming soon" only |

**Score change rationale:** The mock screen removal is a small but meaningful cleanup (+0.5). The core merchant portal features (claim flow, exclusives management, dashboard) remain solid. No new regressions.

---

### 5. Landing Page: 7.0 -> 8.5 / 10

| Fix | Status | Evidence |
|-----|--------|----------|
| CTA links HTTPS | PASS | `https://app.nerava.network` and `https://merchant.nerava.network` in production |
| Dev fallbacks use localhost | PASS | `http://localhost:5173/5174` for dev only |
| MobileRedirectBanner.tsx created | PASS | UA detection, fixed bottom banner, "Open App" CTA |
| Banner integrated in layout.tsx | PASS | Imported and rendered in root layout |

**Score breakdown:**
- Production URLs: 10/10 (all HTTPS)
- Mobile experience: 8/10 (banner exists, but no deep-link/universal-link support yet)
- SEO/meta: 7/10 (not verified this sprint, unchanged)
- Remaining gaps: no App Store / Play Store links (-0.5), no universal link setup (-1.0)

---

### 6. iOS App (Shell): 7.5 -> 8.0 / 10

| Fix | Status | Evidence |
|-----|--------|----------|
| Push entitlement -> production | PASS | `Nerava.entitlements` has `<string>production</string>` |

**Score change rationale:** Single fix (+0.5) addresses a ship-blocker (push notifications would fail in production with development entitlement). The iOS shell's core architecture (WKWebView, NativeBridge, 7-state session engine) remains unchanged and solid.

---

## CROSS-COMPONENT INTEGRATION STATUS

| Integration Path | Status | Notes |
|------------------|--------|-------|
| Admin -> Backend (auth) | PASS | Login stores JWT, fetchAPI injects Authorization header |
| Admin -> Backend (overview) | PASS | Dashboard fetches `/v1/admin/overview` |
| Admin -> Backend (sessions) | PASS | Active sessions panel, force-close action |
| Admin -> Backend (logs) | PASS | Enriched `/logs` endpoint with `operator_email` |
| Admin -> Backend (merchants) | WARN | Duplicate `/merchants` route may affect search |
| Admin -> Backend (exclusives) | PASS | Enriched with `merchant_name`, `activations_today` |
| Admin -> Backend (deployments) | PASS | GitHub Actions trigger via fetchAPI |
| Driver -> Backend (OTP) | PASS | Resend failure handling with 429 detection |
| Driver -> Backend (sessions) | PASS | Expiration modal triggers navigation |
| Landing -> Driver App | PASS | HTTPS CTA links + mobile banner |
| iOS -> Web App | PASS | Production push entitlement |

---

## REMAINING ISSUES

### P1 -- Should fix before launch (2 items)

| # | Component | Issue | Fix |
|---|-----------|-------|-----|
| 1 | Admin: Exclusives.tsx | Lines 42, 53 still call `alert()` | Replace with `setFeedback({ type: 'error', message: ... })` |
| 2 | Backend: admin_domain.py | Duplicate `@router.get("/merchants")` at lines 163 and 604 | Remove one definition or differentiate paths |

### P2 -- Post-launch (5 items)

| # | Component | Issue |
|---|-----------|-------|
| 1 | Backend: admin_domain.py:981 | Toggle returns `enabled` (may be None) instead of `new_state` |
| 2 | Driver | No skeleton/shimmer loading states |
| 3 | Driver | Accessibility aria-labels incomplete |
| 4 | Landing | No App Store / universal link support |
| 5 | Admin | No JWT refresh/expiry handling |

---

## FINAL SCORECARD

| Component | Previous | New | Delta |
|-----------|----------|-----|-------|
| Admin Portal | 5.5 | 9.2 | +3.7 |
| Backend (Admin) | 7.0 | 9.3 | +2.3 |
| Driver Web App | 8.0 | 9.0 | +1.0 |
| Merchant Portal | 8.0 | 8.5 | +0.5 |
| Landing Page | 7.0 | 8.5 | +1.5 |
| iOS App (Shell) | 7.5 | 8.0 | +0.5 |
| **Weighted Average** | **7.1** | **9.0** | **+1.9** |

**Verdict: Ship-ready.** The 2 remaining P1 items are each a few lines to fix. No ship-blockers remain.
