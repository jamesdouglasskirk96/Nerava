# Gap Analysis Plan: Current Mobile Web → Target 3-Tab Next.js App

## Objective
Analyze gaps between current `ui-mobile/` implementation and target 3-tab UX (Wallet/Discovery/Profile) with magic-link auth.

## Scope
- **Current State**: `ui-mobile/` vanilla JS app (5 tabs + FAB)
- **Target State**: Next.js mobile web app with 3-tab structure + magic-link auth
- **No code changes** in this phase - analysis only

## Analysis Structure

### 1. Repository Reconnaissance
**Tasks:**
- Map all current routes/pages in `ui-mobile/`
- Document navigation structure (5 tabs + FAB)
- Identify all page modules in `js/pages/`
- List current authentication flows
- Document backend auth endpoints

**Deliverables:**
- Table: Current Routes & Pages
- Table: Current Navigation Structure
- List of page modules and their purposes

### 2. Target 3-Tab Model Documentation
**Source:** User-provided spec (from Nerava_App_Layout.pdf concept)

**TAB 1 — WALLET:**
- Charging state hero (Off-peak/Peak/Idle)
- Nova balance + quick actions
- Condensed activity feed
- Energy reputation progress
- QR/Scan entry point

**TAB 2 — DISCOVERY:**
- Search + filters
- Map module with merchant pins
- Perk feed + merchant cards
- Merchant details page
- Charge guidance capsule

**TAB 3 — PROFILE:**
- Avatar, name, email
- Badge tier + reputation
- Account options
- Legal links
- Sign out (magic-link session clear)

**Auth Requirement:**
- Email-only magic link (no password fields anywhere)

### 3. Gap Analysis by Tab

#### 3.1 WALLET Tab Analysis
**Current State:**
- Existing: `page-wallet`, `wallet.js`, `wallet-new.js`
- Features: Balance display, activity list, progress bars, streaks

**Gaps to Identify:**
- Missing charging state hero
- Activity feed structure differences
- Energy reputation vs current implementation
- QR/Scan entry point location/flow

#### 3.2 DISCOVERY Tab Analysis  
**Current State:**
- Existing: `page-explore` (full-screen map), `explore.js`
- Features: Map, merchant pins, recommendations, search bar

**Gaps to Identify:**
- Search/filter implementation completeness
- Map module alignment
- Perk feed standardization
- Merchant detail modal/page differences
- Missing charge guidance capsule

**Redundancies:**
- `page-earn` vs Discovery integration
- `page-claim` vs Discovery flow
- Multiple merchant views (showCode, merchantDashboard)

#### 3.3 PROFILE Tab Analysis
**Current State:**
- Existing: `page-profile`, `me.js`
- Features: Profile info, vehicle, notifications, account settings

**Gaps to Identify:**
- Badge tier display
- Reputation visualization
- Account options consolidation
- Legal links placement

### 4. Auth Gap Analysis

#### 4.1 Current Auth Flows
- Email/password registration (`apiRegister`)
- Email/password login (`apiLogin`)
- SSO (Apple/Google) buttons
- Backend: `/auth/register`, `/auth/login` with password_hash

#### 4.2 Magic-Link Requirements
- Email-only input (no password fields)
- Backend endpoint changes (new magic-link endpoint)
- Session management differences
- UI removal of all password inputs

#### 4.3 Code Locations to Document
- Frontend: `ui-mobile/js/app.js` (renderSSO)
- Frontend: `ui-mobile/js/core/api.js` (apiRegister, apiLogin)
- Backend: `nerava-backend-v9/app/routers/auth.py`
- Backend: User model password_hash field

### 5. Behavior Loop Reality Check

**Target Loops:**
1. Wallet → Discovery → Merchant → QR → Wallet
2. Instant reward visibility
3. Reputation updates visible
4. Clear feedback after off-peak charging

**Analysis:**
- What works today
- What breaks the loop
- Missing transitions
- January pilot blockers

### 6. Redundant/Obsolete Screens

**Pages to Consolidate:**
- `page-activity` → Should merge into Wallet or Discovery?
- `page-earn` → Should merge into Discovery flow?
- `page-claim` → Should merge into Discovery flow?
- `page-charge` → Purpose unclear?
- `page-show-code` → Merchant detail modal instead?
- `page-merchant-dashboard` → Separate merchant app?

### 7. Technical Architecture Gaps

**Current:**
- Vanilla JS with hash routing
- Static HTML pages
- Module-based JS files
- FastAPI backend serving static files

**Target:**
- Next.js App Router
- TypeScript
- Server/client component architecture
- API routes for backend integration

### 8. Deliverable Document Structure

**File:** `NEXT_MOBILE_GAP_ANALYSIS.md`

**Sections:**
1. **Overview** - Executive summary
2. **Current State Inventory** - Routes, pages, navigation
3. **Target State Definition** - 3-tab model specification
4. **Gap Analysis by Tab** - Wallet/Discovery/Profile detailed gaps
5. **Auth Gap Analysis** - Password → Magic-link migration requirements
6. **Behavior Loop Reality Check** - What works/breaks
7. **Redundant Screens** - Consolidation opportunities
8. **Technical Architecture Gaps** - Vanilla JS → Next.js considerations
9. **Recommended Next Steps** - High-level implementation roadmap

## Execution Steps

1. ✅ Complete repository reconnaissance
2. ✅ Map current routes and pages
3. ✅ Document target 3-tab model
4. ✅ Perform detailed gap analysis per tab
5. ✅ Document auth migration requirements
6. ✅ Analyze behavior loops
7. ✅ Identify redundant screens
8. ✅ Document technical architecture gaps
9. ✅ Compile into final markdown document

## Timeline Estimate
- Reconnaissance: 10 min
- Gap Analysis: 20 min
- Document Compilation: 10 min
- **Total: ~40 minutes**

---

**Status:** Ready for approval to proceed

