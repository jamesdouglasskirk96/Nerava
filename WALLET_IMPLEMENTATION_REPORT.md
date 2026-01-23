# Wallet Pass Implementation Report

**Date:** 2025-01-27  
**Auditor:** Nerava Wallet Pass Implementation Auditor  
**Scope:** Apple Wallet Pass (.pkpass) implementation audit against official Apple PassKit guidance

---

## 1. Executive Summary

- **Current State:** Functional wallet pass generation with signing support, PassKit Web Service endpoints implemented, but missing critical production hardening
- **Critical Gaps:** Missing HTTP caching headers, no WWDR intermediate certificate chain validation, incomplete image asset validation, no rate limiting on pass issuance
- **Security Concerns:** Pass issuance endpoints lack anti-abuse measures; authentication tokens exist but no expiry/revocation mechanism
- **Production Readiness:** ~70% - Core functionality works, but missing headers, caching, and security hardening required for production
- **Recommendation:** Address P0 items before production deployment; P1 items within 2 weeks; P2 items for enhanced UX

---

## 2. Current Implementation Map

### 2.1 File Structure

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **Pass Generator** | `nerava-backend-v9/app/services/apple_wallet_pass.py` | Creates pkpass bundles, signs manifests |
| **API Endpoints** | `nerava-backend-v9/app/routers/wallet_pass.py` | REST endpoints for pass creation, PassKit Web Service |
| **PassKit Web Service** | `nerava-backend-v9/app/routers/wallet_pass.py` (lines 946-1286) | Device registration, pass updates, serial listing |
| **Models** | `nerava-backend-v9/app/models/domain.py` | `DriverWallet`, `ApplePassRegistration` |
| **Frontend** | `ui-mobile/js/pages/wallet-pass.js` | UI for pass download |
| **Assets** | `wallet-pass/assets/`, `ui-mobile/assets/pass/` | Image assets (icon, logo) |
| **Config** | `nerava-backend-v9/app/core/config.py` | Environment variable definitions |
| **Tests** | `nerava-backend-v9/tests/unit/test_apple_wallet_pass.py` | Unit tests for pass generation |

### 2.2 Key Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|-------|
| `/v1/wallet/pass/apple/create` | POST | Generate and download pkpass | ✅ Implemented |
| `/v1/wallet/pass/apple/refresh` | POST | Refresh existing pass | ✅ Implemented |
| `/v1/wallet/pass/apple/preview` | GET | Preview unsigned pass (debug) | ✅ Implemented |
| `/v1/wallet/pass/apple/eligibility` | GET | Check user eligibility | ✅ Implemented |
| `/v1/wallet/pass/apple/devices/{deviceLibraryId}/registrations/{passTypeId}/{serial}` | POST | Register device (PassKit) | ✅ Implemented |
| `/v1/wallet/pass/apple/devices/{deviceLibraryId}/registrations/{passTypeId}/{serial}` | DELETE | Unregister device (PassKit) | ✅ Implemented |
| `/v1/wallet/pass/apple/devices/{deviceLibraryId}/registrations/{passTypeId}` | GET | List serials needing updates | ✅ Implemented |
| `/v1/wallet/pass/apple/passes/{passTypeId}/{serial}` | GET | Get updated pass (PassKit) | ✅ Implemented |

### 2.3 Environment Variables

| Variable | Purpose | Status |
|----------|---------|-------|
| `APPLE_WALLET_SIGNING_ENABLED` | Enable/disable signing | ✅ Configured |
| `APPLE_WALLET_PASS_TYPE_ID` | Pass Type Identifier | ✅ Configured |
| `APPLE_WALLET_TEAM_ID` | Apple Developer Team ID | ✅ Configured |
| `APPLE_WALLET_CERT_P12_PATH` | P12 certificate path | ✅ Configured |
| `APPLE_WALLET_CERT_PATH` | PEM certificate path | ✅ Configured |
| `APPLE_WALLET_KEY_PATH` | Private key path | ✅ Configured |
| `APPLE_WALLET_KEY_PASSWORD` | Key password (optional) | ✅ Configured |
| `APPLE_WALLET_APNS_KEY_ID` | APNs key ID (push) | ✅ Configured |
| `APPLE_WALLET_APNS_AUTH_KEY_PATH` | APNs auth key path | ✅ Configured |

---

## 3. Requirements Checklist

