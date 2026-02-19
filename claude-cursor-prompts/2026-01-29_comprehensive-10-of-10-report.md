# COMPREHENSIVE REPORT: Path to 10/10

**Date:** 2026-01-29
**Author:** Claude Opus 4.5 (validation, analysis, architecture)
**Baseline:** 9.83/10 composite (system) + 8.7/10 (UX demo)
**Target:** 10.0/10

---

## EXECUTIVE SUMMARY

Nerava is at **9.83/10 system composite** and **8.7/10 UX** after 5 patch rounds and 8 implementation tasks. Zero P0 or P1 blockers remain. The app is ship-ready.

To reach 10/10 requires closing **13 remaining gaps** across 4 categories:
- **UX Copy & Interaction** (5 items) — the largest gap
- **Frontend Polish** (3 items) — loading states and transitions
- **Backend Completeness** (3 items) — wiring RBAC, ORM for remaining endpoints
- **Infrastructure & Assets** (2 items) — OG images, deep-link native code

None of these are ship-blockers. All are achievable in one sprint.

---

## CURRENT STATE

### System Composite: 9.83 / 10

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| App Logic & Features | 10.0 | 30% | 3.00 |
| Infrastructure & Ops | 9.5 | 20% | 1.90 |
| Compliance & Privacy | 9.8 | 20% | 1.96 |
| Performance & Scale | 9.8 | 15% | 1.47 |
| UX & Polish | 10.0 | 15% | 1.50 |
| **Composite** | | 100% | **9.83** |

### UX Demo Grade: 8.7 / 10

| Dimension | Score |
|-----------|-------|
| Clarity & hierarchy | 9.0 |
| Flow & navigation | 9.0 |
| Affordances & interaction | 8.0 |
| Feedback & states | 8.0 |
| Content & copy | 8.5 |
| Visual polish | 9.0 |
| Completion & delight | 9.0 |

### Score Progression

| Phase | System | UX | Notes |
|-------|--------|-----|-------|
| Pre-upgrade baseline | 6.5 | — | Initial audit |
| Post Phase 1-3 (24 steps) | 8.3 | — | Compliance + resilience |
| Post P0/P1 fixes (6 items) | 8.5 | — | Bug fixes |
| Post P1/P2 polish (9 items) | 9.1 | — | Timer, pagination, a11y |
| Post Cursor 8-task sprint | 9.83 | 8.7 | Skeletons, ORM, RBAC, SEO, a11y |
| **Target** | **10.0** | **10.0** | **This report** |

---

## ALL 13 REMAINING GAPS

### Category A: UX Copy & Interaction (5 items)

---

#### A1. "Done Charging" Button Label is Wrong

**Severity:** High (users will be confused)
**Observed:** Demo frame 8 — Active Session screen
**Current:** Third CTA reads "Done Charging"
**Problem:** The user hasn't finished charging — they secured a dining reservation. "Done Charging" conflates two activities (EV charging and merchant visit).

**Fix:**
- File: `apps/driver/src/components/ExclusiveActiveView/ExclusiveActiveView.tsx`
- Replace static "Done Charging" with context-aware label based on intent type
- If intent = "Eat" → "I've Arrived — Done"
- If intent = "Work" → "Done Working"
- If intent = "Quick Stop" → "Visit Complete"
- Fallback → "I'm at the Merchant - Done"

**Effort:** 15 min
**Impact:** +0.3 UX

---

#### A2. Amenity Filter Chips Have No Selected State

**Severity:** Medium (interaction affordance gap)
**Observed:** Demo frames 2, 3, 9, 13 — Discovery screens
**Current:** Bathroom, Food, WiFi, Pets, Music, Patio appear as identical gray icons. No visual feedback on tap.
**Problem:** Users can't tell if chips are interactive or decorative. If tapped, no visual state change confirms selection.

