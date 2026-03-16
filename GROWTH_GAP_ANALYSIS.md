# Nerava Growth Readiness Gap Analysis

**Date:** 2026-03-04
**Scope:** Android Play Store launch + iOS hardening before major growth push
**Status:** Living document — update as items are resolved

---

## Summary

5 audits were run across the full stack: Android native, iOS native, backend, driver web app, and infrastructure/CI. Findings are prioritized into Critical (blockers), High (pre-launch), Medium (pre-scale), and Low (nice-to-have).

**Scorecard:**
| Area | Ready? | Blockers |
|------|--------|----------|
| Android | 75% | Firebase project, app icons, data safety |
| iOS | 94% | Apple Sign-In entitlement |
| Backend | 85% | Data retention, sync push |
| Driver Web | 80% | Consent gating, bundle size |
| Infra/CI | 60% | Tesla key leak, no native CI, Terraform drift |

---

## CRITICAL / Blockers

### 1. [SECURITY] Tesla Private Key in Repo
- **Location:** `infra/certs/` (untracked but visible in git status)
- **Risk:** Private keys for Tesla Fleet Telemetry sitting in repo. Security incident if pushed.
- **Fix:** Rotate the key immediately, add `infra/certs/` to `.gitignore`, store in AWS Secrets Manager.
- **Status:** [ ] Not started

### 2. [ANDROID] No Firebase Project / google-services.json
- **Impact:** Android app won't compile for release. `build.gradle.kts` applies Google Services plugin — build fails without this file.
- **Fix:**
  1. Create Firebase project at console.firebase.google.com
  2. Add Android app (`network.nerava.app`)
  3. Download `google-services.json` → `mobile/nerava_android/app/`
  4. Enable Cloud Messaging
  5. Generate service account key → set `FIREBASE_CREDENTIALS_JSON` env var in App Runner
- **Status:** [ ] Not started

### 3. [iOS] Sign in with Apple Entitlement Missing
- **Impact:** iOS app supports Apple Sign-In in login modal but entitlements file doesn't include `com.apple.developer.applesignin`. App Review will reject.
- **Fix:** Add capability in Xcode → Signing & Capabilities → + Sign in with Apple. Also enable in Apple Developer portal under App IDs.
- **Status:** [ ] Not started

### 4. [BACKEND] No Data Retention Policy
- **Impact:** `session_events` table grows unbounded. At 100K drivers (~1M rows/month), DB hits ~100GB/year with indexes.
- **Fix:**
  - TTL-based archival to S3 (sessions older than 90 days)
  - Partition `session_events` by `created_at` month
  - Add `pg_cron` or scheduled Lambda cleanup job
- **Status:** [ ] Not started

---

## HIGH Priority (Pre-Launch)

### 5. [ANDROID] Placeholder App Icons
- **Impact:** Default Android Studio icons, not Nerava brand. Play Store will look unprofessional.
- **Fix:** Generate adaptive icons from brand assets:
  - Foreground: Nerava logo on transparent
  - Background: Brand color
  - All densities: mdpi (48), hdpi (72), xhdpi (96), xxhdpi (144), xxxhdpi (192)
  - Adaptive icon XML files: `ic_launcher_foreground.xml`, `ic_launcher_background.xml`
- **Status:** [ ] Not started

### 6. [ANDROID] No Data Safety Declaration
- **Impact:** Google Play requires Data Safety section. Submission will be blocked without it.
- **Data collected:** Location (precise, always), phone number, device tokens, charging data, financial data (wallet/payout), analytics.
- **Fix:** Complete Data Safety form in Play Console during app submission.
- **Status:** [ ] Not started

### 7. [ANDROID + iOS] No Crash Reporting
- **Impact:** Native crashes (WebView process termination, background task failures, location service errors) go undetected in production.
- **Fix Android:** Add Sentry SDK or Firebase Crashlytics to `build.gradle.kts` and initialize in `NeravaApplication.kt`.
- **Fix iOS:** Add Sentry SDK via SPM and initialize in `NeravaApp.swift` `AppDelegate.didFinishLaunching`.
- **Status:** [ ] Not started