| Requirement | Status | Evidence | Fix Required |
|-------------|--------|----------|--------------|
| **HTTP Headers & MIME Type** |
| Content-Type: `application/vnd.apple.pkpass` | ✅ **PASS** | `wallet_pass.py:544, 636, 729, 1271` | None |
| Content-Disposition header | ✅ **PASS** | `wallet_pass.py:546, 638, 731, 1273` | None |
| Cache-Control headers | ❌ **FAIL** | Not found | Add `Cache-Control: no-cache, no-store, must-revalidate` |
| ETag header | ❌ **FAIL** | Not found | Add ETag based on pass content hash |
| Last-Modified header | ❌ **FAIL** | Not found | Add Last-Modified based on wallet_activity_updated_at |
| **Pass Structure** |
| pass.json formatVersion | ✅ **PASS** | `apple_wallet_pass.py:228` | None |
| passTypeIdentifier | ✅ **PASS** | `apple_wallet_pass.py:229` | None |
| serialNumber (non-PII) | ✅ **PASS** | `apple_wallet_pass.py:231` (uses opaque token) | None |
| teamIdentifier | ✅ **PASS** | `apple_wallet_pass.py:232` | None |
| webServiceURL | ✅ **PASS** | `apple_wallet_pass.py:221, 256` | None |
| authenticationToken | ✅ **PASS** | `apple_wallet_pass.py:257` (encrypted at rest) | None |
| **Image Assets** |
| icon.png (29x29 or 58x58) | ⚠️ **UNKNOWN** | `apple_wallet_pass.py:478-486` (checks exist, not size) | Validate dimensions |
| logo.png (160x50 or 320x100) | ⚠️ **UNKNOWN** | `apple_wallet_pass.py:489-497` (checks exist, not size) | Validate dimensions |
| strip.png (optional) | ❌ **MISSING** | Not implemented | Add if using strip image |
| **Signing** |
| Manifest.json with SHA1 | ✅ **PASS** | `apple_wallet_pass.py:265-276` | None |
| Signature file | ✅ **PASS** | `apple_wallet_pass.py:375-379, 512-513` | None |
| PKCS1v15 padding | ✅ **PASS** | `apple_wallet_pass.py:377` | None |
| SHA1 hash | ✅ **PASS** | `apple_wallet_pass.py:378` | None |
| WWDR intermediate cert | ❌ **MISSING** | Not validated in chain | Validate WWDR cert in chain |
| **PassKit Web Service** |
| POST registration endpoint | ✅ **PASS** | `wallet_pass.py:946-1041` | None |
| DELETE unregistration | ✅ **PASS** | `wallet_pass.py:1044-1084` | None |
| GET registrations list | ✅ **PASS** | `wallet_pass.py:1087-1181` | None |
| GET pass by serial | ✅ **PASS** | `wallet_pass.py:1184-1286` | None |
| AuthenticationToken validation | ✅ **PASS** | `wallet_pass.py:900-943` | None |
| Push token storage | ✅ **PASS** | `wallet_pass.py:977-983, 1006` | None |
| **Security** |
| Opaque serial numbers | ✅ **PASS** | `apple_wallet_pass.py:231` (nerava-{token}) | None |
| Encrypted auth tokens | ✅ **PASS** | `domain.py:139` (encrypted at rest) | None |
| Rate limiting | ❌ **FAIL** | Not implemented | Add rate limiting to create/refresh |
| Token expiry | ❌ **FAIL** | No expiry mechanism | Add expiry/revocation |
| CSRF protection | ⚠️ **UNKNOWN** | Depends on FastAPI middleware | Verify CSRF middleware |
| **Distribution** |
| Safari download handling | ⚠️ **UNKNOWN** | Frontend uses blob download | Test Safari behavior |
| Redirect after download | ❌ **MISSING** | No redirect mechanism | Add redirect to success page |
| Error handling | ✅ **PASS** | `wallet_pass.py:550-572` | None |

---

## 4. Security & Abuse Analysis

### 4.1 Current Security Measures

✅ **Implemented:**
- Opaque `wallet_pass_token` (no PII in serial numbers)
- Encrypted `apple_authentication_token` at rest
- AuthenticationToken validation for PassKit endpoints
- User authentication required (`get_current_driver` dependency)
- Eligibility check (requires VehicleAccount)

❌ **Missing:**
- **Rate limiting** on `/pass/apple/create` and `/pass/apple/refresh` endpoints
- **Token expiry/revocation** mechanism for authentication tokens
- **IP-based throttling** for suspicious patterns
- **Audit logging** for pass generation events
- **One-time-use tokens** for pass download links (if needed)

