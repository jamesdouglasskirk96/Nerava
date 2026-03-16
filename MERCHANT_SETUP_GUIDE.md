# Merchant Portal Setup Guide

This document lists everything you need to configure for the merchant portal overhaul (Google OAuth, Pro Tier, Nerava Ads).

## 1. Google Cloud Console

1. Create project (or use existing Nerava project)
2. Enable APIs:
   - **My Business Account Management API**
   - **My Business Business Information API**
3. Create **OAuth 2.0 credentials** (Web application type):
   - Authorized redirect URIs:
     - `https://merchant.nerava.network/auth/google/callback`
     - `http://localhost:5174/auth/google/callback` (dev)
4. Set environment variables:
   ```
   GOOGLE_OAUTH_CLIENT_ID=<from Google Cloud>
   GOOGLE_OAUTH_CLIENT_SECRET=<from Google Cloud>
   GOOGLE_OAUTH_REDIRECT_URI=https://merchant.nerava.network/auth/google/callback
   ```
5. **Google Business Profile API access** requires Google review for production usage.
   - During development: use `MERCHANT_AUTH_MOCK=true` to test with mock data
   - Apply at: https://developers.google.com/my-business/content/prereqs

## 2. Stripe Dashboard

Create 2 Products + Prices:

| Product | Price | Env Var |
|---------|-------|---------|
| **Pro Plan** | $200/mo recurring | `STRIPE_PRICE_PRO_MONTHLY` |
| **Nerava Ads Flat** | $99/mo recurring | `STRIPE_PRICE_ADS_FLAT_MONTHLY` |

Create a webhook endpoint:
- URL: `https://api.nerava.network/v1/merchant/billing/webhook`
- Events to listen for:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`
- Get signing secret → set `STRIPE_MERCHANT_WEBHOOK_SECRET`

## 3. AWS SES (for weekly reports)

- Verify domain `nerava.network` in SES (already done if console email OTP works)
- Ensure `noreply@nerava.network` is a verified sender
- Set `EMAIL_SENDER=ses` in App Runner env

## 4. App Runner Environment Variables

Add these to the App Runner service configuration:

```
GOOGLE_OAUTH_CLIENT_ID=<from Google Cloud>
GOOGLE_OAUTH_CLIENT_SECRET=<from Google Cloud>
GOOGLE_OAUTH_REDIRECT_URI=https://merchant.nerava.network/auth/google/callback
STRIPE_PRICE_PRO_MONTHLY=price_xxx
STRIPE_PRICE_ADS_FLAT_MONTHLY=price_xxx
STRIPE_MERCHANT_WEBHOOK_SECRET=whsec_xxx
MERCHANT_PORTAL_URL=https://merchant.nerava.network
MERCHANT_AUTH_MOCK=false
```

## 5. Database Migration

```bash
cd backend && python -m alembic upgrade head  # runs 099-102
```

This creates:
- `merchant_oauth_tokens` — encrypted Google OAuth tokens
- `merchant_subscriptions` — Stripe subscription tracking
- `ad_impressions` — driver-side impression tracking
- Adds `description`, `website`, `hours_text`, `photo_url` columns to `domain_merchants`

## 6. Local Development

For local dev without real Google OAuth:
```bash
MERCHANT_AUTH_MOCK=true
```

This returns mock locations and mock tokens so you can test the full claim flow.

## 7. Verification Checklist

- [ ] Google OAuth: Visit `/claim`, click "Sign in with Google" → consent screen → callback → location selection → dashboard
- [ ] Profile editing: Go to Settings, update fields, verify saved
- [ ] Pro subscription: Click "Upgrade to Pro" on Billing → Stripe Checkout → verify Insights shows detail data
- [ ] Nerava Ads: Navigate to `/nerava-ads`, subscribe, verify impression stats
- [ ] Weekly report: Wait for Monday 8am CT or manually trigger worker
- [ ] Impression tracking: Open driver app, verify impressions recorded in `ad_impressions` table