**Fix:**
- Files: `apps/driver/src/components/DriverHome/DriverHome.tsx`, `PreChargingScreen.tsx`
- On tap: chip background → brand blue (#1877F2), icon → white, text → white
- On second tap: deselect (return to gray)
- Update header count: "2 chargers with open stalls" → "1 charger with WiFi" when filtered
- Add `aria-pressed` attribute for accessibility

**Effort:** 2-3 hours
**Impact:** +0.3 UX

---

#### A3. Account Screen is Sparse — No Visit History or Profile

**Severity:** Medium (retention/engagement gap)
**Observed:** Demo frame 14 — Account screen
**Current:** 4 items only: Favorites (1 saved), Share Nerava, Settings, Log out
**Problem:** No user identity (name, photo), no visit history, no earned perks, no reputation display. The reputation system exists in the backend but isn't surfaced.

**Fix:**
- File: `apps/driver/src/components/Account/AccountScreen.tsx`
- Add at top: User profile section (name, phone last 4 digits, member since date)
- Add "Visit History" row with count (e.g., "3 visits") → taps to chronological list
- Add "Reputation" row showing tier badge (Bronze/Silver/Gold) + score
- Pull data from existing `/v1/activity/reputation` endpoint

**Effort:** 4-6 hours
**Impact:** +0.3 UX

---

#### A4. Completion Feedback is Binary Only

**Severity:** Low (signal quality gap)
**Observed:** Demo frame 11 — Reservation Completed modal
**Current:** Thumbs up / thumbs down + "Share your charge moment" + Done
**Problem:** Binary feedback gives minimal signal. No way to capture why a visit was good or bad.

**Fix:**
- File: `apps/driver/src/components/ExclusiveCompleted/` (or CompletionFeedbackModal)
- After thumbs down: show a single-select chips row — "Wrong hours", "Too crowded", "Offer not honored", "Other"
- After thumbs up: show optional "What did you love?" text input (max 140 chars)
- Store feedback in existing `verified_visits` table or new `visit_feedback` table
- Keep it optional — "Done" button always visible, feedback is opt-in

**Effort:** 3-4 hours
**Impact:** +0.2 UX

---

#### A5. "2 here now" Social Proof Inconsistent Placement

**Severity:** Low (visual consistency)
**Observed:** Demo frames 1 vs 2
**Current:** On Merchant Detail (frame 1), "2 here now" is below "128 drivers visited" as inline text. On Carousel Card (frame 2), it's a green badge overlaid on the hero image top-left.
**Problem:** Same data, different visual treatment between views. Users lose the pattern.

**Fix:**
- Files: `MerchantDetailsScreen.tsx`, `FeaturedMerchantCard.tsx`, `MerchantCarousel.tsx`
- Standardize: always use the green badge with dot + count + "here now" as an overlay on the hero image
- Remove inline "2 here now" text from detail screen body; use badge consistently
- Badge position: top-left on all cards and hero images

**Effort:** 1 hour
**Impact:** +0.1 UX

---

### Category B: Frontend Polish (3 items)

---

#### B1. No Screen Transitions

**Severity:** Medium (perceived quality)
**Observed:** All frame transitions in demo — hard cuts between screens
**Current:** Screens appear/disappear instantly with no animation
**Problem:** Without transitions, the app feels like a slideshow. Users lose spatial context (where did I come from? where am I going?).

**Fix:**
- File: `apps/driver/src/App.tsx` (router level)
- Add CSS transitions:
  - Discovery → Merchant Detail: slide up from bottom (300ms ease-out)
  - Merchant Detail → Intent Modal: bottom sheet rise (250ms ease-out)
  - Active Session → Show Host: crossfade (200ms)
  - Any → Account: slide from right (250ms)
  - Back navigation: reverse of the forward transition
- Use `framer-motion` (already in React ecosystem) or pure CSS transitions
- Respect `prefers-reduced-motion` (already implemented — transitions become instant)

**Effort:** 4-6 hours
**Impact:** +0.3 UX

---

#### B2. Skeleton Loaders Not Demonstrated in Real Network Conditions

**Severity:** Low (verified as implemented, needs production validation)
**Observed:** No loading states visible in demo
**Current:** Skeleton components exist (`Skeleton.tsx` — 5 variants). Integrated into `DriverHome`, `PreChargingScreen`, `WhileYouChargeScreen`.
**Problem:** Demo data loads instantly (localhost/mock). Skeletons aren't exercised.

**Fix:**
- No code change needed if skeletons are already wired to `isLoading` state
- Verify by adding `await new Promise(r => setTimeout(r, 1500))` to API calls temporarily
- If skeletons don't appear, check that `isLoading` state is correctly toggled before/after fetch

**Effort:** 30 min (verification only)
**Impact:** +0.1 UX (confirmed working)

---

#### B3. OTP Input Needs Per-Digit aria-labels

**Severity:** Low (accessibility polish)
**Observed:** Not in demo, identified in code audit
**Current:** OTP digit inputs exist but lack per-field `aria-label`
**Files:** `apps/driver/src/components/VerificationCode/`

**Fix:**
```tsx
<input
  aria-label={`Digit ${index + 1} of 6`}
  inputMode="numeric"
  // ... existing props
/>
```

**Effort:** 15 min
**Impact:** +0.1 a11y

---

### Category C: Backend Completeness (3 items)

---

#### C1. RBAC Not Wired to Admin Endpoints

**Severity:** Medium (infrastructure gap)
**Current state:** `AdminRole` enum, `ROLE_PERMISSIONS`, `has_permission()`, and `require_permission()` dependency all exist. Migration 061 added `admin_role` column. But no admin endpoint actually uses `require_permission()`.

**Fix:**
- File: `backend/app/routers/admin_domain.py`
- Replace `get_current_admin_user` with `require_permission("merchants", "read")` on read endpoints
- Add `require_permission("merchants", "write")` on mutation endpoints
- Add `require_permission("kill_switch", "write")` on kill switch endpoint
- Seed initial super_admin: update existing admin user's `admin_role` to `"super_admin"`

```python
# Example: protect merchant delete
@router.delete("/admin/merchants/{id}")
async def delete_merchant(
    id: str,
    admin: User = Depends(require_permission("merchants", "delete")),
    db: Session = Depends(get_db)
):
```

**Effort:** 2-3 hours
**Impact:** +0.2 infrastructure

---

#### C2. Raw SQL Remains in Some Intent Endpoints

**Severity:** Low (maintainability)
**Current state:** `GET /v1/intent` and `GET /v1/activity/reputation` were migrated to ORM. But `POST /v1/intent`, `POST /v1/intents`, `GET /v1/intents/me`, `PATCH /v1/intents/{id}/start`, and `POST /v1/intents/{id}/verify-geo` still use raw SQL.

**Fix:**
- File: `backend/app/routers/intents.py`
- Replace all remaining `text()` queries with `db.query(ChargeIntent)` ORM equivalents
- The `ChargeIntent` model already exists — just use it for INSERT, UPDATE, and filtered SELECTs
- Keep `km_distance()` utility function as-is (pure Python math, not DB)

**Effort:** 2-3 hours
**Impact:** +0.1 maintainability

---

#### C3. Stale Comment in activity.py

**Severity:** Trivial (cosmetic)
**Current:** `activity.py:50` contains comment "fallback to demo data" but the code correctly returns `status: 'new'` for users without reputation rows.

**Fix:**
- File: `backend/app/routers/activity.py`
- Remove or update the comment to say "new user defaults"

**Effort:** 1 min
**Impact:** +0.0 (code hygiene only)

---

### Category D: Infrastructure & Assets (2 items)

---

#### D1. OG/Twitter Card Images Don't Exist

**Severity:** Medium (social sharing broken)
**Current state:** `layout.tsx` references `og-image.png` (1200x630) and `twitter-card.png` (1200x600) at `https://nerava.network/`. These files don't exist yet.
**Problem:** Social share previews will show a broken image or no image.

**Fix:**
- Design/create two images:
  - `apps/landing/public/og-image.png` — 1200x630, Nerava logo + tagline + app screenshot
  - `apps/landing/public/twitter-card.png` — 1200x600, similar but optimized for Twitter
- Deploy to S3/CloudFront so `https://nerava.network/og-image.png` resolves
- Verify with: `curl -I https://nerava.network/og-image.png`
- Test with: https://cards-dev.twitter.com/validator and https://developers.facebook.com/tools/debug/

**Effort:** 1-2 hours (design) + 15 min (deploy)
**Impact:** +0.2 compliance/SEO

---

#### D2. iOS Deep-Link Routing — Documentation Exists, Code Doesn't

**Severity:** Low (not needed until push notifications ship)
**Current state:** `docs/ios-deep-link-routing.md` has URL scheme, Universal Links setup, route mapping, and Swift implementation code. But the actual iOS shell app hasn't been updated.

**Fix:**
- Requires Xcode: add URL scheme to `Info.plist`, add `application(_:open:options:)` handler to `AppDelegate.swift`
- Add Associated Domains entitlement: `applinks:app.nerava.network`
- Create `apple-app-site-association` file at `https://app.nerava.network/.well-known/apple-app-site-association`
- Test with: `xcrun simctl openurl booted "nerava://merchant/abc123"`

**Effort:** 2-3 hours (native iOS)
**Impact:** +0.1 infrastructure

---

## IMPLEMENTATION PRIORITY

### Sprint 1: High-Impact UX Fixes (1 day)

| # | Task | Effort | UX Impact |
|---|------|--------|-----------|
| A1 | Fix "Done Charging" → context-aware label | 15 min | +0.3 |
| A2 | Amenity filter selected state | 2-3 hrs | +0.3 |
| B1 | Screen transitions | 4-6 hrs | +0.3 |
| A5 | Standardize "here now" badge | 1 hr | +0.1 |

**Expected UX after Sprint 1:** 8.7 → **9.7**

### Sprint 2: Account & Feedback (1 day)

| # | Task | Effort | UX Impact |
|---|------|--------|-----------|
| A3 | Account screen: profile + visit history | 4-6 hrs | +0.3 |
| A4 | Completion feedback: negative reason chips | 3-4 hrs | +0.2 |
| C1 | Wire RBAC to admin endpoints | 2-3 hrs | +0.2 sys |

**Expected UX after Sprint 2:** 9.7 → **10.0**
**Expected System after Sprint 2:** 9.83 → **9.95**

### Sprint 3: Polish & Assets (half day)

| # | Task | Effort | Impact |
|---|------|--------|--------|
| C2 | ORM migration for remaining intents endpoints | 2-3 hrs | +0.1 sys |
| D1 | Create and deploy OG/Twitter images | 1-2 hrs | +0.2 sys |
| B2 | Verify skeleton loaders under real latency | 30 min | +0.1 UX |
| B3 | OTP per-digit aria-labels | 15 min | +0.1 a11y |
| C3 | Remove stale comment in activity.py | 1 min | +0.0 |
| D2 | iOS deep-link native code | 2-3 hrs | +0.1 sys |

**Expected System after Sprint 3:** 9.95 → **10.0**

---

## CURSOR PROMPT FOR SPRINT 1

```
You are Cursor. Implement 4 high-impact UX fixes for the Nerava driver app.

TASK A1: Fix "Done Charging" button label
- File: apps/driver/src/components/ExclusiveActiveView/ExclusiveActiveView.tsx
- The third CTA currently says "I'm at the Merchant - Done"
- Make it context-aware based on the refuelDetails prop:
  - If refuelDetails.type === 'eat' → "I've Arrived"
  - If refuelDetails.type === 'work' → "Done Working"
  - If refuelDetails.type === 'quick_stop' → "Visit Complete"
  - Fallback → "I'm at the Merchant"
- Keep the same click handler (capture event + onArrived)

TASK A2: Amenity filter chips interactive with selected state
- Files: apps/driver/src/components/DriverHome/DriverHome.tsx
- The amenity chips (Bathroom, Food, WiFi, Pets, Music, Patio) need:
  - A selectedFilters state: useState<string[]>([])
  - On tap: toggle filter in/out of array
  - Selected style: bg-[#1877F2] text-white (brand blue)
  - Unselected style: bg-white text-[#65676B] border border-[#E4E6EB]
  - Add aria-pressed={isSelected} to each chip button
  - Update header text when filters active: "X chargers matching Y"
  - Pass filters to the data query/filter logic

TASK B1: Screen transitions with framer-motion (or CSS)
- File: apps/driver/src/App.tsx
- Add slide-up transition for merchant detail modal
- Add bottom-sheet rise for intent capture modal
- Add crossfade for show-host fullscreen
- Wrap with @media (prefers-reduced-motion: reduce) to disable

TASK A5: Standardize "here now" badge
- Files: MerchantDetailsScreen.tsx, FeaturedMerchantCard.tsx, MerchantCarousel.tsx
- Use green badge overlay on hero image consistently
- Pattern: green dot + "X here now" text, top-left of image
- Remove inline text version from detail screen body

Keep changes surgical. Use existing patterns. No new dependencies except framer-motion for B1 if needed.
```

---

## CURSOR PROMPT FOR SPRINT 2

```
You are Cursor. Implement 3 items for Sprint 2: Account enhancements and RBAC wiring.

TASK A3: Enhance Account screen
- File: apps/driver/src/components/Account/AccountScreen.tsx
- Add at top: User profile section
  - Fetch user data from existing auth context or /v1/me endpoint
  - Show: user name (or "Driver"), phone last 4 digits, "Member since Jan 2026"
  - Use a circular avatar placeholder (initials or icon)
- Add "Visit History" row after Favorites
  - Show count from API: GET /v1/activity/reputation → use data to derive visit count
  - Chevron → navigates to visit history list (create simple VisiHistory component)
- Add "Reputation" row showing tier badge
  - Fetch from existing GET /v1/activity/reputation
  - Show: "Bronze" / "Silver" / "Gold" badge with score

TASK A4: Enhanced completion feedback
- File: apps/driver/src/components/ExclusiveCompleted/ (or CompletionFeedbackModal)
- After thumbs down is clicked:
  - Show chips: "Wrong hours", "Too crowded", "Offer not honored", "Other"
  - Single-select, optional
  - On "Done", send feedback to POST /v1/exclusive/{id}/feedback
- After thumbs up is clicked:
  - Show optional text input: "What did you love?" (max 140 chars)
  - On "Done", send feedback to same endpoint
- Keep "Done" always visible; feedback is opt-in

TASK C1: Wire RBAC to admin endpoints
- File: backend/app/routers/admin_domain.py
- File: backend/app/dependencies_domain.py (require_permission already exists)
- Replace get_current_admin_user with require_permission on these endpoints:
  - GET /admin/merchants → require_permission("merchants", "read")
  - PUT /admin/merchants/{id} → require_permission("merchants", "write")
  - DELETE /admin/merchants/{id} → require_permission("merchants", "delete")
  - POST /admin/kill-switch → require_permission("kill_switch", "write")
  - GET /admin/overview → require_permission("analytics", "read")
- For backward compatibility: if user.admin_role is NULL, treat as super_admin
  (existing admins keep working until roles are assigned)

Keep changes surgical. Use existing patterns.
```

---

## CODEX TESTING PROMPT

```
You are Codex. Write comprehensive test cases for the Nerava system.

Focus areas:
1. RBAC permission checks (admin_role.py + admin_domain.py)
   - Test each role (super_admin, zone_manager, support, analyst)
   - Verify allowed actions succeed and denied actions return 403
   - Test NULL admin_role backward compatibility

2. ORM ChargeIntent model (charge_intent.py + intents.py)
   - Test CRUD operations via ORM
   - Test dedupe logic (same user, same merchant, within 10 minutes)
   - Test datetime serialization (.isoformat())

3. Frontend analytics events
   - Test merchant_clicked event fires with correct properties
   - Test otp_sent backend event captures phone hash (not raw phone)
   - Test debug endpoint returns events in non-prod

4. Skeleton loader rendering
   - Test ChargerCardSkeleton renders with aria-hidden
   - Test MerchantCardSkeleton renders correct structure
   - Test skeleton shows when isLoading=true, hides when false

5. Timer accessibility
   - Test aria-live="polite" present on countdown
   - Test aria-label updates with minutes
   - Test role="timer" attribute

6. Consent system
   - Test consent grant stores ip_address and privacy_policy_version
   - Test consent revoke creates new record (not updates)
   - Test consent banner respects localStorage

7. Active session flow
   - Test intent capture → session creation → timer → completion loop
   - Test expiration modal appears at 0 minutes
   - Test "Find a New Spot" navigates to discovery

Run with: pytest backend/tests/ -q && cd apps/driver && npx vitest run
```

---

## FINAL EXPECTED SCORES

### After All 13 Items

| Dimension | Current | Target | Gap |
|-----------|---------|--------|-----|
| App Logic & Features | 10.0 | 10.0 | 0.0 |
| Infrastructure & Ops | 9.5 | 10.0 | +0.5 (RBAC wiring, deep-links) |
| Compliance & Privacy | 9.8 | 10.0 | +0.2 (OG images, OTP aria-labels) |
| Performance & Scale | 9.8 | 10.0 | +0.2 (skeleton verification, ORM) |
| UX & Polish | 10.0 | 10.0 | 0.0 |
| **System Composite** | **9.83** | **10.0** | **+0.17** |

| UX Dimension | Current | Target | Gap |
|-----------|---------|--------|-----|
| Clarity & hierarchy | 9.0 | 10.0 | +1.0 (A3 account, A5 badge) |
| Flow & navigation | 9.0 | 10.0 | +1.0 (B1 transitions, A1 copy) |
| Affordances & interaction | 8.0 | 10.0 | +2.0 (A2 filter chips) |
| Feedback & states | 8.0 | 10.0 | +2.0 (A4 feedback, B2 skeletons) |
| Content & copy | 8.5 | 10.0 | +1.5 (A1 context labels) |
| Visual polish | 9.0 | 10.0 | +1.0 (B1 transitions, A5 consistency) |
| Completion & delight | 9.0 | 10.0 | +1.0 (A3 history, A4 feedback) |
| **UX Average** | **8.7** | **10.0** | **+1.3** |

---

## SUCCESS CRITERIA

- [ ] All 13 items implemented and verified
- [ ] System composite: 10.0/10
- [ ] UX demo grade: 10.0/10
- [ ] TypeScript compiles without errors
- [ ] Python tests pass
- [ ] All migrations apply cleanly
- [ ] OG images return 200 from production URL
- [ ] RBAC blocks unauthorized admin actions
- [ ] Screen transitions respect prefers-reduced-motion
- [ ] Amenity chips toggle with visual feedback
- [ ] Account screen shows visit history and reputation
- [ ] Completion feedback captures qualitative signal

---

*Last updated: 2026-01-29*
*Next: Give Sprint 1 Cursor prompt to Cursor, then validate.*
