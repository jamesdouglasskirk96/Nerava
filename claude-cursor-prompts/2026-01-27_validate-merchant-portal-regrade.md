CLAUDE PROMPT — Validate Merchant Portal Fixes + Regrade Readiness

You are Claude Code. Validate the merchant portal fixes listed below against the repo and regrade production readiness. Confirm each requirement is actually satisfied, note any regressions, and provide an updated score + ship verdict.

Changes to validate:
1) Overview.tsx: removed hardcoded mock data; uses getMerchantExclusives + analytics
2) Session management: logout button, JWT expiry check, 401 interceptor, token check
3) DemoNav gated behind VITE_DEMO_MODE
4) Non‑functional pages now honest “Coming Soon” or no‑data states
5) Exclusives alert() replaced with inline error banner
6) CustomerExclusiveView wired to API (GET /v1/exclusive/{session_id}) with loading/error
7) Exclusives progress bar uses real analytics / daily cap
8) CreateExclusive removed unsupported fields; payload aligns with backend

Files modified:
- apps/merchant/app/components/Overview.tsx
- apps/merchant/app/components/DashboardLayout.tsx
- apps/merchant/app/services/api.ts
- apps/merchant/app/App.tsx
- apps/merchant/app/components/Exclusives.tsx
- apps/merchant/app/components/CreateExclusive.tsx
- apps/merchant/app/components/CustomerExclusiveView.tsx
- apps/merchant/app/components/Settings.tsx
- apps/merchant/app/components/Billing.tsx
- apps/merchant/app/components/PrimaryExperience.tsx
- apps/merchant/app/components/SelectLocation.tsx

Your output MUST include:
1) Pass/Fail per requirement with evidence (file + line)
2) Updated UX score (0–10) and ship verdict
3) Any remaining blockers or missing backend endpoints
4) Next steps (if any)

Keep it concise and rigorous.
