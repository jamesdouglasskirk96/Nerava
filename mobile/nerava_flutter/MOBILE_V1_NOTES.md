# Nerava Mobile v1 - Implementation Notes

## Reconnaissance Summary

### Existing Mobile Code
- **No Flutter code found** - Starting fresh
- `ui-mobile/` directory exists but is a **PWA/web app** (vanilla JS), not a native mobile app
- No existing Dart files or `pubspec.yaml` files in the repository

### Backend API Structure

#### Canonical v1 Auth Endpoints (use these)
- **POST `/v1/auth/login`** - Login with email/password
  - Request: JSON body `{ "email": "user@example.com", "password": "password" }`
  - Response: `{ "access_token": "...", "token_type": "bearer" }`
  - Location: `nerava-backend-v9/app/routers/auth_domain.py`

- **POST `/v1/auth/register`** - Register new user
  - Request: JSON body `{ "email": "...", "password": "...", "display_name": "..." (optional), "role": "driver" (optional) }`
  - Response: `{ "access_token": "...", "token_type": "bearer" }`

- **GET `/v1/auth/me`** - Get current user info
  - Requires: Authorization header with Bearer token
  - Response: `{ "id": 123, "email": "...", "display_name": "...", "role_flags": "...", "linked_merchant": {...} (optional) }`

- **POST `/v1/auth/logout`** - Logout (clears HTTP-only cookie on web)

#### Legacy Auth Endpoints (avoid for v1)
- `/auth/login` - Legacy OAuth2 form-based endpoint (kept for backward compat)
- `/auth/register` - Legacy endpoint

#### Backend URLs
- **Production API**: `https://web-production-526f6.up.railway.app`
- **Development API**: `http://127.0.0.1:8001`
- **Web App URL**: `https://nerava.network`

#### Authentication Method
- JWT tokens in `access_token` field
- Token stored in Authorization header: `Authorization: Bearer <token>`
- Web app uses HTTP-only cookies, but mobile app should use Bearer tokens
- No refresh tokens in current implementation (access tokens expire, user must re-login)

### Web App Integration
- Main web app lives at `https://nerava.network`
- Backend serves static files at `/app/` endpoint (mounts `ui-mobile/` directory)
- Web app uses cookies for auth in browser
- For Flutter WebView, we'll need to:
  1. Store JWT token in secure storage
  2. Inject token into WebView requests (via JavaScript or headers)
  3. OR use a special login URL with token parameter (if backend supports it)

### Key Findings
1. Backend uses FastAPI with SQLAlchemy
2. CORS is configured to allow credentials
3. Canonical v1 endpoints use `/v1/*` prefix
4. Auth uses JWT tokens (HS256 algorithm)
5. No refresh token mechanism - tokens expire after configured time (default 60 minutes)
6. Web app is a PWA with service worker

## Implementation Decisions

### Auth Strategy
- Store JWT token in `flutter_secure_storage`
- Send token in `Authorization: Bearer <token>` header for API calls
- For WebView: Inject token via JavaScript or load special authenticated URL
- Check token on app launch - if present and not expired, auto-login

### API Client
- Use `dio` for HTTP client (better interceptors for auth headers)
- Base URL configurable via `app_config.dart`
- Interceptor adds `Authorization: Bearer <token>` to all requests

### State Management
- Use **Riverpod** (minimal boilerplate, good for async)
- Providers for:
  - Auth state (logged in user)
  - WebView state
  - App config

## Manual Test Steps (to be validated)

1. **Launch app**
   - Should show splash screen
   - Check for stored token
   - If token exists → MainShell
   - If no token → LoginScreen

2. **Login**
   - Enter email/password
   - Call `/v1/auth/login`
   - Store token
   - Navigate to MainShell
   - WebView should load nerava.network (authenticated)

3. **Navigate WebView**
   - Click links within nerava.network → stay in WebView
   - Click external links → open in system browser

4. **Scan QR**
   - Open QR scanner
   - Scan QR code with nerava.network URL
   - Should navigate WebView to that URL
   - Scan invalid QR → show error

5. **Open Settings**
   - View account info (email from stored user)
   - View app version
   - Tap Privacy Policy → opens browser
   - Tap Terms → opens browser
   - Tap Sign Out → clears token, navigates to LoginScreen

6. **Logout**
   - Tap Sign Out in Settings
   - Token cleared from storage
   - Navigate to LoginScreen
   - WebView cookies cleared (if possible)

## Known Limitations / TODOs

- [x] Backend doesn't provide refresh tokens - users must re-login after token expires (documented, not a blocker for v1)
- [x] WebView auth integration - implemented via JavaScript token injection (may need refinement)
- [x] iOS camera permissions - added to Info.plist with proper description
- [ ] App icons and splash screen need final artwork (scaffold code ready)
- [ ] Privacy Policy and Terms URLs need verification (currently placeholder URLs)

## Implementation Status

1. ✅ Reconnaissance complete
2. ✅ Create Flutter app skeleton
3. ✅ Implement auth layer
4. ✅ Implement navigation
5. ✅ Implement WebView screen
6. ✅ Implement QR scanner
7. ✅ Implement settings screen
8. ✅ Wire iOS/Android config

**All core v1 features implemented!** See `IMPLEMENTATION_SUMMARY.md` for details.

