# Cursor Prompt: Validate Phone-First EV Arrival Implementation

## Context

Claude Code just implemented a "Phone-First" EV Arrival flow for Nerava. This flow allows Tesla drivers to check in using their car browser and receive an SMS link on their phone. The implementation spans backend, driver app, merchant app, and a new minimal link app.

## Your Task

1. **Validate all changes** - Review each file for correctness, security issues, and best practices
2. **Run tests** where applicable
3. **Create a validation report** suitable for ChatGPT to review

---

## Files to Validate

### Backend (Python/FastAPI)

#### New Files:
- `backend/app/utils/rate_limit.py` - Rate limiting utility with Redis/in-memory fallback
- `backend/app/utils/session_token.py` - HMAC-SHA256 signed session tokens

#### Modified Files:
- `backend/app/utils/ev_browser.py` - Added `require_ev_browser()` function
- `backend/app/services/checkin_service.py` - Added phone-first flow methods
- `backend/app/routers/checkin.py` - Added phone-first endpoints

### Frontend - Link App (New)

- `apps/link/package.json`
- `apps/link/tsconfig.json`
- `apps/link/tsconfig.node.json`
- `apps/link/vite.config.ts`
- `apps/link/index.html`
- `apps/link/src/main.tsx`
- `apps/link/src/App.tsx`
- `apps/link/src/index.css`
- `apps/link/src/vite-env.d.ts`

### Frontend - Driver App

- `apps/driver/src/App.tsx` - Added `/s/:token` route
- `apps/driver/src/components/PhoneCheckin/PhoneCheckinScreen.tsx` - New component
- `apps/driver/src/components/PhoneCheckin/index.ts` - Export
- `apps/driver/src/analytics/events.ts` - Added checkin events

### Frontend - Merchant App

- `apps/merchant/app/components/EVArrivals.tsx` - Added code redemption UI

---

## Validation Checklist

### Backend Validation

1. **Rate Limiting (`rate_limit.py`)**:
   - [ ] Thread-safe implementation
   - [ ] Redis fallback works correctly
   - [ ] Sliding window algorithm is correct
   - [ ] Rate limits: 3/day per phone, 10/hour per IP

2. **Session Tokens (`session_token.py`)**:
   - [ ] HMAC-SHA256 signature is secure
   - [ ] Base64url encoding is correct
   - [ ] Token expiration (30 min TTL) works
   - [ ] Constant-time comparison for signature verification

3. **EV Browser Detection (`ev_browser.py`)**:
   - [ ] Tesla User-Agent patterns are correct
   - [ ] Dev bypass only works in non-prod
   - [ ] Other EV brands detected (Rivian, Lucid, Polestar)

4. **Checkin Service (`checkin_service.py`)**:
   - [ ] `phone_start_checkin()` creates session correctly
   - [ ] `send_session_sms()` sends proper SMS format
   - [ ] `get_session_by_token()` verifies tokens properly
   - [ ] `activate_session()` links user to session
   - [ ] Session code generation uses correct alphabet (no ambiguous chars)

5. **Checkin Router (`checkin.py`)**:
   - [ ] `/phone-start` requires EV browser
   - [ ] `/s/{token}` returns correct session data
   - [ ] `/s/{token}/activate` works with auth
   - [ ] `/s/{token}/verify` checks geolocation
   - [ ] Rate limiting applied correctly
   - [ ] Analytics events fired

### Frontend Validation

6. **Link App (`apps/link/`)**:
   - [ ] Builds successfully with `npm run build`
   - [ ] Phone number formatting works (US numbers)
   - [ ] API call to `/api/v1/checkin/phone-start` is correct
   - [ ] Success screen shows session code
   - [ ] Error handling for rate limits, non-EV browser

7. **Driver App PhoneCheckinScreen**:
   - [ ] Token parsing from URL works
   - [ ] OTP flow integrates with existing auth
   - [ ] Geolocation verification works
   - [ ] Success screen shows code prominently
   - [ ] Error states handled gracefully

