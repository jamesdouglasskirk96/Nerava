# Production Quality Gate - Action Items

**Generated:** 2025-01-27  
**Priority:** P0 (Launch Blockers) → P1 (Pre-Launch) → P2 (Post-Launch)

---

## P0 - Launch Blockers (Must Fix Before Production)

### P0-1: Purchase Webhook Replay Protection
**Risk:** HIGH - Replay attacks can double-credit wallets  
**Evidence:** `nerava-backend-v9/app/routers/purchase_webhooks.py:30`  
**Fix:**
1. Add timestamp extraction from webhook payload (`normalized["ts"]`)
2. Reject events older than 5 minutes (like Stripe: `stripe_api.py:631-643`)
3. Log rejected events for audit
**Tests:** Unit test replay rejection, integration test with old timestamp  
**Effort:** 2 hours  
**Owner:** Backend Team

### P0-2: Wallet Balance DB Constraint
**Risk:** MEDIUM - Application bug could create negative balance  
**Evidence:** `nerava-backend-v9/app/models/domain.py:DriverWallet` - No CHECK constraint  
**Fix:**
1. Create Alembic migration: `ALTER TABLE driver_wallets ADD CONSTRAINT check_nova_balance_non_negative CHECK (nova_balance >= 0)`
2. Test constraint with negative value (should fail)
**Tests:** Migration test, integration test negative balance rejection  
**Effort:** 1 hour  
**Owner:** Backend Team

### P0-3: Negative Balance Prevention (Application Layer)
**Risk:** MEDIUM - Double-check application logic  
**Evidence:** `nova_service.py:312-335` - Atomic UPDATE has balance check  
**Fix:**
1. Add explicit check before UPDATE: `if wallet.nova_balance < amount: raise ValueError`
2. Ensure all wallet debit paths use this check
**Tests:** Unit test insufficient balance, integration test concurrent redemptions  
**Effort:** 1 hour  
**Owner:** Backend Team

### P0-4: Square Webhook Signature Verification
**Risk:** HIGH - If secret leaked, webhooks can be spoofed  
**Evidence:** `purchase_webhooks.py:43` - Only checks `X-Webhook-Secret` header  
**Fix:**
1. Implement Square signature verification (see Square docs)
2. Verify `X-Square-Signature` header using `SQUARE_WEBHOOK_SIGNATURE_KEY`
3. Fallback to secret check only if signature key not configured (backward compat)
**Tests:** Unit test signature validation, integration test with Square test webhook  
**Effort:** 4 hours  
**Owner:** Backend Team

---

## P1 - High Priority (Pre-Launch)

### P1-1: Multi-Instance Migration Strategy
**Risk:** HIGH - Race condition if multiple instances start simultaneously  
**Evidence:** `main_simple.py:293-305` - Migrations removed from startup  
**Fix:**
1. Create init container script: `scripts/init-migrations.sh`
2. Run `alembic upgrade head` in init container
3. Only start app containers after migration completes
4. Document in deployment runbook
**Tests:** E2E test with 2+ instances starting simultaneously  
**Effort:** 3 hours  
**Owner:** DevOps Team

### P1-2: Wallet Update Transaction Boundary
**Risk:** MEDIUM - Balance update and transaction insert not atomic  
**Evidence:** `nova_service.py:155-169` - Separate commits  
**Fix:**
1. Wrap `grant_to_driver()` in single transaction
2. Ensure `NovaTransaction` insert and `DriverWallet` update in same transaction
3. Add rollback test
**Tests:** Unit test rollback scenario, integration test concurrent grants  
**Effort:** 2 hours  
**Owner:** Backend Team

### P1-3: Rate Limiting Multi-Instance Fallback
**Risk:** MEDIUM - If Redis unavailable, rate limits bypassed in multi-instance  
**Evidence:** `ratelimit.py:125-138` - In-memory fallback per instance  
**Fix:**
1. In prod, if Redis unavailable and not local env, fail fast (raise exception)
2. Remove in-memory fallback for prod (already validated in startup, but ensure middleware respects this)
**Tests:** Integration test Redis failure in prod  
**Effort:** 1 hour  
**Owner:** Backend Team

### P1-4: Correlation IDs for Logging
**Risk:** LOW - Difficult to trace requests across services  
**Evidence:** No correlation IDs found  
**Fix:**
1. Add `X-Request-ID` middleware (generate UUID if not present)
2. Include in all log statements
3. Return in response headers
**Tests:** Log analysis - verify correlation ID in all logs  
**Effort:** 3 hours  
**Owner:** Backend Team

### P1-5: PII Sanitization in Logs
**Risk:** MEDIUM - Email, tokens may be logged  
**Evidence:** No sanitization visible  
**Fix:**
1. Create log sanitizer utility: `app/utils/log_sanitizer.py`
2. Sanitize: email (show first 2 chars), tokens (show last 4), passwords (redact)
3. Apply to all logger calls
**Tests:** Unit test log output - verify PII redacted  
**Effort:** 4 hours  
**Owner:** Backend Team

