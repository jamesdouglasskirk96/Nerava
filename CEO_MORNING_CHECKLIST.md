# CEO Morning Checklist — Nerava Launch

Everything you need to do by hand across both apps. No code — just portal work, account setup, and configuration. Estimated 2-2.5 hours total.

---

## PHASE 1: Stripe (15 min) — Already mostly working

Campaign funding, Stripe Checkout, webhooks, and platform fee are all working (you charged $5 and saw it in Stripe). What's left:

- [ ] **Switch to live mode** (if still in test) — Dashboard top banner → "Activate payments" → business verification. If already live, skip this.
- [ ] **Get live API keys** (if switching modes) — Developers → API keys → copy `sk_live_...`
- [ ] **Enable Stripe Connect** — Connect → Settings → Enable Express accounts → Platform name: Nerava, URL: https://nerava.network. This is what lets drivers withdraw earnings. (~5 min)
- [ ] **Create Merchant Pro product** — Products → Add → "Nerava Merchant Pro", $49/month recurring → copy `price_...` ID (~3 min)
- [ ] **Create Merchant Ads product** — Products → Add → "Nerava Ads", $99/month recurring → copy `price_...` ID (~2 min)
- [ ] **Fund Stripe balance** (optional) — Balances → Add to balance → $500+ from bank. Only needed if you want driver withdrawals to work before campaign payments cover it.

Already working (no action needed):
- Webhook endpoint (`/v1/stripe/webhooks`) — already firing, confirmed campaign auto-activation
- Campaign checkout with 20% platform fee — tested and deployed
- Stripe Checkout flow — end to end working

---

## PHASE 2: Firebase (10 min) — Unlocks Android push notifications