8. **Merchant App EVArrivals**:
   - [ ] Code input accepts 6 alphanumeric chars
   - [ ] Redemption API call uses correct endpoint/payload
   - [ ] Success/error feedback displayed
   - [ ] Already-redeemed codes handled

---

## Tests to Run

```bash
# Backend unit tests
cd backend
python3 -c "
from app.utils.rate_limit import CheckinRateLimiter
from app.utils.session_token import generate_session_token, verify_session_token, hash_phone
from app.utils.ev_browser import detect_ev_browser, require_ev_browser

# Test rate limiter
limiter = CheckinRateLimiter()
allowed, remaining = limiter.check_phone_limit('+15125551234')
assert allowed == True, 'Rate limit should allow first request'
print('Rate limiter: PASS')

# Test session token
token = generate_session_token('test-123', 'phonehash')
payload = verify_session_token(token)
assert payload is not None, 'Token should verify'
assert payload['session_id'] == 'test-123', 'Session ID should match'
print('Session token: PASS')

# Test phone hash
h = hash_phone('+15125551234')
assert len(h) == 64, 'Hash should be 64 chars (SHA256 hex)'
print('Phone hash: PASS')

# Test EV browser detection
tesla_ua = 'Mozilla/5.0 Tesla/2024.38.6'
info = detect_ev_browser(tesla_ua)
assert info.is_ev_browser == True, 'Tesla should be detected'
assert info.brand == 'Tesla', 'Brand should be Tesla'
print('EV browser detection: PASS')

print('\\nAll backend tests passed!')
"

# Frontend type check (link app)
cd apps/link
npm install
npm run build

# Frontend type check (driver app - may have pre-existing errors)
cd ../driver
npx tsc --noEmit 2>&1 | grep -i "PhoneCheckin" || echo "PhoneCheckin component has no type errors"
```

---

## Security Review Points

1. **HMAC Token Security**:
   - Uses `hmac.compare_digest()` for constant-time comparison
   - Secret key from settings (not hardcoded)
   - Token expiration enforced

2. **Rate Limiting**:
   - Phone hash used (not raw phone) for rate limit keys
   - IP rate limiting prevents abuse
   - Redis + in-memory fallback for reliability

3. **EV Browser Validation**:
   - Prevents session creation from non-EV browsers
   - Dev bypass only in non-production environments
   - User-Agent logged but truncated (privacy)

4. **Input Validation**:
   - Phone number normalized to E.164
   - Session code uses safe alphabet
   - Token format validated before parsing

---

## Expected Output Format

Create a report with the following structure:

```markdown
# Phone-First EV Arrival Validation Report

## Summary
- Overall Status: [PASS/FAIL/PARTIAL]
- Files Reviewed: X
- Issues Found: Y

## Backend Validation
### rate_limit.py
- Status: [PASS/FAIL]
- Notes: ...

### session_token.py
- Status: [PASS/FAIL]
- Notes: ...

[Continue for each file...]

## Frontend Validation
### apps/link/
- Build Status: [PASS/FAIL]
- Notes: ...

[Continue for each app...]

## Security Review
- [List any security concerns]

## Recommendations
- [List any improvements needed]

## Test Results
- [Paste test output]
```

---

## Additional Context

### API Endpoints Added

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/checkin/phone-start` | Start session (requires EV browser) |
| GET | `/v1/checkin/s/{token}` | Get session by signed token |
| POST | `/v1/checkin/s/{token}/activate` | Activate session after OTP |
| POST | `/v1/checkin/s/{token}/verify` | Verify geolocation |

### Session Code Format
- 6 alphanumeric characters
- Alphabet: `23456789ABCDEFGHJKMNPQRSTUVWXYZ` (no 0, 1, I, L, O)
- Example: `A3B5C7`

### Token Format
- `base64url(payload).base64url(signature)`
- Payload: `{"sid": "session-id", "ph": "phone-hash-prefix", "exp": timestamp}`
- TTL: 30 minutes

---

## When Complete

After validation, copy the report to share with ChatGPT for cross-review. Tag any critical issues that need immediate attention.
