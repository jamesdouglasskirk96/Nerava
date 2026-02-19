# Nerava Engineering Reference — February 2026

> Upload this document to NotebookLM for a queryable reference on the Nerava codebase, production incidents, architecture, and readiness gaps.

---

## Section 1: Production Incident Report — OTP Verification Failure (Feb 2, 2026)

### Incident Summary

| Field | Value |
|-------|-------|
| Date | February 2, 2026 |
| Severity | P0 — Authentication completely broken |
| Duration | Unknown (reported as "since the charging party") |
| Impact | All driver OTP verification failed silently. Users received SMS codes but could not log in. |
| Resolution | Code fix deployed to 4 files. Root cause: three separate bugs combined to mask all failure types as "Invalid code." |

### Timeline

1. **User reports**: Received OTP code via SMS at Asadas Grill, entered it, got "not working" error.
2. **Investigation**: Production health check passed (`GET /v1/health` returned `{"status":"ok","db":"ok"}`). OTP send confirmed working (`POST /auth/otp/start` returned `{"otp_sent":true}`). Problem isolated to the verify path.
3. **Root cause identified**: Three independent bugs made every OTP failure — rate limits, timeouts, Twilio API errors, expired codes — appear as "Invalid code." to the user.

### Root Cause: Three Bugs Combined

**Bug 1 — Rate-limit 429 returned "Invalid code."**
- File: `backend/app/services/otp_service_v2.py` line 197
- When a user exceeded verify rate limits, the HTTP 429 response said `"Invalid code."` instead of a rate-limit message.
- Effect: Users who retried too quickly saw "Invalid code." and thought their code was wrong.

**Bug 2 — Server error 500 returned "Invalid code."**
- File: `backend/app/services/otp_service_v2.py` line 259 and `backend/app/routers/auth.py` line 561
- When the Twilio Verify API was unreachable (timeout, network error, misconfiguration), the 500 error said `"Invalid code."`.
- Effect: Infrastructure failures appeared as user input errors.

**Bug 3 — Twilio Verify provider silently swallowed all exceptions**
- File: `backend/app/services/auth/twilio_verify.py`, `verify_otp()` method
- The method caught ALL exceptions (timeouts, TwilioException, unknown errors) and returned `False`.
- No diagnostic logging — no service_sid prefix, no code length, no Twilio error codes.
- Effect: When Twilio returned error 20404 (service not found), 60200 (max attempts), or 60202 (expired), the system treated them all as "wrong code."

### Why These Bugs Compound

The three bugs form a failure cascade:
1. Twilio API has a transient issue (timeout, rate limit, or config error)
2. `twilio_verify.py` catches the exception and returns `False` (Bug 3)
3. `otp_service_v2.py` sees `False`, raises HTTPException 401 with `"Invalid code."` (Bug 2)
4. User retries, hits rate limit, gets HTTPException 429 with `"Invalid code."` (Bug 1)
5. User sees "Invalid code." for every attempt regardless of actual cause

### Fixes Applied

**Fix 1 — Differentiated error messages in otp_service_v2.py**
- Line 197: Changed 429 message from `"Invalid code."` to `"Too many attempts. Please wait a few minutes and try again."`
- Line 259: Changed 500 message from `"Invalid code."` to `"Verification service error. Please try again."`

**Fix 2 — Rewrote twilio_verify.py verify_otp() to propagate real errors**
- Added diagnostic logging: service_sid prefix, code length
- Timeouts now raise exceptions (not return False)
- Twilio error 20404 (bad service SID): raises with "misconfigured" message
- Twilio error 60200 (max check attempts): returns False (legitimate "wrong code")
- Twilio error 60202 (expired): returns False (legitimate "code expired")
- All other TwilioExceptions: raise with error string
- Unknown exceptions: raise instead of silent False

**Fix 3 — Fixed auth.py catch-all error handler**
- Line 561: Changed from `"Invalid code."` to `"Verification service error. Please request a new code."`
- Added `logger.error()` with exc_info for stack traces

**Fix 4 — Added OTP diagnostics admin endpoint**
- New `GET /v1/admin/otp/diagnostics` endpoint on admin_domain.py
- Checks: OTP provider config, Twilio credentials presence, Verify service SID validity, rate-limit backend type