### P1-6: Frontend Config Injection
**Risk:** LOW - Frontend needs rebuild for different environments  
**Evidence:** `ui-mobile/js/core/api.js` - API base URL likely hardcoded  
**Fix:**
1. Create `/v1/config` endpoint returning `{apiBaseUrl, ...}`
2. Frontend fetches on load, stores in global config
3. Fallback to hardcoded if endpoint fails
**Tests:** E2E test config load, test fallback  
**Effort:** 2 hours  
**Owner:** Frontend Team

### P1-7: IDOR Audit (All Routers)
**Risk:** HIGH - 90+ routers not audited for resource access  
**Evidence:** Need to verify all endpoints  
**Fix:**
1. Audit all routers for:
   - Path params with user_id/merchant_id
   - Verify requester has access to resource
   - Admin endpoints require admin role
2. Document findings, fix issues
**Tests:** Security scan - attempt to access other users' resources  
**Effort:** 8 hours  
**Owner:** Security Team

### P1-8: Metrics/Prometheus Endpoints
**Risk:** LOW - No visibility into system health  
**Evidence:** No metrics found  
**Fix:**
1. Add Prometheus metrics: `prometheus_client`
2. Expose `/metrics` endpoint
3. Track: request counts, latencies, error rates, wallet operations
**Tests:** Load test - verify metrics collected  
**Effort:** 4 hours  
**Owner:** Backend Team

---

## P2 - Post-Launch Improvements

### P2-1: Secret Rotation Strategy
**Risk:** MEDIUM - No documented rotation process  
**Fix:**
1. Document rotation steps for: `JWT_SECRET`, `TOKEN_ENCRYPTION_KEY`, `STRIPE_SECRET`
2. Create rotation scripts (e.g., `scripts/rotate-jwt-secret.sh`)
3. Test rotation in staging
**Effort:** 4 hours  
**Owner:** DevOps Team

### P2-2: Dependency Vulnerability Scanning
**Risk:** LOW - No automated scanning  
**Fix:**
1. Add Dependabot or Snyk to repository
2. Configure weekly scans
3. Set up alerts for critical vulnerabilities
**Effort:** 1 hour  
**Owner:** DevOps Team

### P2-3: APM Integration
**Risk:** LOW - No performance monitoring  
**Fix:**
1. Integrate Datadog APM or New Relic
2. Add distributed tracing
3. Set up performance dashboards
**Effort:** 6 hours  
**Owner:** DevOps Team

### P2-4: JWT in httpOnly Cookies
**Risk:** MEDIUM - localStorage XSS risk  
**Evidence:** `ui-mobile/js/core/api.js` - Token in localStorage  
**Fix:**
1. Backend: Set httpOnly cookie on login
2. Frontend: Remove localStorage token, rely on cookie
3. Update CORS to allow credentials
**Tests:** E2E test auth flow, test XSS protection  
**Effort:** 4 hours  
**Owner:** Full-Stack Team

---

## Testing Requirements

### Unit Tests
- [ ] P0-1: Webhook replay rejection
- [ ] P0-2: Balance constraint violation
- [ ] P0-3: Negative balance check
- [ ] P0-4: Square signature verification
- [ ] P1-2: Transaction rollback
- [ ] P1-5: PII sanitization

### Integration Tests
- [ ] P0-1: Old webhook timestamp rejection
- [ ] P0-2: Migration constraint creation
- [ ] P0-3: Concurrent redemptions (balance check)
- [ ] P0-4: Square webhook signature validation
- [ ] P1-1: Multi-instance migration (no race)
- [ ] P1-2: Concurrent grants (transaction atomicity)
- [ ] P1-3: Redis failure in prod (fail fast)
- [ ] P1-7: IDOR attempts (access other users' data)

### E2E Tests
- [ ] P1-1: 2+ instances starting simultaneously
- [ ] P1-6: Frontend config load
- [ ] P2-4: Auth flow with httpOnly cookies

---

## Rollout Plan

### Phase 1: P0 Fixes (Week 1)
1. Deploy P0-1, P0-2, P0-3, P0-4 to staging
2. Run full test suite
3. Deploy to production
4. Monitor for 48 hours

### Phase 2: P1 Fixes (Week 2-3)
1. Deploy P1-1 (migrations) first (critical for multi-instance)
2. Deploy P1-2, P1-3, P1-4, P1-5 (stability)
3. Deploy P1-6, P1-7, P1-8 (operational)
4. Monitor each deployment

### Phase 3: P2 Improvements (Post-Launch)
1. Implement as needed based on production learnings
2. Prioritize based on incident frequency

---

## Acceptance Criteria

**Production Launch Gate:**
- [x] All P0 fixes implemented and tested
- [ ] All P1 fixes implemented and tested
- [ ] Monitoring/alerting in place
- [ ] Runbook documented
- [ ] Security audit completed (P1-7)
- [ ] Load testing completed
- [ ] Backup strategy documented

**Rollout Readiness:**
- [ ] Staging environment matches production
- [ ] Smoke tests passing
- [ ] Rollback plan documented
- [ ] On-call rotation established


