# Nerava Release Guide

Complete checklist for production launch. Covers mobile apps, push notifications, payments, auth, subscriptions, and API access for all user types.

**Estimated time:** 4-6 hours of setup (spread across today + tomorrow)

---

## TABLE OF CONTENTS

1. [Platform Status Summary](#1-platform-status-summary)
2. [Stripe Account Setup (Real Money)](#2-stripe-account-setup-real-money)
3. [Push Notification Credentials](#3-push-notification-credentials)
4. [Android Play Store Release](#4-android-play-store-release)
5. [iOS App Store Hardening](#5-ios-app-store-hardening)
6. [Sponsor Console — Campaign Payments](#6-sponsor-console--campaign-payments)
7. [Merchant Portal — Subscriptions & Billing](#7-merchant-portal--subscriptions--billing)
8. [Partner / Developer API Access](#8-partner--developer-api-access)
9. [App Runner Environment Variables](#9-app-runner-environment-variables)
10. [Auth & Account Readiness Matrix](#10-auth--account-readiness-matrix)
11. [Revenue Readiness Matrix](#11-revenue-readiness-matrix)
12. [Quick Reference Commands](#12-quick-reference-commands)

---

## 1. PLATFORM STATUS SUMMARY

| Platform | Auth | Payments | Status |
|----------|------|----------|--------|
| Driver App (iOS) | Phone OTP, Apple, Google Sign-In | Stripe Express payouts | READY (after push creds) |
| Driver App (Android) | Same as iOS (WebView) | Same as iOS | READY (after Firebase + icons) |
| Merchant Portal | Google Business Profile OAuth | Stripe subscriptions + Nova purchase | READY (after Stripe price IDs) |
| Sponsor Console | Email OTP | Stripe Checkout for campaign funding | READY (after Stripe price IDs) |
| Admin Dashboard | Email/Password | N/A | READY |
| Partner API | API Key (admin-issued) | NOT IMPLEMENTED | Partial — no self-serve |
| Utility Partners | N/A | NOT IMPLEMENTED | Not started |

---

## 2. STRIPE ACCOUNT SETUP (REAL MONEY)

This is the most important step. Without it, drivers can't withdraw earnings, sponsors can't fund campaigns, and merchants can't subscribe.

### 2A. Activate Stripe Account for Live Mode

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. If still in test mode, click **"Activate payments"** in the top banner
3. Complete business verification:
   - Legal business name, EIN or SSN
   - Business address
   - Bank account for receiving funds
   - Identity verification (government ID)
4. Once approved, you'll see **"Live mode"** toggle in the dashboard

### 2B. Fund Your Stripe Account for Driver Payouts

Drivers withdraw via Stripe Express transfers. Stripe transfers come from YOUR Stripe balance. If the balance is $0, transfers fail silently.

**Option A: Pre-fund via bank transfer**
1. Stripe Dashboard → **Balances** → **Add to balance**
2. Transfer from your linked bank account (takes 2-3 business days)
3. Start with $500-1000 to cover initial driver withdrawals

**Option B: Let campaign payments fund it naturally**
- When sponsors pay for campaigns via Stripe Checkout, the funds land in your Stripe balance
- Driver payouts draw from this balance
- You need campaigns funded BEFORE drivers can withdraw

**Option C: Manual top-up**
```bash
# Create a top-up via Stripe API (instant if you have a card on file)
curl https://api.stripe.com/v1/topups \
  -u sk_live_YOUR_KEY: \
  -d amount=50000 \
  -d currency=usd \
  -d description="Initial balance for driver payouts" \
  -d source=YOUR_BANK_SOURCE_ID
```

### 2C. Get Live API Keys

1. Stripe Dashboard → **Developers** → **API keys**
2. Copy the **Secret key** (`sk_live_...`) — this goes in App Runner
3. Copy the **Publishable key** (`pk_live_...`) — this goes in frontend env vars

### 2D. Set Up Stripe Webhooks (Critical)

Webhooks drive the entire payment lifecycle. Without them, campaign funding confirmations, subscription updates, and payout completions won't work.

1. Stripe Dashboard → **Developers** → **Webhooks**
2. Click **"Add endpoint"**
3. URL: `https://api.nerava.network/v1/stripe/webhooks`
4. Select events:
   - `checkout.session.completed` (campaign funding + merchant subscriptions)
   - `customer.subscription.updated` (plan changes)
   - `customer.subscription.deleted` (cancellations)
   - `transfer.created` (driver payout initiated)
   - `transfer.reversed` (payout failed/reversed)
   - `payout.paid` (payout completed)
   - `payout.failed` (payout failed)
5. Copy the **Webhook signing secret** (`whsec_...`)
6. Set as `STRIPE_WEBHOOK_SECRET` in App Runner env vars

### 2E. Create Stripe Products & Prices for Subscriptions

Merchants subscribe to plans. You need to create these products in Stripe:

**Merchant Pro Plan:**
1. Stripe Dashboard → **Products** → **Add product**
2. Name: **"Nerava Merchant Pro"**
3. Description: "Access to analytics, exclusive offers, and priority listing"
4. Add a price: **$49/month** (recurring, monthly)
5. Copy the Price ID (`price_...`) → set as `STRIPE_PRICE_PRO_MONTHLY`

**Merchant Ads Flat Plan:**
1. Add another product: **"Nerava Ads"**
2. Description: "Flat-rate ad impressions to EV drivers near your location"
3. Add a price: **$99/month** (recurring, monthly)
4. Copy the Price ID → set as `STRIPE_PRICE_ADS_FLAT_MONTHLY`

**Campaign Funding (no product needed):**
- Sponsors pay custom amounts per campaign via Stripe Checkout
- Already handled dynamically — no Stripe product setup required

### 2F. Enable Stripe Connect for Driver Payouts

1. Stripe Dashboard → **Connect** → **Settings**
2. Enable **Express accounts** (drivers use this)
3. Set your platform profile:
   - Platform name: Nerava
   - Platform URL: https://nerava.network
   - Support email: support@nerava.network
4. Configure Express onboarding:
   - Country: US
   - Capabilities: Transfers
5. Set `ENABLE_STRIPE_PAYOUTS=true` in App Runner env vars

---

## 3. PUSH NOTIFICATION CREDENTIALS

### 3A. Firebase (Android FCM)

**Time: ~10 min**

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. **"Add project"** → Name: **"Nerava"** → Disable Google Analytics
3. **"Add app"** → Android → Package: **`network.nerava.app`**
4. Download `google-services.json` → place at `mobile/nerava_android/app/google-services.json`
5. Project Settings → **Service Accounts** → **"Generate new private key"**
6. Copy the entire JSON → set as `FIREBASE_CREDENTIALS_JSON` env var on App Runner

### 3B. APNs (iOS)

**Time: ~10 min**

1. [Apple Developer Portal](https://developer.apple.com/account/resources/authkeys/list) → **Keys** → **Create Key**
2. Check **"Apple Push Notifications service (APNs)"** → Download `.p8` file
3. Note the **Key ID** (10 chars) and **Team ID** (from Membership page)
4. Set on App Runner:

```
APNS_KEY_ID=YOUR_KEY_ID
APNS_TEAM_ID=YOUR_TEAM_ID
APNS_KEY_CONTENT=-----BEGIN PRIVATE KEY-----\nMIGT...full key content...\n-----END PRIVATE KEY-----
APNS_BUNDLE_ID=com.nerava.driver
APNS_USE_SANDBOX=false
```

---

## 4. ANDROID PLAY STORE RELEASE

### 4A. Code Parity (Already Done)

| Gap | Fix |
|-----|-----|
| `updateChargerGeofences()` | Added JS API + bridge handler + SessionEngine method |
| Haptic feedback | Added VibrationEffect for each state transition |
| Short link deep links | Added `/s/`, `/m/` routes + `link.nerava.network` |
| Auto-retry on network errors | Added 2 retries with 1.5s delay |
| OAuth popup WebView | Added `onCreateWindow` handler for Google/Apple/Stripe |

### 4B. App Icons

**Time: ~15 min**

Use [Android Asset Studio](https://romannurik.github.io/AndroidAssetStudio/icons-launcher.html):
1. Upload Nerava logo PNG
2. Download generated zip
3. Extract into `mobile/nerava_android/app/src/main/res/`

Required sizes:

| Size | Directory |
|------|-----------|
| 48x48 | `mipmap-mdpi/` |
| 72x72 | `mipmap-hdpi/` |
| 96x96 | `mipmap-xhdpi/` |
| 144x144 | `mipmap-xxhdpi/` |
| 192x192 | `mipmap-xxxhdpi/` |
| 432x432 | Adaptive icon foreground |

### 4C. Splash Screen

1. Add `splash_logo.png` (512x512) to `app/src/main/res/drawable/`
2. Create `app/src/main/res/drawable/splash_background.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@color/splash_bg"/>
    <item>
        <bitmap android:gravity="center" android:src="@drawable/splash_logo"/>
    </item>
</layer-list>
```
3. Add to `app/src/main/res/values/colors.xml`:
```xml
<color name="splash_bg">#1A1A2E</color>
```
4. Set splash theme on MainActivity in `AndroidManifest.xml`:
```xml
<activity android:name=".MainActivity" android:theme="@style/Theme.Nerava.Splash" ...>
```

### 4D. Release Keystore

```bash
keytool -genkey -v -keystore nerava-release.keystore \
  -alias nerava -keyalg RSA -keysize 2048 -validity 10000 \
  -storepass YOUR_STORE_PASSWORD -keypass YOUR_KEY_PASSWORD \
  -dname "CN=Nerava, OU=Mobile, O=Nerava Network, L=Austin, ST=TX, C=US"
```

**BACK THIS UP.** If you lose it, you can never update the app on Play Store.

Create `mobile/nerava_android/keystore.properties`:
```properties
storeFile=/path/to/nerava-release.keystore
storePassword=YOUR_STORE_PASSWORD
keyAlias=nerava
keyPassword=YOUR_KEY_PASSWORD
```

Build: `cd mobile/nerava_android && ./gradlew bundleRelease`

### 4E. Play Store Listing

**Time: ~30 min**

1. [Google Play Console](https://play.google.com/console) — $25 one-time fee
2. Create app → Category: **"Auto & Vehicles"**
3. Fill in:
   - **App name:** Nerava
   - **Short description:** Earn rewards while charging your EV
   - **Full description:** Nerava transforms your EV charging stops into earning opportunities. Connect your Tesla, charge at any supported charger, and earn cash rewards from local sponsors. Discover nearby merchants with exclusive deals while you charge.
   - **Screenshots:** 2+ phone screenshots (1080x1920)
   - **Feature graphic:** 1024x500 banner
   - **Privacy policy:** https://nerava.network/privacy
4. Upload the signed AAB
5. Submit for review (1-3 days for new apps)

---

## 5. iOS APP STORE HARDENING

The iOS app is already on TestFlight/App Store. These are hardening items:

### 5A. Rotate Tesla Private Keys

The `infra/certs/` directory contains Tesla Fleet API private keys that should NOT be in git.

1. Move keys to AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name "nerava/tesla-fleet-private-key" \
  --secret-string "$(cat infra/certs/com.tesla.3p.public-key.pem)" \
  --region us-east-1
```
2. Update `tesla_oauth.py` to read from Secrets Manager instead of file path
3. Delete `infra/certs/` from git history (use `git filter-branch` or BFG)

### 5B. App Store Screenshots

If updating the listing, capture screenshots showing:
- Map view with charger pins + gold star badges
- Vehicle card with charging animation
- Wallet with earnings
- Merchant details with exclusive offers

---

## 6. SPONSOR CONSOLE — CAMPAIGN PAYMENTS

### What Works Now
- Sponsors log in via email OTP at `console.nerava.network` (or wherever deployed)
- Sponsors create campaigns with budget, targeting rules, and activation criteria
- Campaigns are funded via Stripe Checkout (one-time payment)
- Webhook confirms funding → campaign can be activated
- Active campaigns match driver sessions and award incentives

### What's Missing

| Gap | Impact | Fix |
|-----|--------|-----|
| No saved payment methods | Sponsors re-enter card for each campaign | Add Stripe Customer creation + saved payment methods |
| No self-service signup | Admin must create sponsor accounts | Build public signup page on console |
| No campaign budget refunds | Unused budget stays in Nerava's Stripe balance | Implement refund endpoint for canceled campaigns |
| No spend reports/invoices | Sponsors can't download receipts | Add Stripe invoice retrieval endpoint |
| No auto-renew billing | Monthly campaigns require manual re-funding | Wire `auto_renew_budget_cents` to Stripe recurring |

### To Unblock Sponsors Today

1. **Create sponsor accounts manually:**
```bash
# Via email OTP — sponsor signs in, account auto-created
# OR create directly in admin dashboard
```

2. **Verify Stripe Checkout works in live mode:**
   - Set `STRIPE_SECRET_KEY=sk_live_...` in App Runner
   - Set `STRIPE_WEBHOOK_SECRET=whsec_...` in App Runner
   - Test: Create a campaign → Fund it → Verify webhook fires → Campaign status → "funded"

---

## 7. MERCHANT PORTAL — SUBSCRIPTIONS & BILLING

### What Works Now
- Merchants sign up via Google Business Profile OAuth at `merchant.nerava.network/claim`
- Merchants can subscribe to Pro or Ads plans via Stripe Checkout (subscription mode)
- Subscription lifecycle managed via webhooks (active → canceled → past_due)
- Merchants can cancel at period end
- Merchants can buy Nova point packages ($100/$450/$800)

### What's Missing

| Gap | Impact | Fix |
|-----|--------|-----|
| No Stripe Billing Portal | Merchants can't update card or view invoices | Add `POST /v1/merchant/billing/portal` → `stripe.billing_portal.Session.create()` |
| No plan upgrade/downgrade | Must cancel + resubscribe | Implement `stripe.Subscription.modify()` with proration |
| No invoice history endpoint | No receipts for merchants | Add `GET /v1/merchant/billing/invoices` → `stripe.Invoice.list()` |
| No payment method management | Can't change card without new subscription | Add card update via Billing Portal |
| No Stripe price IDs set | Subscriptions will 404 | Create products in Stripe Dashboard (see 2E) |
| No data licensing tier | No subscription for API/data access | Create new Stripe product + plan |

### To Unblock Merchants Today

1. **Create Stripe Products** (see Section 2E)
2. **Set price IDs in App Runner:**
```
STRIPE_PRICE_PRO_MONTHLY=price_XXXXXXXX
STRIPE_PRICE_ADS_FLAT_MONTHLY=price_XXXXXXXX
```
3. Test: Merchant signs up → subscribes → webhook confirms → subscription active

---

## 8. PARTNER / DEVELOPER API ACCESS

### What Works Now
- Admin creates partner via `POST /v1/admin/partners/` (admin JWT required)
- Admin generates API key via `POST /v1/admin/partners/{id}/keys`
- Partner authenticates with `X-Partner-Key` header
- Partner submits charging sessions, gets incentive evaluations
- Rate limits enforced per partner (`rate_limit_rpm`)
- Trust tiers affect quality score

### What's Missing (Significant)

| Gap | Impact | Who It Blocks |
|-----|--------|---------------|
| **No self-service signup** | Every partner needs admin intervention | Developers, utilities, fleet platforms |
| **No developer portal / docs** | Partners can't integrate without hand-holding | All API consumers |
| **No API key self-service** | Can't generate, rotate, or revoke keys | All partners |
| **No usage dashboard** | Partners can't see their API usage or limits | All partners |
| **No partner billing** | Free unlimited access (no revenue model) | Revenue from API access |
| **No sandbox environment** | Partners test against production | Developers |
| **No webhook management** | Partners can't configure callback URLs via UI | Partners needing real-time updates |
| **No data licensing subscription** | No recurring payment for data/API access | Utilities, fleet platforms |

### To Unblock Partners Today (Manual)

1. **Create a partner via admin API:**
```bash
curl -X POST https://api.nerava.network/v1/admin/partners/ \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Partner Name",
    "slug": "partner-slug",
    "partner_type": "charging_network",
    "trust_tier": 2,
    "contact_email": "partner@example.com",
    "rate_limit_rpm": 60
  }'
```

2. **Generate an API key:**
```bash
curl -X POST https://api.nerava.network/v1/admin/partners/PARTNER_ID/keys \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Production Key", "scopes": ["sessions:write","sessions:read","grants:read","campaigns:read"]}'
```
**Save the key from the response — it's shown only once.**

3. **Share API docs manually** — the endpoints are documented in `CLAUDE.md` under "Partner Incentive API"

### Future: Data Licensing & Charging Session Verification API

For utilities and fleet platforms that want ongoing API access, you need:

1. **Create Stripe Product:** "Nerava API Access" with tiered pricing:
   - **Starter:** $99/mo — 1,000 sessions/mo, basic data
   - **Growth:** $499/mo — 10,000 sessions/mo, enriched data
   - **Enterprise:** Custom — unlimited, dedicated support

2. **Build partner subscription flow:**
   - Partner signs up → creates Stripe Customer → subscribes to tier
   - Webhook creates/updates `PartnerSubscription` record
   - Rate limits tied to subscription tier (not just hardcoded)

3. **Build developer portal** (separate app or section of landing page):
   - API key management
   - Usage analytics
   - Interactive API docs (Swagger/OpenAPI)
   - Sandbox environment toggle

---

## 9. APP RUNNER ENVIRONMENT VARIABLES

**Update via AWS Console** (safer than CLI — CLI can wipe existing vars):

AWS Console → App Runner → `nerava-backend` → Configuration → Environment Variables → Edit

Add/verify ALL of these:

### Payment & Billing
```
STRIPE_SECRET_KEY=sk_live_XXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXX
ENABLE_STRIPE_PAYOUTS=true
MINIMUM_WITHDRAWAL_CENTS=2000
WEEKLY_WITHDRAWAL_LIMIT_CENTS=100000
STRIPE_PRICE_PRO_MONTHLY=price_XXXXXXXX
STRIPE_PRICE_ADS_FLAT_MONTHLY=price_XXXXXXXX
```

### Push Notifications
```
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...full JSON...}
APNS_KEY_ID=XXXXXXXXXX
APNS_TEAM_ID=XXXXXXXXXX
APNS_KEY_CONTENT=-----BEGIN PRIVATE KEY-----\n...key...\n-----END PRIVATE KEY-----
APNS_BUNDLE_ID=com.nerava.driver
APNS_USE_SANDBOX=false
```

### Auth
```
JWT_SECRET=<already set>
GOOGLE_CLIENT_ID=<for Google Sign-In>
APPLE_CLIENT_ID=<for Apple Sign-In>
TESLA_CLIENT_ID=<for Tesla OAuth>
TESLA_CLIENT_SECRET=<for Tesla OAuth>
```

### Already Set (verify these exist)
```
DATABASE_URL=<RDS connection string>
ENV=prod
SENTRY_DSN=<if using Sentry>
FRONTEND_URL=https://app.nerava.network
PUBLIC_BASE_URL=https://api.nerava.network
DRIVER_APP_URL=https://app.nerava.network
```

---

## 10. AUTH & ACCOUNT READINESS MATRIX

| User Type | Can Sign Up? | How? | Can Add Card? | Can Subscribe? | Gaps |
|-----------|-------------|------|---------------|----------------|------|
| **Driver** | YES | Phone OTP, Apple, Google | YES (Stripe Express) | N/A | None |
| **Merchant** | YES | Google Business OAuth → `/claim` | YES (Stripe SetupIntent) | YES (Pro/Ads plans) | No billing portal, no card management UI |
| **Sponsor** | PARTIAL | Email OTP (auto-creates account) | At checkout only | N/A (prepaid campaigns) | No saved payment methods, no self-serve signup landing page |
| **Admin** | NO (by design) | Email/password (provisioned manually) | N/A | N/A | None — this is correct |
| **API Partner** | NO | Admin creates manually via API | NO | NO | No self-serve, no billing, no portal |
| **Utility** | NO | Would use Partner API | NO | NO | No flow exists |
| **Developer** | NO | Would use Partner API | NO | NO | No portal, no docs site, no sandbox |

---

## 11. REVENUE READINESS MATRIX

| Revenue Stream | Implemented? | Can Accept Payment? | Can Bill Recurring? | Gaps |
|---------------|-------------|--------------------|--------------------|------|
| **Campaign Funding** (sponsors) | YES | YES (Stripe Checkout) | NO (one-time only) | No auto-renew billing, no refunds |
| **Merchant Pro Sub** | YES | YES (Stripe Subscription) | YES | Need Stripe price IDs set |
| **Merchant Ads Sub** | YES | YES (Stripe Subscription) | YES | Need Stripe price IDs set |
| **Merchant Nova Purchase** | YES | YES (Stripe Checkout) | NO (one-time) | Working |
| **Driver Payouts** | YES | N/A (outbound) | N/A | Need Stripe balance funded |
| **Platform Fee** | YES | Auto-deducted (20% BPS) | YES | Working |
| **Partner API Billing** | NO | NO | NO | No billing model exists |
| **Data Licensing** | NO | NO | NO | No product, no flow |
| **In-Store POS (Square)** | PARTIAL | Backend exists | NO | No UI integration |

---

## 12. QUICK REFERENCE COMMANDS

### Android Build
```bash
cd mobile/nerava_android
./gradlew assembleDebug          # Debug APK
./gradlew bundleRelease          # Release AAB for Play Store
./gradlew test                   # Unit tests
adb install app/build/outputs/apk/debug/app-debug.apk  # Install on device
```

### Backend Deploy
```bash
# Build + push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 566287346479.dkr.ecr.us-east-1.amazonaws.com
docker build --platform linux/amd64 -t 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:TAG ./backend
docker push 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:TAG

# Update App Runner
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{"ImageRepository":{"ImageIdentifier":"566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:TAG","ImageConfiguration":{"Port":"8000"},"ImageRepositoryType":"ECR"},"AutoDeploymentsEnabled":false,"AuthenticationConfiguration":{"AccessRoleArn":"arn:aws:iam::566287346479:role/nerava-apprunner-ecr-access"}}' \
  --region us-east-1
```

### Frontend Deploy
```bash
# Driver app
cd apps/driver && VITE_API_BASE_URL=https://api.nerava.network VITE_ENV=prod npm run build
aws s3 sync dist/ s3://app.nerava.network/ --delete --region us-east-1
aws cloudfront create-invalidation --distribution-id E2UEQFQ3RSEEAR --paths "/*"

# Merchant portal
cd apps/merchant && VITE_API_BASE_URL=https://api.nerava.network VITE_PUBLIC_BASE=/merchant/ VITE_ENV=prod npm run build
aws s3 sync dist/ s3://merchant.nerava.network/ --delete --region us-east-1
aws cloudfront create-invalidation --distribution-id E2EYO3ZPM3S1S0 --paths "/*"

# Admin dashboard
cd apps/admin && VITE_API_BASE_URL=https://api.nerava.network VITE_ENV=prod npm run build
aws s3 sync dist/ s3://admin.nerava.network/ --delete --region us-east-1
aws cloudfront create-invalidation --distribution-id E1WZNEUSEZC1X0 --paths "/*"
```

### Verify Production
```bash
curl https://api.nerava.network/healthz
aws logs tail "/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application" --follow --region us-east-1
```

---

## PRIORITY ORDER FOR TODAY/TOMORROW

### Today (Critical Path — 2-3 hours)
1. **Stripe live mode activation** (Section 2A) — 15 min
2. **Create Stripe products + prices** (Section 2E) — 15 min
3. **Set up Stripe webhooks** (Section 2D) — 10 min
4. **Enable Stripe Connect** (Section 2F) — 10 min
5. **Fund Stripe balance** for driver payouts (Section 2B) — 5 min
6. **Firebase project + `google-services.json`** (Section 3A) — 10 min
7. **APNs key** (Section 3B) — 10 min
8. **Update App Runner env vars** (Section 9) — 15 min
9. **Test full payment flow** — Create campaign → fund → verify webhook → activate — 30 min

### Tomorrow (Launch Prep — 2-3 hours)
1. **Android app icons + splash screen** (Section 4B-C) — 30 min
2. **Release keystore** (Section 4D) — 10 min
3. **Play Store listing + submit** (Section 4E) — 30 min
4. **Test merchant subscription flow** — Sign up → subscribe → verify active — 15 min
5. **Test driver payout flow** — Earn incentive → withdraw → verify Stripe transfer — 15 min
6. **Create first partner account** if needed (Section 8) — 10 min
7. **iOS screenshot update** if desired (Section 5B) — 30 min
8. **Rotate Tesla private keys** from git (Section 5A) — 15 min
