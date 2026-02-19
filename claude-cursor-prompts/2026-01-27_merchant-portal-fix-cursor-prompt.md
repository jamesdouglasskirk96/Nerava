CURSOR PROMPT — Merchant Portal 10/10 Fixes (Apps/Merchant Only)

You are Claude Code. The last attempt solved the wrong problem. This time, ONLY modify apps/merchant/* (and its API client) to satisfy the 8 merchant‑portal requirements below. Do NOT touch iOS or backend hardening unrelated to the merchant portal.

Requirements (must all be addressed):
1) Remove hardcoded mock data in Overview
   - File: apps/merchant/app/components/Overview.tsx
   - Remove “Free Pastry with Coffee” and hardcoded progress stats
   - Replace with real data or honest “No active exclusive”/“Coming Soon” states

2) Add session management (token expiry + logout)
   - Files: apps/merchant/app/components/DashboardLayout.tsx, apps/merchant/app/services/api.ts
   - Add Logout button (clears access_token, businessClaimed, merchant_id; route to /claim)
   - Add 401 interceptor: on 401, clear session and redirect to /claim
   - Add JWT exp check on load; if expired, clear session

3) Gate DemoNav behind env flag
   - File: apps/merchant/app/App.tsx
   - Render <DemoNav /> only if VITE_DEMO_MODE === 'true'

4) Fix non‑functional pages (honest UX)
   - Files: apps/merchant/app/components/Settings.tsx, Billing.tsx, PrimaryExperience.tsx, SelectLocation.tsx
   - Remove hardcoded fake data or mark sections “Coming Soon”
   - Hide demo-only buttons from production

5) Replace alert() with inline error UI
   - File: apps/merchant/app/components/Exclusives.tsx
   - Replace alert() with inline banner or toast component

6) Wire CustomerExclusiveView to real API
   - File: apps/merchant/app/components/CustomerExclusiveView.tsx
   - Replace mockExclusiveData with API call: GET /v1/exclusive/{session_id}
   - Add loading + error states

7) Fix Exclusives progress bar
   - File: apps/merchant/app/components/Exclusives.tsx
   - Remove progress bar if no data OR hook to real daily activations

8) Send all fields in CreateExclusive
   - File: apps/merchant/app/components/CreateExclusive.tsx
   - Include type, start_time, end_time, staff_instructions in request payload
   - OR remove those inputs if not supported by backend

Output MUST include:
A) Step‑by‑step implementation with exact file edits/snippets
B) QA checklist
C) Guardrails: no refactors, no new deps, apps/merchant only

Focus and execute. Do not drift to other parts of the repo.