### 4.2 Abuse Vectors

1. **Pass Generation Spam:** User could repeatedly call `/pass/apple/create` to generate many passes
   - **Risk:** Medium - Wastes server resources, potential DoS
   - **Mitigation:** Rate limit to 5 requests per user per hour

2. **Token Reuse:** If authentication token is compromised, no expiry means indefinite access
   - **Risk:** High - Attacker could register devices and receive push updates
   - **Mitigation:** Add token rotation on pass refresh, expiry after 90 days

3. **Serial Enumeration:** Serial format `nerava-{token}` is predictable pattern
   - **Risk:** Low - Token is opaque, but pattern is visible
   - **Mitigation:** Consider adding random prefix or UUID-based serials

4. **PassKit Web Service Abuse:** Unauthenticated endpoints could be probed
   - **Risk:** Low - Endpoints require AuthenticationToken, but no rate limiting
   - **Mitigation:** Add rate limiting per deviceLibraryId

---

## 5. Distribution Flow Analysis

### 5.1 Current Flow

```
User clicks "Add to Apple Wallet"
  ↓
Frontend: POST /v1/wallet/pass/apple/create
  ↓
Backend: Validates eligibility, generates pkpass
  ↓
Response: application/vnd.apple.pkpass (no caching headers)
  ↓
Frontend: Creates blob URL, triggers download
  ↓
Safari: Opens pkpass file
  ↓
iOS: Prompts "Add to Wallet"
```

### 5.2 Issues Identified

1. **Missing Cache Headers:** Safari may cache pkpass files incorrectly
   - **Impact:** Users may receive stale passes
   - **Fix:** Add `Cache-Control: no-cache, no-store, must-revalidate`

2. **No ETag/Last-Modified:** Cannot use conditional requests
   - **Impact:** Unnecessary bandwidth usage
   - **Fix:** Add ETag based on pass content hash

3. **Blob Download Pattern:** Frontend downloads via blob URL
   - **Impact:** May not trigger Safari's native "Add to Wallet" prompt
   - **Fix:** Consider direct link or redirect to pkpass URL

4. **No Redirect After Download:** User stays on same page
   - **Impact:** Confusing UX - user doesn't know if pass was added
   - **Fix:** Redirect to success page or show confirmation modal

### 5.3 Safari-Specific Behavior

**Expected Behavior:**
- Safari should recognize `application/vnd.apple.pkpass` MIME type
- Should show "Add to Wallet" button in Safari UI
- Should handle pkpass files natively

