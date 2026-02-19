CURSOR EXECUTION PROMPT: COMPLETE PUBLIC‑SCALE 10/10

You are Cursor. Finish the remaining items in the “Public Scale 10/10” plan. Some Phase 1 items were already implemented; you MUST verify current state and skip anything already done. Only implement missing items. Keep changes surgical and backward‑compatible. No new dependencies.

Scope
- Backend (FastAPI + SQLAlchemy)
- Driver web app (React)
- Admin portal
- Merchant portal
- Landing page
- iOS (if any code change needed)

Guardrails
- No broad refactors; targeted fixes only.
- No breaking API changes; additive/backward‑compatible only.
- ASCII only.
- Use existing patterns/utilities.
- If a migration number already exists, use the next available revision.

STEP 0 — VERIFY WHAT’S ALREADY DONE (SKIP IF TRUE)
Check and record:
- Exclusive activate/complete idempotency logic in `backend/app/routers/exclusive.py` and that idempotency_key is persisted in new sessions.
- `exclusive_sessions.idempotency_key` exists and is unique (migration 056).
- `nova_transactions.idempotency_key` unique index is applied and migration 057 is idempotent.
- Stripe webhook atomic transaction is fixed in `backend/app/services/stripe_service.py`.
- Charger search uses PostgreSQL bounding‑box query in `backend/app/services/intent_service.py`.
- `GOOGLE_PLACES_API_KEY` is read from env (not hardcoded).
- Redis OTP rate limiting is enabled + read‑only check logic (no double counting) in `backend/app/services/auth/rate_limit.py`.
If any are missing or incorrect, fix them first.

PHASE 2 (P1) — COMPLIANCE + RESILIENCE

1) Consent system (backend)
- Add model: `backend/app/models/user_consent.py`
- Register in `backend/app/models/__init__.py`
- Add router: `backend/app/routers/consent.py` with GET + grant/revoke endpoints.
- Register router in `backend/app/main.py`.
- Create migration (next available revision) to add `user_consents` table with unique (user_id, consent_type) index.

2) Gate PostHog identify on consent
- Driver: `apps/driver/src/analytics/index.ts` add `identifyIfConsented()` helper.
- Replace identify() in `apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx` with identifyIfConsented().
- Apply same consent gate to merchant + admin analytics (`apps/merchant/app/analytics/index.ts`, `apps/admin/src/analytics/index.ts`).
- Store consent in localStorage (e.g., `consent_analytics=granted`) or fetch `/v1/consent` and cache; keep minimal.

3) Account deletion with anonymization
- `backend/app/routers/account.py`: replace soft delete with anonymization + cascade deletes for refresh tokens, vehicle tokens, favorites, consents. Keep nova_transactions immutable; anonymize user references.
- Log deletion via audit service.

4) Account export endpoint
- `backend/app/routers/account.py`: return real export JSON (user, wallet, sessions, intents, transactions, consents). Replace placeholder.

5) Data retention job
- Add `backend/app/jobs/data_retention.py` to delete old `intent_sessions`, `otp_challenges`, `claim_sessions`, `vehicle_onboarding`, `merchant_cache`, and anonymize old exclusive session locations.
- No scheduler code required; document run command in file docstring.

6) Admin performance fixes
- `backend/app/routers/admin_domain.py`: replace N+1 merchant last-activity query with subquery join.
- Add Redis caching (60s TTL) around `/v1/admin/overview` using existing cache layer.

7) Fix duplicate `/merchants` route
- In `backend/app/routers/admin_domain.py`, rename the search endpoint to `/merchants/search` (keep list endpoint at `/merchants`).
- Update `apps/admin/src/services/api.ts` to call `/merchants/search`.

8) Remove alert() in admin exclusives
- `apps/admin/src/components/Exclusives.tsx`: replace alert() with inline feedback or toast (use existing patterns).

9) Google Places resilience
- `backend/app/integrations/google_places_client.py`: add circuit breaker + stale-while-revalidate using cached entries; avoid returning [] on transient failure when cached data exists.
- Add request coalescing if feasible without new deps (basic in‑process lock per geo cell is acceptable).

10) Replace bare excepts in critical paths
- `backend/app/routers/admin_domain.py` (the specified lines) and `backend/app/routers/exclusive.py`: replace bare except with logged exceptions and minimal context.

PHASE 3 (P2) — HARDENING

11) p95 latency instrumentation
- `backend/app/middleware/metrics.py`: add histogram metric for critical endpoints (OTP verify, exclusive activate/complete, intent capture, nearby merchants, verify visit).

12) Remove hardcoded demo values
- `backend/app/routers/intents.py`: replace demo-user IDs with authenticated user; return 401 if no auth.
- `backend/app/routers/bootstrap.py`: require BOOTSTRAP_KEY env var (no dev default in prod).
- `backend/app/routers/activity.py`: remove hardcoded demo users.

13) Stripe SDK calls off event loop
- `backend/app/services/stripe_service.py`: if any async endpoints are blocked by sync Stripe calls, wrap via `asyncio.to_thread` or isolate in sync-only route. Keep API contract unchanged.

14) System-wide kill switch
- `backend/app/routers/admin_domain.py`: add `/v1/admin/system/pause` endpoint that sets Redis flag.
- `backend/app/middleware/auth.py`: if Redis flag set, block non-admin endpoints with 503.

DATABASE MIGRATIONS
- Use next available revision numbers (do NOT reuse 056/057/058).
- Migration for `user_consents` table.
- If you need any additional indexes/constraints, include them in the same or subsequent migration.

VALIDATION
- Run: `cd backend && pytest tests/test_otp_auth.py tests/test_exclusive_sessions.py -q`
- Run migrations on a DB that already has migration 033 to confirm no conflicts.
- `apps/admin` build + typecheck: `npm run build` and `npx tsc --noEmit`.
- Validate `/v1/consent` endpoints, `/v1/admin/overview` cache, and `/v1/admin/merchants/search`.

OUTPUT
- Provide a concise summary of changes with file paths.
- List any manual infra steps still required (ECS tasks, Redis, RDS sizing, alarms).