### Architecture Context: OTP Flow

```
Driver App (auth.ts)
  → POST /v1/auth/otp/start { phone }
    → otp_service_v2.py send_otp()
      → rate_limit.py check → otp_factory.py get_provider()
        → twilio_verify.py send_otp() → Twilio Verify API
  ← { otp_sent: true }

Driver App (auth.ts)
  → POST /v1/auth/otp/verify { phone, code }
    → otp_service_v2.py verify_otp()
      → rate_limit.py check → otp_factory.py get_provider()
        → twilio_verify.py verify_otp() → Twilio Verify API
  ← { token, user }
```

Key detail: Production uses `app.main_simple:app` (not `app.main:app`) as the entry point. Confirmed in `backend/scripts/start.sh` line 41.

### Lessons Learned

1. **Never use the same error message for different failure modes.** The single string "Invalid code." made it impossible to diagnose whether the problem was user error, rate limiting, or infrastructure failure.
2. **External API wrappers must not swallow exceptions.** The Twilio Verify provider's `except: return False` pattern is the most dangerous anti-pattern in the codebase. A timeout looks identical to a wrong code.
3. **Add diagnostic logging at integration boundaries.** Without logging the Twilio service_sid prefix, error codes, or response status, there was zero observability into why verification failed.
4. **Frontend error mapping depends on backend specificity.** The driver app correctly maps 401→"Incorrect code", 429→"Too many requests", 500→"Verification unavailable" — but this only works if the backend returns the right status codes.

### Prevention: What Must Change

- All external API wrappers (Twilio, Stripe, Google Places) must distinguish between "the operation returned a negative result" (return False) and "the operation could not be completed" (raise Exception).
- Error messages in HTTP responses must indicate the category of failure (auth error, rate limit, server error) — never a generic string.
- The OTP diagnostics endpoint should be checked during deploy verification.

---

## Section 2: Codebase Readability Analysis

### Overall Scores

| Level | Score | Summary |
|-------|-------|---------|
| Project / System | 4.5 / 10 | Disorganized structure, dual configs, 226 untracked files |
| File | 3.5 / 10 | God-files, duplicated services, unclear test layout |
| Code | 7.5 / 10 | Good type safety and async patterns, poor error handling and duplication |

### Project / System Level (4.5/10)

**Structure Issues:**
- 115 router files, 141 service files — far more than a system this size needs
- Two config modules: `backend/app/config.py` (used by main_simple.py) and `backend/app/core/config.py` (used by OTP/auth services). Both read env vars independently. This caused the OTP incident — debugging which config module controls which behavior is non-obvious.
- 226 untracked files in git (scripts, docs, prompt files, data exports)
- 8 model stub files that should be deleted or consolidated
- Orphaned directories from prior refactors
- No consistent naming convention for routers (`auth.py` vs `auth_domain.py` vs `admin_domain.py`)

**What a new engineer would struggle with:**
- Which entry point is production? (`main.py` vs `main_simple.py` — answer: `main_simple.py`)
- Which config module matters? (both, depending on the import path)
- Which router handles a given endpoint? (115 files to search through)
- Which model file defines a given table? (models spread across `models/`, `models_all.py`, `models_domain.py`, `models_while_you_charge.py`, `models_vehicle.py`)

### File Level (3.5/10)

**God-files (single files doing too much):**
- `admin_domain.py`: 1,742 LOC — admin CRUD, wallet mutations, user search, Nova grants, OTP diagnostics
- `main_simple.py`: 1,317 LOC — production entry point with 85 print() statements, 100+ router registrations, CORS config, exception handlers, static file serving
- `DriverHome.tsx`: 1,121 LOC — driver app home screen with location, chargers, merchants, navigation
- `pilot.py`: 1,236 LOC — deprecated PWA endpoint still in use
- `drivers_domain.py`: 1,231 LOC — charging session management
- `exclusive.py`: 1,008 LOC — exclusive session state machine
- `wallet_pass.py`: 1,389 LOC — Apple Wallet pass generation