**Current Implementation:**
- ✅ Correct MIME type set
- ⚠️ Frontend uses blob download (may bypass Safari's native handler)
- ❌ No caching headers (may cause Safari to cache incorrectly)

**Recommendation:**
- Test direct link access: `<a href="/v1/wallet/pass/apple/create" download="pass.pkpass">`
- Add proper caching headers
- Consider server-side redirect after pass generation

---

## 6. Test Coverage Assessment

### 6.1 Existing Tests

**Unit Tests** (`test_apple_wallet_pass.py`):
- ✅ pkpass bundle non-empty
- ✅ Contains pass.json
- ✅ No driver_id in pass.json
- ✅ Signing disabled returns unsigned
- ✅ wallet_pass_token creation

**Missing Tests:**
- ❌ HTTP headers validation
- ❌ Image asset dimension validation
- ❌ PassKit Web Service endpoint tests
- ❌ Authentication token validation tests
- ❌ Rate limiting tests
- ❌ Error handling tests (missing assets, invalid certs)
- ❌ E2E tests (Safari download flow)

### 6.2 Proposed Tests

**P0 Tests:**
1. `test_pkpass_content_type_header` - Verify `application/vnd.apple.pkpass`
2. `test_pkpass_cache_headers` - Verify `Cache-Control` headers
3. `test_image_dimensions` - Validate icon.png and logo.png sizes
4. `test_passkit_auth_token_validation` - Test AuthenticationToken validation
5. `test_rate_limiting_create_endpoint` - Verify rate limiting works

**P1 Tests:**
1. `test_passkit_registration_flow` - E2E registration flow
2. `test_passkit_update_flow` - E2E update flow
3. `test_safari_download_flow` - Test Safari native download
4. `test_wwdr_cert_validation` - Verify WWDR cert in chain

**P2 Tests:**
1. `test_token_expiry` - Test token rotation/expiry
2. `test_serial_number_uniqueness` - Verify no collisions
3. `test_pass_refresh_updates_timestamp` - Verify refresh updates last_generated_at

---

## 7. Prioritized Fix Plan

### P0: Must Fix Before Production

1. **Add HTTP Caching Headers**
   - **File:** `nerava-backend-v9/app/routers/wallet_pass.py`
   - **Lines:** 542-548, 634-640, 727-733, 1269-1275
   - **Fix:** Add headers: `Cache-Control: no-cache, no-store, must-revalidate`, `Pragma: no-cache`, `Expires: 0`
   - **Impact:** Prevents Safari caching issues

2. **Validate Image Asset Dimensions**
   - **File:** `nerava-backend-v9/app/services/apple_wallet_pass.py`
   - **Lines:** 477-497
   - **Fix:** Add PIL/Pillow validation for icon.png (29x29 or 58x58) and logo.png (160x50 or 320x100)
   - **Impact:** Ensures passes display correctly on all devices

3. **Add Rate Limiting**
   - **File:** `nerava-backend-v9/app/routers/wallet_pass.py`
   - **Lines:** 460, 575
   - **Fix:** Add rate limiting decorator (5 requests per user per hour)
   - **Impact:** Prevents abuse/DoS

4. **Add ETag/Last-Modified Headers**
   - **File:** `nerava-backend-v9/app/routers/wallet_pass.py`
   - **Lines:** 1269-1275 (PassKit GET pass endpoint)
   - **Fix:** Generate ETag from pass content hash, Last-Modified from wallet_activity_updated_at
   - **Impact:** Enables conditional requests, reduces bandwidth

5. **Validate WWDR Certificate Chain**
   - **File:** `nerava-backend-v9/app/services/apple_wallet_pass.py`
   - **Lines:** 279-433 (signing function)
   - **Fix:** Validate certificate chain includes WWDR intermediate certificate
   - **Impact:** Ensures passes install correctly on iOS devices

### P1: Fix Within 2 Weeks

1. **Add Token Expiry/Rotation**
   - **File:** `nerava-backend-v9/app/services/apple_wallet_pass.py`
   - **Lines:** 59-81 (`_ensure_apple_auth_token`)
   - **Fix:** Add expiry timestamp, rotate tokens every 90 days or on pass refresh
   - **Impact:** Reduces security risk of compromised tokens

2. **Improve Error Messages**
   - **File:** `nerava-backend-v9/app/routers/wallet_pass.py`
   - **Lines:** 550-572
   - **Fix:** Add more specific error messages for missing assets, invalid certs
   - **Impact:** Better debugging experience

3. **Add Audit Logging**
   - **File:** `nerava-backend-v9/app/routers/wallet_pass.py`
   - **Lines:** 460, 575, 946, 1184
   - **Fix:** Log all pass generation, registration, and update events
   - **Impact:** Better security monitoring

4. **Test Safari Download Flow**
   - **File:** `ui-mobile/js/pages/wallet-pass.js`
   - **Lines:** 94-197
   - **Fix:** Test direct link access vs blob download, add redirect after download
   - **Impact:** Better UX on Safari

5. **Add PassKit Web Service Tests**
   - **File:** `nerava-backend-v9/tests/api/test_wallet_passkit.py` (new)
   - **Fix:** Add integration tests for all PassKit endpoints
   - **Impact:** Prevents regressions

### P2: Enhancements for Better UX

1. **Add Strip Image Support**
   - **File:** `nerava-backend-v9/app/services/apple_wallet_pass.py`
   - **Lines:** 470-501
   - **Fix:** Add optional strip.png (320x84 or 640x168) for storeCard passes
   - **Impact:** Better visual design

2. **Add Pass Expiry Field**
   - **File:** `nerava-backend-v9/app/services/apple_wallet_pass.py`
   - **Lines:** 227-262 (`_create_pass_json`)
   - **Fix:** Add `expirationDate` field (optional, e.g., 1 year from creation)
   - **Impact:** Automatic cleanup of old passes

3. **Add Localization Support**
   - **File:** `nerava-backend-v9/app/services/apple_wallet_pass.py`
   - **Lines:** 227-262
   - **Fix:** Add `localizations` field with translated strings
   - **Impact:** Multi-language support

4. **Add Pass Update Push Notifications**
   - **File:** `nerava-backend-v9/app/services/apple_pass_push.py`
   - **Lines:** All
   - **Fix:** Implement APNs push notifications when wallet activity updates
   - **Impact:** Real-time pass updates

5. **Add Pass Analytics**
   - **File:** `nerava-backend-v9/app/routers/wallet_pass.py`
   - **Lines:** 946-1041 (registration endpoint)
   - **Fix:** Track pass installs, updates, device types
   - **Impact:** Better product insights

---

## 8. Decisions Needed

1. **Token Expiry Model**
   - **Question:** How long should authentication tokens be valid? (Recommendation: 90 days, rotate on refresh)
   - **Impact:** Security vs UX tradeoff

2. **Rate Limiting Threshold**
   - **Question:** How many pass generation requests per user per hour? (Recommendation: 5/hour)
   - **Impact:** Prevents abuse but may block legitimate refresh attempts

3. **Pass Update Model**
   - **Question:** Should we push updates immediately or batch them? (Recommendation: Immediate for balance changes, batched for timeline updates)
   - **Impact:** APNs costs vs UX

4. **Serial Number Format**
   - **Question:** Keep `nerava-{token}` or switch to UUID? (Recommendation: Keep current, add random prefix if needed)
   - **Impact:** Predictability vs simplicity

5. **Image Asset Storage**
   - **Question:** Store in repo, S3, or CDN? (Recommendation: S3/CDN for production)
   - **Impact:** Deployment complexity vs performance

6. **Pass Expiry Policy**
   - **Question:** Should passes expire? If so, when? (Recommendation: No expiry, but add expirationDate field for future)
   - **Impact:** User experience vs cleanup

7. **Error Recovery**
   - **Question:** What happens if pass generation fails mid-request? (Recommendation: Return 500, log error, show user-friendly message)
   - **Impact:** User experience

8. **WWDR Certificate Handling**
   - **Question:** Bundle WWDR cert in repo or download at runtime? (Recommendation: Bundle in repo, validate at startup)
   - **Impact:** Deployment complexity vs security

---

## 9. References & Official Documentation

### Apple Official Documentation
- [PassKit Programming Guide](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/PassKit_PG/)
- [PassKit Web Service Reference](https://developer.apple.com/library/archive/documentation/PassKit/Reference/PassKit_WebService/WebService.html)
- [WWDR Intermediate Certificates](https://www.apple.com/certificateauthority/)

### Key Requirements (from Apple docs)
- **MIME Type:** `application/vnd.apple.pkpass` (✅ Implemented)
- **Image Sizes:**
  - `icon.png`: 29x29 points (29x29px @1x, 58x58px @2x)
  - `logo.png`: 160x50 points (160x50px @1x, 320x100px @2x)
  - `strip.png`: 320x84 points (optional, 320x84px @1x, 640x168px @2x)
- **Signing:** SHA1 with PKCS1v15 padding (✅ Implemented)
- **WWDR Certificate:** Required in certificate chain (❌ Not validated)

### Best Practices (from community)
- **Caching:** Use `Cache-Control: no-cache` for pkpass files
- **ETag:** Generate from pass content hash for conditional requests
- **Rate Limiting:** 5-10 requests per user per hour
- **Token Expiry:** Rotate every 90 days or on suspicious activity

---

## 10. Summary

### Current State: ✅ Functional, ⚠️ Needs Hardening

The implementation has a solid foundation with:
- ✅ Correct MIME type
- ✅ Proper signing mechanism
- ✅ Complete PassKit Web Service implementation
- ✅ Security-conscious token handling

However, production readiness requires:
- ❌ HTTP caching headers
- ❌ Image dimension validation
- ❌ Rate limiting
- ❌ WWDR certificate validation
- ❌ Token expiry mechanism

### Recommended Action Plan

1. **Week 1:** Fix P0 items (caching headers, image validation, rate limiting)
2. **Week 2:** Fix P1 items (token expiry, audit logging, tests)
3. **Week 3:** Test Safari download flow, deploy to staging
4. **Week 4:** Monitor production, iterate on P2 items

### Risk Assessment

- **Security Risk:** Medium (missing rate limiting, token expiry)
- **UX Risk:** Low (core functionality works)
- **Production Risk:** Medium (missing headers may cause Safari issues)

**Recommendation:** Address P0 items before production deployment.

---

**Report Generated:** 2025-01-27  
**Next Review:** After P0 fixes implemented




