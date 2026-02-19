CLAUDE PROMPT — Full System 10/10 Plan (All Components)

You are Claude Code. Using the system status report below (and your own reasoning), produce a Cursor‑ready implementation plan to get all six components to 10/10 production readiness. Include your analysis first (concise), then a prioritized implementation plan with exact file paths and code‑level steps.

Components:
1) iOS App (WKWebView wrapper)
2) Driver Web App (standalone + embedded)
3) Merchant Portal
4) Admin Portal
5) Backend API
6) Landing Page

Your output MUST include:
A) Your own readiness analysis per component (score + top blockers)
B) Cross‑component risks (shared backend gaps, auth flows, data contracts)
C) Prioritized plan (P0/P1/P2) with exact files + steps
D) QA checklist by component
E) Guardrails (no refactors, no new deps unless unavoidable)

Key facts from the current report (use as context but validate if needed):
- iOS App: 8/10; push notification entitlement still development; no deep links; App Store metadata missing
- Driver Web App: 8.8/10; timer expiration recovery UI missing; some empty states incomplete; OTP resend failure not handled
- Merchant Portal: 8/10; 5 screens still mock/placeholder; claim flow is real; auth handled client‑side; staff view now uses /v1/exclusive/session/{session_id}
- Admin Portal: 5.5/10; no auth gate/login UI; duplicate functions in api.ts (build error); 7 missing backend endpoints; dashboard is mock data
- Backend: 9/10; 8 admin endpoints missing; some legacy router duplication; feature flags default false
- Landing Page: 9/10; CTA links use http not https; no structured data or sitemap; no phone auto‑redirect (OK)

Explicit gaps to address (minimum for 10/10):
- Admin portal: add login/auth gate, fix api.ts duplicates, wire dashboard to /v1/admin/overview, replace alert()/prompt(), implement missing endpoints
- Backend: implement admin endpoints used by admin portal
- Landing page: switch CTA links to https, add sitemap + JSON‑LD if feasible
- iOS app: set aps‑environment to production for release; deep links if in scope
- Driver web app: add timer expiration recovery UI and OTP resend failure state
- Merchant portal: convert remaining mock screens to honest “Coming Soon” or real data; consider edit‑exclusive UI and merchant_id handling

Constraints:
- Keep changes additive; avoid refactors
- Provide code‑level detail sufficient for Cursor implementation
- If backend endpoints are missing, list exact router files to edit

Deliverable: A single, tight plan that Cursor can execute to reach 10/10 across the system.
