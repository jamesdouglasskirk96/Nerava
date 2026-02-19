# Android App QA Checklist

Manual QA checklist for the Nerava Android shell app.
Test against the production web app (`https://app.nerava.network`) or local dev server.

---

## 1. Install & Launch

- [ ] App installs from APK without errors
- [ ] App launches to white screen, then loads web app
- [ ] Nerava logo / spinner visible during load
- [ ] No crash on first launch

## 2. Login / OTP Flow

- [ ] OTP entry screen renders correctly
- [ ] Keyboard appears and input is focused
- [ ] OTP code can be pasted (clipboard)
- [ ] Successful login persists across app restart (cookie/token)
- [ ] After login, native bridge receives auth token (`SET_AUTH_TOKEN` in logs)

## 3. WebView Behavior

- [ ] Pull-to-refresh works (swipe down → page reloads)
- [ ] Back button navigates within web app (not exit app)
- [ ] Back button exits app only when at root screen
- [ ] External links open in system browser (not in WebView)
- [ ] Text zoom is locked at 100% (system font size doesn't break layout)
- [ ] Page renders correctly with no missing CSS/JS

## 4. Offline / Error Handling

- [ ] Airplane mode → error overlay with "offline" message and retry button
- [ ] Retry button reloads page when connection restored
- [ ] Kill server (staging) → "server unavailable" error overlay
- [ ] Error overlay hides after successful retry

## 5. Location Permission Flow

- [ ] On first launch, permission dialog appears
- [ ] Granting "While Using App" enables location updates
- [ ] When bridge sends `REQUEST_ALWAYS_LOCATION`, background permission dialog appears
- [ ] Denying location doesn't crash — web app still works (degraded)
- [ ] Permission status reported correctly via `GET_PERMISSION_STATUS`

## 6. Geofence & Arrival Detection

- [ ] `SET_CHARGER_TARGET` logs charger geofence creation
- [ ] Entering charger zone (400m) → state changes to `NEAR_CHARGER`
- [ ] Dwelling 120s within 30m → state changes to `ANCHORED`
- [ ] After exclusive activation → state changes to `SESSION_ACTIVE`
- [ ] Leaving charger → state changes to `IN_TRANSIT`
- [ ] Entering merchant zone (40m) → state changes to `AT_MERCHANT`
- [ ] **Mock location test:** Use ADB or mock location app to simulate geofence entry
- [ ] Verify `POST /v1/native/session-events` appears in backend logs with `source: android_native`

## 7. Session Engine

- [ ] Session state persists across app kill (snapshot restore)
- [ ] Grace period (15 min) expires correctly → `SESSION_ENDED`
- [ ] Hard timeout (1 hour) expires correctly → `SESSION_ENDED`
- [ ] `END_SESSION` from web → session ends cleanly
- [ ] Foreground notification appears during active session
- [ ] Foreground notification clears when session ends

## 8. Push Notifications

- [ ] FCM token is logged on first launch
- [ ] (When backend supports it) Push notification appears
- [ ] Notification tap opens the app

## 9. Deep Links

- [ ] `adb shell am start -d "nerava://merchant/test123"` opens app
- [ ] `adb shell am start -d "https://app.nerava.network/merchant/test123"` opens app
- [ ] Deep link resolves to correct URL in WebView

## 10. Bridge Diagnostics (Debug Only)

- [ ] Diagnostics screen accessible from code
- [ ] Shows environment (URL, build type)
- [ ] Shows permission states
- [ ] Shows auth token presence

## 11. Security

- [ ] HTTPS enforced (no mixed content warnings in release)
- [ ] Auth token stored in EncryptedSharedPreferences
- [ ] Bridge messages rejected if WebView navigates to unauthorized origin
- [ ] ProGuard doesn't strip `@JavascriptInterface` methods

## 12. Battery & Performance

- [ ] Battery usage not excessive during idle (no wakelock abuse)
- [ ] Location updates respect accuracy mode (low when idle, high when near charger)
- [ ] Foreground service stops when session ends
- [ ] WebView process gone → auto-reload (no crash)

---

## Test Environment

| Variable | Value |
|----------|-------|
| Device | |
| Android Version | |
| Build Type | debug / staging / release |
| Web App URL | |
| API URL | |
| Tester | |
| Date | |