### 8. [BACKEND] Push Notifications are Synchronous
- **Impact:** `send_push_to_user()` sends inline during request handling. Campaign blast to 100K+ users blocks API threads.
- **Fix:** Move to background task queue. Options:
  - `asyncio.create_task()` (simplest, App Runner compatible)
  - Celery + SQS (more robust, adds infrastructure)
  - AWS Lambda triggered by SQS (serverless)
- **Status:** [ ] Not started

### 9. [BACKEND] RDS Connection Pool Risk
- **Impact:** App Runner scales to 25 instances × `pool_size=5` = 125 connections. RDS `db.t3.medium` allows ~150 max. Near saturation.
- **Fix options:**
  - Use RDS Proxy (~$30/month) — transparent connection pooling
  - Reduce pool_size to 3 with `max_overflow=2`
  - Upgrade RDS instance class
- **Status:** [ ] Not started

### 10. [WEB APP] Analytics Consent Not Gated
- **Impact:** PostHog analytics auto-initialized without explicit user consent. GDPR/CCPA violation risk.
- **Component:** `ConsentBanner` exists but may not gate PostHog initialization.
- **Fix:** Ensure PostHog only initializes after user accepts consent banner. Block tracking calls before consent.
- **Status:** [ ] Not started

### 11. [INFRA] No Android/iOS CI Pipelines
- **Impact:** Bad merge can break native builds. No one knows until manual testing.
- **Fix:** Add GitHub Actions workflows:
  - Android: `./gradlew assembleDebug` on PR + push to main
  - iOS: `xcodebuild -scheme Nerava build` on macOS runner
- **Status:** [ ] Not started

---

## MEDIUM Priority (Post-Launch, Pre-Scale)

### 12. [INFRA] Terraform Drift
- **Impact:** Terraform targets ECS/ALB but production runs App Runner + S3/CloudFront. State is local (no S3 remote backend). Infrastructure changes are manual and unauditable.
- **Fix:** Either migrate Terraform to match App Runner architecture, or deprecate Terraform and document the manual process.
- **Status:** [ ] Not started

### 13. [BACKEND] CloudWatch Log Costs
- **Impact:** At 100K drivers polling every 60s, ~108GB logs/month ($54+ ingestion). Every poll request fully logged.
- **Fix:** Sample 200-status `/poll` responses (log 1-in-10) or move to structured metrics.
- **Status:** [ ] Not started

### 14. [WEB APP] Bundle Size (867KB)
- **Impact:** Exceeds 500KB recommended threshold. Slower first-load on 3G (common at parking garages).
- **Fix:** Code-split Leaflet map, analytics SDK, and heavy modal components. Lazy-load below-fold features.
- **Status:** [ ] Not started

### 15. [WEB APP] No Service Worker / Offline Support
- **Impact:** Driver enters parking garage (common at chargers), loses connectivity, sees blank page.
- **Fix:** Add basic service worker for app shell caching. Workbox or manual SW with cache-first for static assets.
- **Status:** [ ] Not started

### 16. [INFRA] Missing Frontend Deploy Automation
- **Impact:** Only backend + driver app have documented deploy steps. Merchant, admin, console, landing are manual S3 syncs.
- **Fix:** Create CI deploy jobs or `scripts/deploy-frontend.sh` for all apps.
- **Status:** [ ] Not started

### 17. [ANDROID] Deep Link Verification (assetlinks.json)
- **Impact:** Without `assetlinks.json` at `https://nerava.network/.well-known/`, Android App Links show disambiguation dialog instead of opening app directly.
- **Fix:** Deploy `assetlinks.json` to S3 with release keystore SHA-256 fingerprint. CloudFront must pass through `.well-known/` path.
- **Status:** [ ] Not started

---

## LOW Priority (Nice-to-Have)

### 18. [iOS] Background App Refresh
- **Impact:** No `BGAppRefreshTask` registration. Session polling stops when backgrounded. Driver locks phone mid-charge → no updates until app reopened.
- **Fix:** Register background task in `Info.plist` + `BGTaskScheduler`.
- **Status:** [ ] Not started