**Duplicated services (same capability, two files):**
- `otp_service.py` + `otp_service_v2.py` — OTP sending/verification
- `pool.py` + `pool2.py` — database connection pooling
- `events.py` + `events2.py` — analytics event definitions
- `config.py` + `core/config.py` — application configuration

**Test directory confusion:**
- `backend/tests/` — main test directory (100 files)
- `tests/` (project root) — separate test directory with different test files
- `e2e/` — end-to-end tests
- No documented convention for which tests go where

### Code Level (7.5/10)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Error handling | 7/10 | 29+ bare `except:` clauses that swallow errors silently |
| Type safety | 8/10 | Good Pydantic usage in backend; some `any` casts in frontend TypeScript |
| Logging | 7/10 | 85 print() statements in main_simple.py; good structured logging elsewhere |
| Code duplication | 6/10 | CORS config duplicated in main.py and main_simple.py; user creation logic in 4 places |
| Security | 8/10 | Good SQL injection prevention via SQLAlchemy ORM; Fernet encryption for OAuth tokens |
| Async patterns | 9/10 | Excellent asyncio.to_thread usage for blocking Twilio/Stripe calls |

**Specific code-level issues:**
- 29+ bare `except:` clauses across 15 files (admin_domain.py, stripe_api.py, purchases.py, fraud.py, etc.)
- 73+ TODO/FIXME comments indicating incomplete features
- 6 router-to-router imports creating tight coupling (e.g., `admin_domain.py` imports `_balance` from `drivers_wallet.py`)
- 215 direct `db.commit()` calls in router files (should be in service layer)
- 15+ hardcoded values (demo keys, localhost URLs, charger IDs)
- 10+ `console.log()` statements in production driver app code

---

## Section 3: Production Gap Analysis

### P0 — Critical (Must Fix Before Invoicing)

**P0-1: Merchant arrivals endpoints completely unauthenticated**
- File: `backend/app/routers/merchant_arrivals.py` lines 53-140
- The `POST /v1/arrivals/create`, `PUT /v1/arrivals/{id}/confirm`, and `GET /v1/arrivals/merchant/{id}` endpoints have no `Depends(get_current_user)` or any authentication.
- Risk: Anyone can create fake arrival sessions, confirm arrivals, and view merchant data.
- Fix: Add `current_user = Depends(get_current_user)` to all endpoints.

**P0-2: Rate limiting is in-memory, lost on container restart**
- File: `backend/app/services/auth/rate_limit.py`
- Rate limit state stored in Python dicts (`_phone_limits`, `_ip_limits`). When the App Runner container restarts, all rate limits reset to zero.
- Risk: An attacker can trigger a container restart (via OOM or crash) to bypass rate limits.
- Fix: Use Redis as the rate limit backend. Redis is already configured but optional (`REDIS_ENABLED=false` by default).

**P0-3: No token refresh endpoint**
- JWT access tokens expire in 60 minutes. There is no `/v1/auth/refresh` endpoint.
- Risk: Users must re-authenticate via OTP every 60 minutes. During a charging session or exclusive redemption, the token can expire mid-flow.
- Fix: Add a refresh token endpoint that issues new access tokens using a longer-lived refresh token.

**P0-4: Twilio SMS webhook not signature-validated**
- File: `backend/app/routers/twilio_sms_webhook.py` lines 28-152
- Incoming SMS webhooks from Twilio are not validated using Twilio's request signature (`X-Twilio-Signature` header).
- Risk: Anyone who knows the webhook URL can send forged SMS replies, triggering fake "DONE" confirmations for merchant arrivals.
- Fix: Use `twilio.request_validator.RequestValidator` to verify the signature before processing.

**P0-5: Stripe webhook replay not prevented**
- Stripe webhooks are verified for signature but there's no idempotency key check to prevent replay attacks.
- Risk: A replayed webhook could double-credit Nova tokens or duplicate payment records.
- Fix: Store processed webhook event IDs and reject duplicates.

**P0-6: Session creation race condition**
- No database-level UNIQUE constraint on (user_id, merchant_id, status='active') for exclusive sessions.
- Risk: Two concurrent requests can create duplicate active sessions for the same user/merchant.
- Fix: Add a partial unique index: `CREATE UNIQUE INDEX ON exclusive_sessions (user_id, merchant_id) WHERE status = 'active'`.

