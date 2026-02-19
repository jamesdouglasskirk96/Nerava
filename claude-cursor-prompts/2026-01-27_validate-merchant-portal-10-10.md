CLAUDE PROMPT — Validate Merchant Portal 10/10 Fixes + Regrade

You are Claude Code. Validate the latest merchant portal fixes and regrade readiness. Confirm each of the 5 steps below is correctly implemented with file/line evidence, then provide an updated score and ship verdict.

Steps to validate:
1) merchant_id fallback fixed
   - Files: apps/merchant/app/components/Overview.tsx, Exclusives.tsx, CreateExclusive.tsx
   - Expect: no more 'current_merchant' fallback; guard when missing

2) New backend endpoint
   - File: backend/app/routers/exclusive.py
   - Endpoint: GET /v1/exclusive/session/{session_id}
   - Expect: validates UUID, returns exclusive_session + merchant_name + exclusive_title + staff_instructions

3) CustomerExclusiveView wired to new endpoint
   - File: apps/merchant/app/components/CustomerExclusiveView.tsx
   - Expect: calls /v1/exclusive/session/{session_id} and renders real data

4) Overview Primary Experience CTA removed
   - File: apps/merchant/app/components/Overview.tsx
   - Expect: no-op button removed; replaced with Coming Soon badge

5) Exclusives status uses analytics
   - File: apps/merchant/app/components/Exclusives.tsx
   - Expect: getStatusColor/getStatusText use activations vs daily_cap; no TODO stubs

Your output MUST include:
- Pass/Fail per step with evidence (file + line)
- Updated UX score (0–10)
- Ship verdict
- Any remaining gaps or backend dependencies

Keep it concise and rigorous.