### 19. [ANDROID] Adaptive Theme / Edge-to-Edge
- **Impact:** Android 15 enforces edge-to-edge. App should handle window insets and support Material You dynamic color.
- **Status:** [ ] Not started

### 20. [WEB APP] Accessibility Gaps
- **Impact:** Missing `aria-live` regions for session state changes, toast announcements, loading states. WCAG 2.1 AA compliance needed for enterprise/government partnerships.
- **Status:** [ ] Not started

### 21. [ANDROID] Store Listing Assets
- **Items needed:**
  - 2+ phone screenshots (1080x1920)
  - Feature graphic (1024x500)
  - Short description (80 chars max)
  - Full description (4000 chars max)
  - Privacy policy URL (publicly accessible)
  - IARC content rating questionnaire
  - Target audience: 18+ (financial transactions)
- **Status:** [ ] Not started

---

## Completed Items

### [ANDROID] FCM Token Pipeline — DONE (2026-03-04)
Full pipeline implemented: Android native → JS bridge → web app → backend API → FCM routing.
- Files: `BridgeMessage.kt`, `BridgeInjector.kt`, `NativeBridge.kt`, `FCMService.kt`, `MainActivity.kt`

### [ANDROID] Bridge Parity with iOS — DONE (2026-03-04)
All 3 missing message types added: `DEVICE_TOKEN_REGISTERED`, `OPEN_EXTERNAL_URL`, `PUSH_DEEP_LINK`.

### [WEB APP] Platform Detection Fix — DONE (2026-03-04)
Changed hardcoded `'ios'` to UA-based detection in `DriverHome.tsx` for device token registration.

### [BACKEND] Dual-Platform Push (APNs + FCM) — DONE (2026-03-04)
`push_service.py` now routes by `device.platform`: Android → FCM, iOS → APNs.

### [ANDROID] Release Signing Config — DONE (2026-03-04)
`build.gradle.kts` has signing config, `keystore.properties.example` created, `.gitignore` updated.

### [ANDROID] ProGuard Rules — DONE (2026-03-04)
Keep rules for bridge classes, `@JavascriptInterface` methods, OkHttp, Firebase.

---

## Recommended Implementation Order

| # | Item | Type | Est. Effort |
|---|------|------|-------------|
| 1 | Rotate Tesla key, add to Secrets Manager | Manual/DevOps | 1 hour |
| 2 | Create Firebase project + google-services.json | Manual | 30 min |
| 3 | Add Apple Sign-In entitlement to iOS | Code | 15 min |
| 4 | Generate Nerava app icons for Android | Design + Code | 1 hour |
| 5 | Add Sentry to Android + iOS native | Code | 2 hours |
| 6 | Add data retention job for session_events | Backend code | 3 hours |
| 7 | Fix analytics consent gating | Frontend code | 1 hour |
| 8 | Async push notifications | Backend code | 2 hours |
| 9 | Android/iOS CI workflows | DevOps | 2 hours |
| 10 | Data Safety declaration | Manual | 1 hour |
| 11 | Deploy assetlinks.json | DevOps | 15 min |
| 12 | Prepare store listing assets | Design | 2 hours |
| 13 | Submit to Play Store | Manual | 1 hour |

Items 1-7 are blockers/high-priority. Items 8-13 should be done before or shortly after launch.

---

## Manual Steps Required (Cannot Be Automated by Claude)

1. Create Firebase project + download `google-services.json`
2. Generate Firebase service account key → set `FIREBASE_CREDENTIALS_JSON` env var
3. Generate release keystore + create `keystore.properties`
4. Create Play Store developer account ($25 one-time fee)
5. Deploy `assetlinks.json` to `nerava.network/.well-known/`
6. Prepare screenshots + listing assets (design work)
7. Upload AAB + complete Play Store listing
8. Rotate Tesla private key in Tesla Developer portal
9. Add Apple Sign-In capability in Apple Developer portal
10. Complete IARC content rating questionnaire