- [ ] **Create Firebase project** — [console.firebase.google.com](https://console.firebase.google.com/) → Add project → "Nerava" → disable Analytics
- [ ] **Add Android app** — Package: `network.nerava.app` → download `google-services.json`
- [ ] **Place the file** — put `google-services.json` at `mobile/nerava_android/app/google-services.json`
- [ ] **Generate service account key** — Project Settings → Service Accounts → Generate new private key → save the JSON

---

## PHASE 3: Apple (15 min) — Unlocks iOS push + fixes Sign-In

- [ ] **Create APNs key** — [developer.apple.com](https://developer.apple.com/account/resources/authkeys/list) → Keys → Create → check "APNs" → download `.p8` file
- [ ] **Note the Key ID** (10 chars) and **Team ID** (from Membership page)
- [ ] **Add Sign in with Apple entitlement** — Xcode → Nerava target → Signing & Capabilities → + Sign in with Apple. Also enable in Apple Developer portal under App IDs.

---

## PHASE 4: App Runner Env Vars (15 min) — Activates everything in production

Go to: **AWS Console → App Runner → nerava-backend → Configuration → Environment Variables → Edit**

Add these new vars (don't delete existing ones):

| Variable | Value |
|----------|-------|
| `STRIPE_SECRET_KEY` | `sk_live_...` from Phase 1 |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` from Phase 1 |
| `ENABLE_STRIPE_PAYOUTS` | `true` |
| `STRIPE_PRICE_PRO_MONTHLY` | `price_...` from Phase 1 |
| `STRIPE_PRICE_ADS_FLAT_MONTHLY` | `price_...` from Phase 1 |
| `FIREBASE_CREDENTIALS_JSON` | Full JSON from Phase 2 service account key |
| `APNS_KEY_ID` | Key ID from Phase 3 |
| `APNS_TEAM_ID` | Team ID from Phase 3 |
| `APNS_KEY_CONTENT` | Contents of `.p8` file (with `\n` for newlines) |
| `APNS_BUNDLE_ID` | `com.nerava.driver` |
| `APNS_USE_SANDBOX` | `false` |

Save and deploy. Takes ~5 min to roll out.

---

## PHASE 5: Android Play Store (30 min) — Gets Android app live

### App Icons — DONE
All icon sizes generated from the iOS AppIcon and placed in `mobile/nerava_android/app/src/main/res/`. Adaptive icon XMLs updated. Splash screen logo added.

### Release Keystore (~5 min)
- [ ] Run: `keytool -genkey -v -keystore nerava-release.keystore -alias nerava -keyalg RSA -keysize 2048 -validity 10000 -storepass YOUR_PASSWORD -keypass YOUR_PASSWORD -dname "CN=Nerava, OU=Mobile, O=Nerava Network, L=Austin, ST=TX, C=US"`
- [ ] **BACK THIS UP IMMEDIATELY** — lose it = can never update the app
- [ ] Create `mobile/nerava_android/keystore.properties`:
  ```
  storeFile=/path/to/nerava-release.keystore
  storePassword=YOUR_PASSWORD
  keyAlias=nerava
  keyPassword=YOUR_PASSWORD
  ```
- [ ] Build release: `cd mobile/nerava_android && ./gradlew bundleRelease`

### Play Store Listing (~25 min)
- [ ] Create account at [play.google.com/console](https://play.google.com/console) — $25 one-time fee
- [ ] Create app → Category: "Auto & Vehicles"
- [ ] Copy-paste listing text below
- [ ] Upload 2+ phone screenshots (1080x1920) and feature graphic (1024x500)
- [ ] Privacy policy URL: `https://nerava.network/privacy`
- [ ] Data Safety: location (precise, always), phone number, device IDs, financial data, analytics — all for app functionality
- [ ] Content rating: IARC questionnaire → 18+ (financial transactions)
- [ ] Upload the signed AAB → submit for review (1-3 days)

### Pre-Written Play Store Copy

**App name:** Nerava

**Short description (80 chars):**
Earn cash rewards every time you charge your EV. Connect Tesla & start earning.

**Full description:**
Nerava transforms your EV charging sessions into earning opportunities.

Connect your Tesla account, charge at any supported charger, and automatically earn cash rewards funded by local sponsors and energy partners. No extra steps — just plug in and get paid.

How it works:
1. Sign in and connect your Tesla
2. Charge at any supported EV charger
3. Nerava automatically verifies your session
4. Earn cash rewards deposited to your wallet
5. Withdraw anytime to your bank account via Stripe

Features:
- Automatic charging session detection via Tesla Fleet API
- Cash rewards from sponsor campaigns (not just points)
- Interactive map with 50,000+ chargers across the US
- Real-time session tracking with energy and cost data
- Wallet with instant Stripe payouts
- Exclusive merchant deals while you charge
- Energy reputation system with Bronze to Platinum tiers

Nerava is the incentive layer for the EV charging ecosystem — connecting drivers, charger operators, sponsors, and local merchants.

---

## PHASE 6: Security Hardening (15 min)

- [ ] **Rotate Tesla private keys** — `infra/certs/` has keys that shouldn't be in git
  1. Store in AWS Secrets Manager: `aws secretsmanager create-secret --name "nerava/tesla-fleet-private-key" --secret-string "$(cat infra/certs/com.tesla.3p.public-key.pem)" --region us-east-1`
  2. Delete `infra/certs/` contents locally
  3. Add `infra/certs/` to `.gitignore`

---

## PHASE 7: Verify Everything Works (30 min)

### Campaign funding (sponsor flow)
- [ ] Go to `console.nerava.network` → log in → create a test campaign → click Fund
- [ ] Complete Stripe Checkout → verify campaign status changes to "active"
- [ ] Check Stripe dashboard: payment received, webhook fired

### Merchant subscription
- [ ] Go to `merchant.nerava.network/find` → claim a business → subscribe to Pro
- [ ] Complete Stripe Checkout → verify subscription active in Stripe dashboard

### Driver payout (test tomorrow at charger)
- [ ] Charge at Tesla Supercharger → verify session detected → verify incentive earned
- [ ] Open wallet → request withdrawal → verify Stripe transfer created

### Push notifications
- [ ] Open driver app on iOS → verify device token registered (check backend logs)
- [ ] Open driver app on Android → verify FCM token registered

---

## What's NOT Needed for Tomorrow

These are real gaps but won't block the EVject CEO call or the charger test:

| Item | Why it can wait |
|------|----------------|
| Data retention policy | Only matters at 100K+ drivers |
| Async push notifications | Only matters for campaign blasts to 100K+ |
| RDS connection pool | Only saturates at 25 App Runner instances |
| Bundle size optimization | Works fine, just slower on 3G |
| Service worker / offline | Nice-to-have UX improvement |
| Terraform cleanup | Infrastructure docs, not user-facing |
| Android/iOS CI pipelines | Manual builds work for now |
| Android deep link verification (`assetlinks.json`) | App still opens, just shows disambiguation dialog |
| Partner self-service portal | Manual partner creation via admin API works |
| Merchant billing portal | Merchants can subscribe; invoice history comes later |
| Native crash reporting (Sentry) | Web Sentry already catches most issues |

---

## Quick Reference

| Service | URL |
|---------|-----|
| Driver App | https://app.nerava.network |
| Merchant Portal | https://merchant.nerava.network |
| Sponsor Console | https://console.nerava.network |
| Admin Dashboard | https://admin.nerava.network |
| API Health | https://api.nerava.network/healthz |
| Stripe Dashboard | https://dashboard.stripe.com |
| Firebase Console | https://console.firebase.google.com |
| Apple Developer | https://developer.apple.com |
| Google Play Console | https://play.google.com/console |
| AWS App Runner | AWS Console → App Runner → nerava-backend |
