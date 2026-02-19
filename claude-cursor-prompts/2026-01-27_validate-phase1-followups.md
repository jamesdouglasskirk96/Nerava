CLAUDE PROMPT: REGRADE AFTER PHASE 1 FOLLOW-UP FIXES

You are Claude. Regrade the Phase 1 follow-up fixes and confirm whether the three validation bugs are fully resolved. Use code inspection and cite file+line evidence.

Context
- Cursor applied fixes for:
  1) Exclusive activation idempotency key persistence + collision handling
  2) Redis rate limiter double-counting
  3) Migration 057 idempotency conflicts with migration 033
  4) ExclusiveSession model uniqueness

Your task
1) Verify each fix in code and report PASS/FAIL with evidence (file path + line). 
2) Regrade Phase 1 stability score (0–10) and say whether the system is now safe to proceed to Phase 2.
3) If any issues remain, list exact fixes required and provide a Cursor-ready patch list.

Files to check
- backend/app/routers/exclusive.py
  - activate_exclusive should set idempotency_key on new session
  - unique constraint collisions should return idempotent response (or 409 if driver mismatch)
- backend/app/services/auth/rate_limit.py
  - _check_limit_redis should be read-only (no zadd)
  - record_* should be the only Redis writers
- backend/alembic/versions/057_make_nova_transactions_idempotency_unique.py
  - should be idempotent and handle existing index from 033
- backend/app/models/exclusive_session.py
  - idempotency_key should be unique=True

Format
- Start with a short verdict line (e.g., “Regrade: PASS, Phase 1 is now stable”)
- Then list each fix with PASS/FAIL and evidence
- End with updated readiness score and next steps

No speculation. Only verify in code.