**P0-7: Billing not transactional with session state**
- Billing events are created in a separate db.commit() from session state transitions.
- Risk: If the billing insert succeeds but the session update fails (or vice versa), the system is in an inconsistent state. Merchant could be billed for an incomplete session, or session marked complete without billing.
- Fix: Wrap billing + session state change in a single database transaction.

**P0-8: Twilio SMS failures are silent with no retry**
- When SMS notification to a merchant fails (network timeout, Twilio error), the failure is logged but no retry occurs.
- Risk: Merchant never receives the arrival notification. Driver waits at charger. Session eventually expires with no completion.
- Fix: Add a retry queue (at minimum, 3 retries with exponential backoff).

**P0-9: Analytics blocks critical paths**
- PostHog `capture()` calls are inline in the OTP verification and session creation paths.
- Risk: If PostHog is slow or down, it could add latency to authentication and session creation.
- Fix: Ensure all analytics calls are fire-and-forget (PostHog's Python SDK already uses a background queue, but verify no `flush()` calls are in the hot path).

**P0-10: Dangerous config defaults**
- `OTP_PROVIDER` defaults to `"stub"` in `backend/app/core/config.py` line 134.
- The startup validation in `backend/app/core/startup_validation.py` blocks stub in production, but only if `ENV=prod` is set.
- Risk: If `ENV` is not set or set to anything other than "prod", the stub provider is used in production, bypassing real OTP verification.
- Fix: Default `OTP_PROVIDER` to `"twilio_verify"` instead of `"stub"`. Fail hard if Twilio credentials are missing.

**P0-11: Merchant notification config endpoint unauthenticated**
- The `PUT /v1/merchant/config` endpoint that sets the merchant's SMS notification phone number has no authentication.
- Risk: Anyone can change a merchant's notification phone number, redirecting arrival notifications.
- Fix: Require merchant authentication via magic link token or session.

### P1 — High (Fix Within 2 Weeks)

**P1-1: Billing amounts not validated**
- No server-side validation that billing amounts are positive, within expected ranges, or match the session type.

**P1-2: No session cleanup job**
- Expired sessions are never cleaned up. The `expires_at` field exists but no background task checks it.

**P1-3: No stuck session recovery**
- If a session gets stuck in `awaiting_arrival` or `merchant_notified` state, there's no automatic timeout or recovery.

**P1-4: No structured logging**
- `main_simple.py` uses 85 `print()` statements instead of structured logging. These don't appear in CloudWatch with proper log levels.

**P1-5: Sentry is optional in production**
- Sentry initialization is guarded by `if settings.SENTRY_DSN`. If the env var is missing, errors go untracked silently.

**P1-6: N+1 query in admin merchant list**
- `GET /v1/admin/merchants` executes N+1 database queries (1 to fetch merchants, then 1 per merchant to get last transaction).
- With 100 merchants: 101 queries, ~500ms latency.

**P1-7: Charger lookup loads all chargers into memory**
- `intent_service.py` loads every public charger from the database and computes Haversine distance in Python.
- With 50,000 chargers: ~650ms per request.

**P1-8: Stripe calls are synchronous and not wrapped in asyncio.to_thread**
- `stripe_service.py` makes blocking Stripe API calls without timeout or thread offloading.

**P1-9: In-memory OAuth state for merchant onboarding**
- `merchant_onboarding_service.py` stores OAuth state in a Python dict. Lost on restart. Not shared across instances.

**P1-10: No data export endpoint implemented**
- `GET /v1/account/export` is a stub that returns a placeholder. Required for GDPR compliance.

**P1-11: No consent management system**
- No consent table, no privacy policy version tracking, no opt-in/opt-out flags. Analytics data sent to PostHog without per-user consent.

---

## Section 4: Performance Bottlenecks

### Database

| Issue | Location | Impact |
|-------|----------|--------|
| N+1 queries in admin merchant list | admin_domain.py:179-196 | 101 queries for 100 merchants (~500ms) |
| All chargers loaded into memory | intent_service.py:51-82 | O(N) Python loop for nearest charger (~650ms) |
| Zero SQLAlchemy eager loading | Entire codebase | Any relationship access triggers lazy-load N+1 |
| Connection pool: 20 + 10 overflow | db.py:66-67 | Pool exhaustion under concurrent load |

### External APIs

| Issue | Location | Status |
|-------|----------|--------|
| Twilio calls | twilio_verify.py | GOOD — uses asyncio.to_thread with timeout |
| Stripe calls | stripe_service.py | BAD — synchronous, no timeout, no thread offloading |
| Google Places | google_places_new.py | OK — has geo-cell caching, no circuit breaker |
| HubSpot | hubspot.py | BAD — synchronous `requests.post()`, blocks threads |

### Infrastructure

| Component | Current | Recommended |
|-----------|---------|-------------|
| RDS instance | db.t3.micro (1 vCPU, 1GB RAM) | db.t3.small minimum (2 vCPU, 2GB RAM) |
| Backend ECS tasks | 1 (single point of failure) | 2-3 minimum |
| Backend CPU | 0.5 vCPU | 1 vCPU minimum |
| Backend memory | 1 GB | 2 GB minimum |
| Redis | Optional, disabled by default | Required for rate limiting |

---

## Section 5: Technical Debt Summary

### By the Numbers

| Metric | Count |
|--------|-------|
| Backend Python LOC | ~63,000 |
| Router files | 115 |
| Service files | 141 |
| Bare except clauses | 29+ |
| TODO/FIXME comments | 73+ |
| Stub service implementations | 12 |
| Router-to-router imports | 6 |
| Direct db.commit() in routers | 215 |
| Hardcoded demo values | 15+ |
| Console.log in production frontend | 10+ |
| Untracked git files | 226 |

### Top Debt Items

1. **29+ bare `except:` clauses** — Silent error swallowing across 15 files. This is how the OTP bug went undetected.
2. **73+ TODO/FIXME comments** — Incomplete features: virtual cards, data export, hard deletion, fleet management, AI rewards, city marketplace, coop pools.
3. **12 stub service files** — Services that return hardcoded/placeholder data: merchant_intel.py, s3_storage.py, verify_api.py, coop_pools.py, deals.py, fleet.py, tenant.py, offsets.py, iot.py, ai_growth.py, ai_rewards.py, city_marketplace.py.
4. **Two production entry points** — `main.py` and `main_simple.py` both exist. Production uses `main_simple.py`. The existence of two makes it unclear which one to modify.
5. **Duplicated config modules** — `config.py` and `core/config.py` both read environment variables. Changes to one don't affect the other.

### Compliance Gaps

| Requirement | Status |
|-------------|--------|
| PII encryption at rest | Partial — OAuth tokens encrypted (Fernet), email/phone/location plaintext |
| Encryption in transit | Yes — HTTPS enforced |
| Consent tracking | Not implemented |
| Right to erasure | Soft delete only; hard delete is a TODO |
| Data export | Not implemented (stub endpoint) |
| Data retention policy | Partial — some TTLs, many datasets indefinite |
| Analytics consent | Not implemented — PostHog enabled by default |

---

## Section 6: Architecture Quick Reference

### Production Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Python FastAPI on AWS App Runner | Entry point: `app.main_simple:app` |
| Database | PostgreSQL 15.4 on RDS (db.t3.micro) | SQLAlchemy ORM, Alembic migrations |
| Frontend (driver) | React + Vite + Tailwind | S3 + CloudFront |
| Frontend (merchant) | React + Vite + Tailwind | S3 + CloudFront |
| Frontend (admin) | React + Vite + Tailwind | S3 + CloudFront |
| Landing page | Next.js | S3 + CloudFront |
| iOS app | Swift WebView shell | Wraps driver web app via NativeBridge |
| Auth | JWT (HS256, 60-min expiry) + OTP via Twilio Verify | No refresh token endpoint |
| Payments | Stripe (checkout sessions, webhooks) | |
| SMS | Twilio Verify (OTP) + Twilio SMS (merchant notifications) | |
| Analytics | PostHog (frontend + backend) | |
| Error tracking | Sentry (optional) | |
| Places data | Google Places API (New) with geo-cell caching | |

### Key Files

| Purpose | File |
|---------|------|
| Production entry point | `backend/scripts/start.sh` → `app.main_simple:app` |
| OTP send/verify service | `backend/app/services/otp_service_v2.py` |
| Twilio Verify provider | `backend/app/services/auth/twilio_verify.py` |
| OTP provider factory | `backend/app/services/auth/otp_factory.py` |
| Rate limiting | `backend/app/services/auth/rate_limit.py` |
| Auth router (OTP endpoints) | `backend/app/routers/auth.py` |
| Admin router | `backend/app/routers/admin_domain.py` |
| Config (full) | `backend/app/core/config.py` |
| Config (simple, used by main_simple) | `backend/app/config.py` |
| Driver app auth client | `apps/driver/src/services/auth.ts` |
| Driver app OTP UI | `apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx` |

---

## Section 7: Cursor Implementation Prompts for P0 Fixes

### Prompt 1: Authenticate Merchant Arrival Endpoints

```
File: backend/app/routers/merchant_arrivals.py

Add authentication to all endpoints in this router. Every endpoint must require
a valid JWT token via `current_user = Depends(get_current_user)` from
`backend/app/dependencies/auth.py`.

For the POST /create endpoint: verify current_user.id matches the driver_id in the request body.
For the GET /merchant/{id} endpoint: verify current_user owns the merchant or is an admin.
For the PUT /{id}/confirm endpoint: verify current_user.id matches the session's driver_id.

Import: from app.dependencies.auth import get_current_user
```

### Prompt 2: Redis-Backed Rate Limiting

```
File: backend/app/services/auth/rate_limit.py

Replace in-memory rate limiting with Redis-backed rate limiting.

Requirements:
1. If REDIS_URL is set and reachable, use Redis for all rate limit state
2. If Redis is unavailable, fall back to in-memory (current behavior) with a warning log
3. Use Redis INCR + EXPIRE for sliding window rate limits
4. Key format: "rl:phone:{phone_hash}:{window}" and "rl:ip:{ip}:{window}"
5. Phone hash: SHA-256 of normalized phone, first 16 chars
6. Window: unix timestamp divided by window size (e.g., 60 for per-minute)
7. Do NOT change the public API of RateLimitService — check_rate_limit_start,
   check_rate_limit_verify, record_start_attempt, record_verify_attempt must keep
   the same signatures.

File: backend/app/core/config.py
- Change REDIS_ENABLED default from "false" to "true"
- Add RATE_LIMIT_REDIS_PREFIX = os.getenv("RATE_LIMIT_REDIS_PREFIX", "rl:")
```

### Prompt 3: Twilio Webhook Signature Validation

```
File: backend/app/routers/twilio_sms_webhook.py

Add Twilio request signature validation to the webhook endpoint.

Requirements:
1. Import RequestValidator from twilio.security
2. Read X-Twilio-Signature header from the request
3. Reconstruct the full URL (scheme + host + path)
4. Validate using RequestValidator(settings.TWILIO_AUTH_TOKEN).validate(url, params, signature)
5. If validation fails, return 403 with "Invalid signature"
6. Log failed validation attempts with client IP

The Twilio auth token is available at settings.TWILIO_AUTH_TOKEN from app.core.config.
The webhook URL must be reconstructed from the request, not hardcoded.
```

### Prompt 4: Session Creation Race Condition Fix

```
File: backend/alembic/versions/ (new migration)

Create a new Alembic migration that adds a partial unique index to prevent
duplicate active exclusive sessions:

CREATE UNIQUE INDEX ix_exclusive_sessions_active_user_merchant
ON exclusive_sessions (user_id, merchant_id)
WHERE status IN ('active', 'awaiting_arrival', 'merchant_notified');

File: backend/app/routers/exclusive.py

In the activate_exclusive() function, wrap the session creation in a try/except
that catches IntegrityError from the unique constraint. If caught, return the
existing active session instead of creating a duplicate.

from sqlalchemy.exc import IntegrityError
```

### Prompt 5: Billing Transaction Atomicity

```
File: backend/app/routers/merchant_arrivals.py (or wherever session completion + billing happens)

Wrap session state transition and billing event creation in a single database transaction.

Requirements:
1. Use db.begin_nested() for a savepoint
2. Update session status to 'completed'
3. Create billing_event row
4. db.commit() once for both operations
5. If either fails, db.rollback() the savepoint and return 500
6. Log both the session ID and billing event ID on success

Never commit the session state change without the billing event, or vice versa.
```

### Prompt 6: Replace Bare Except Clauses

```
Search the entire backend/app/ directory for bare `except:` clauses (no exception type specified).

For each one:
1. Replace `except:` with the most specific exception type that makes sense
   - JSON parsing: except (json.JSONDecodeError, ValueError)
   - Database: except SQLAlchemyError
   - HTTP: except HTTPException
   - General: except Exception as e (with logging)
2. Add logging: logger.error(f"...: {e}", exc_info=True)
3. Never use `except: pass` — at minimum log the error

Priority files (most bare excepts):
- backend/app/services/purchases.py (6 instances)
- backend/app/routers/admin_domain.py (2 instances)
- backend/app/routers/stripe_api.py (2 instances)
- backend/app/services/fraud.py (2 instances)
- backend/app/routers/purchase_webhooks.py (2 instances)
```

### Prompt 7: Authenticate Merchant Config Endpoint

```
File: backend/app/routers/merchant_config.py (or wherever PUT /v1/merchant/config lives)

Add authentication to the merchant notification config endpoint.

Requirements:
1. Require a valid JWT token via Depends(get_current_user)
2. Verify the authenticated user owns the merchant (check DomainMerchant.owner_user_id)
3. If not the owner, return 403 Forbidden
4. Log config changes with user_id and merchant_id
```

### Prompt 8: Stripe Webhook Idempotency

```
File: backend/app/routers/stripe_api.py (or the Stripe webhook handler)

Add idempotency checking to prevent webhook replay attacks.

Requirements:
1. After verifying the Stripe webhook signature, extract event.id
2. Check if event.id exists in a processed_webhook_events table (or Redis set)
3. If already processed, return 200 OK immediately (Stripe expects 200 for already-handled events)
4. If new, process the event and store event.id with a 72-hour TTL
5. Use a database table if Redis is unavailable:
   CREATE TABLE processed_stripe_events (
     event_id VARCHAR(255) PRIMARY KEY,
     processed_at TIMESTAMP DEFAULT NOW()
   );
6. Add a cleanup job to delete events older than 72 hours
```

### Prompt 9: Add Token Refresh Endpoint

```
File: backend/app/routers/auth.py

Add a POST /v1/auth/refresh endpoint.

Requirements:
1. Accept a refresh_token in the request body
2. Validate the refresh token (check signature, expiry, not revoked)
3. Issue a new access_token (60-min expiry) and new refresh_token (30-day expiry)
4. Revoke the old refresh_token (one-time use)
5. Store refresh tokens in the database with user_id, expires_at, revoked_at
6. Rate limit: max 10 refresh requests per hour per user

Schema for refresh_tokens table:
  id: UUID primary key
  user_id: FK to users
  token_hash: SHA-256 hash of the token (never store raw)
  expires_at: timestamp
  revoked_at: timestamp (nullable)
  created_at: timestamp

The frontend (apps/driver/src/services/auth.ts) should call this endpoint
when a 401 is received and a refresh token is available in localStorage.
```

### Prompt 10: Fix OTP Provider Default

```
File: backend/app/core/config.py

Change the OTP_PROVIDER default from "stub" to "twilio_verify":
  OTP_PROVIDER: str = os.getenv("OTP_PROVIDER", "twilio_verify")

File: backend/app/core/startup_validation.py

Add a validation that fails startup if OTP_PROVIDER is "twilio_verify" but
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_VERIFY_SERVICE_SID are empty.
This should run in ALL environments, not just ENV=prod.

Log the active OTP provider on startup: logger.info(f"OTP provider: {settings.OTP_PROVIDER}")
```

---

*Document generated: February 3, 2026*
*Codebase: Nerava (github.com/nerava)*
*Backend: ~63,000 LOC Python (FastAPI + SQLAlchemy)*
*Frontend: React + Vite (driver, merchant, admin) + Next.js (landing)*
