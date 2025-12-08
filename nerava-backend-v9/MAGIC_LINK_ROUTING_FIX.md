# Magic-Link Auth Endpoint Routing Fix

## Summary

Fixed magic-link authentication endpoints to be available at `/v1/auth/*` paths, matching frontend expectations. The endpoints were previously only available at `/auth/magic_link/*` (legacy router). They are now also available at `/v1/auth/magic_link/*` (canonical router).

## Changes Made

### File Modified: `nerava-backend-v9/app/routers/auth_domain.py`

1. **Added imports**:
   - `from jose import jwt` - for JWT token encoding/decoding
   - `from datetime import datetime` - for token expiration
   - `from app.models import User, UserPreferences` - for user creation
   - `from app.core.security import hash_password, create_access_token` - for password hashing and token creation
   - `from app.core.email_sender import get_email_sender` - for email sending

2. **Added helper function**:
   - `create_magic_link_token(user_id: int, email: str) -> str` - creates time-limited magic link tokens (15 min expiry)

3. **Added request/response models**:
   - `MagicLinkRequest` - email input for magic link request
   - `MagicLinkVerify` - token input for magic link verification

4. **Added endpoints**:
   - `POST /v1/auth/magic_link/request` - requests a magic link for email-only authentication
   - `POST /v1/auth/magic_link/verify` - verifies magic link token and creates session

## Endpoint Details

### POST /v1/auth/magic_link/request

- **Input**: `{"email": "user@example.com"}`
- **Behavior**:
  - Looks up or creates user (with placeholder password for magic-link-only users)
  - Generates time-limited JWT token (15 minutes)
  - Sends email with magic link URL (console logger for dev)
- **Output**: `{"message": "Magic link sent to your email", "email": "user@example.com"}`
- **Logging**: `[Auth][MagicLink] Request for <email>`

### POST /v1/auth/magic_link/verify

- **Input**: `{"token": "..."}`
- **Behavior**:
  - Verifies token signature and expiration
  - Checks token purpose is "magic_link"
  - Creates session token using `AuthService.create_session_token()`
  - Sets HTTP-only cookie (consistent with `/login`)
- **Output**: `{"access_token": "...", "token_type": "bearer"}`
- **Logging**: 
  - Success: `[Auth][MagicLink] Verify success for user_id=<id>`
  - Failures: `[Auth][MagicLink] Verify failed: <reason>`

## Final Auth Route Structure

### Canonical `/v1/auth/*` endpoints (auth_domain.py):
- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `POST /v1/auth/logout`
- `GET /v1/auth/me`
- **`POST /v1/auth/magic_link/request`** ✅ (newly added)
- **`POST /v1/auth/magic_link/verify`** ✅ (newly added)

### Legacy `/auth/*` endpoints (auth.py) - still available:
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/magic_link/request` (backward compatibility)
- `POST /auth/magic_link/verify` (backward compatibility)

## Verification

- ✅ Endpoints are at `/v1/auth/magic_link/*` paths
- ✅ Endpoints coexist with existing `/v1/auth/login` and `/v1/auth/register`
- ✅ Uses `TokenResponse` model (consistent with auth_domain patterns)
- ✅ Uses `AuthService.create_session_token()` for consistency
- ✅ Sets HTTP-only cookies (consistent with login endpoint)
- ✅ Proper logging with `[Auth][MagicLink]` tags
- ✅ No frontend files were modified
- ✅ No breaking changes to existing password-based auth

## Next Steps

The frontend can now call:
- `POST /v1/auth/magic_link/request` with `{"email": "user@example.com"}`
- `POST /v1/auth/magic_link/verify` with `{"token": "..."}`

These endpoints match the frontend API client expectations in `ui-mobile/js/core/api.js`.

