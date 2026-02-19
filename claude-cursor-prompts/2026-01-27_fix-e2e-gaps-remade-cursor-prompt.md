CURSOR PROMPT — Close iOS↔Backend E2E Gaps (Remade with Missing Items)

You are Claude Code. The report below identifies P0/P1 gaps between the iOS app and backend. Your job is to validate and implement the missing fixes with code‑level detail. Keep scope tight and avoid refactors.

Gaps to include (must not miss):
P0 — Build / Crash
1) Missing import: useVoteAmenity in MerchantDetailsScreen
2) Zod schema: perk nullable/optional
3) Zod schema: moment.label nullable
4) Null access: merchantData.perk.* must be guarded

P1 — Schema / Security / Reliability
5) Exclusive session Zod: merchant_id/charger_id nullable
6) Auth hardening: /v1/exclusive/complete must require auth (no demo fallback in prod)
7) Auth hardening: /v1/exclusive/visits/* endpoints require auth
8) Token refresh alias: add /v1/auth/refresh route or update frontend
9) Native events idempotency: replace in‑memory cache with Redis

Data contract mismatches to review (fix if needed):
- merchant.place_id accessed in MerchantDetailsScreen but missing in MerchantInfo schema
- activate_response.status returned by backend but not in Zod
- otp_verify.user returned by backend but not in Zod; auth.ts uses it

Your output MUST include:
A) Quick gap validation (what you confirmed and where)
B) Cursor‑ready implementation steps (exact files + snippets)
C) QA checklist (build + API)
D) Guardrails (no refactors, no new deps)

Key files:
Frontend:
- apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx
- apps/driver/src/services/schemas.ts
- apps/driver/src/services/api.ts

Backend:
- backend/app/routers/exclusive.py
- backend/app/routers/auth_domain.py
- backend/app/routers/native_events.py
- backend/app/core/config.py (for Redis access)
- backend/app/schemas/merchants.py

Keep it concise and executable.
