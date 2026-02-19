CURSOR PROMPT — Fix Backend Gaps (iOS Production) with Missing Details Filled

You are Claude Code. Review the plan below, identify gaps, then execute a corrected Cursor‑ready implementation plan. Keep scope tight and avoid refactors.

Plan Gaps to Address (must include in your output):
1) **Auth + permissions**: vote endpoint must require auth and verify user identity; ensure user_id is from token, not request body.
2) **Validation + error codes**: define 400 for invalid amenity/vote_type, 404 for missing merchant, 409 for conflicting state if any.
3) **Idempotency & toggle behavior**: specify exact toggle semantics and ensure race‑safe upsert logic.
4) **DB indexes + constraints**: include unique constraint and index names; ensure FK references correct merchant key type.
5) **Aggregation performance**: avoid N+1; use single grouped query; ensure counts for both amenities even if zero.
6) **Schema & response consistency**: align MerchantInfo.amenities with frontend expectations; include empty amenities object or explicit null per contract.
7) **Tests**: add backend tests for vote create/update/toggle and aggregation.
8) **Frontend fallback**: if API unavailable, keep localStorage fallback behind feature flag; ensure optimistic UI updates.
9) **Migrations**: include downgrade; verify alembic revision chain.
10) **API docs**: update OpenAPI schema if used in project.

Primary Goals (P0):
- Amenity votes backend API + aggregation in merchant details
- MerchantInfo.amenities field in response
- Frontend uses API instead of localStorage (with fallback)

P1 (if time):
- Filter support in intent capture
- Favorites sync improvements

Your output MUST include:
A) Gap list (brief) with how you’ll fix each
B) Step‑by‑step implementation plan with exact files + snippets
C) QA checklist (API + app behavior)
D) Guardrails (no refactors, no new deps)

Repo paths to use:
Backend:
- backend/alembic/versions/055_add_amenity_votes_table.py
- backend/app/models/while_you_charge.py
- backend/app/schemas/merchants.py
- backend/app/routers/merchants.py
- backend/app/services/merchant_details.py
- backend/app/routers/intent.py (P1)
- backend/app/services/intent_service.py (P1)

Frontend:
- apps/driver/src/services/api.ts
- apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx
- apps/driver/src/contexts/FavoritesContext.tsx (P1)

Keep it concise, executable, and aligned with current project conventions.
