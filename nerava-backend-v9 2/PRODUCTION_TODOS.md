# Production TODOs

This document tracks production readiness items for the merchant onboarding system.

## Token Storage

**Status**: TODO

**Description**: Implement secure token encryption for Google Business Profile OAuth tokens.

**Current State**: Tokens are stored in-memory (OAuth state) or not persisted (access tokens).

**Required Changes**:
1. Create `MerchantOAuthToken` model to store encrypted tokens
2. Use existing `TOKEN_ENCRYPTION_KEY` pattern (same as Square tokens)
3. Encrypt `access_token` and `refresh_token` before storing
4. Implement token refresh logic

**Files to Modify**:
- `app/models/merchant_account.py` - Add MerchantOAuthToken model
- `app/services/merchant_onboarding_service.py` - Store encrypted tokens
- Create Alembic migration for new table

## Stripe Webhooks

**Status**: TODO

**Description**: Implement webhook handler for SetupIntent confirmation to update MerchantPaymentMethod status.

**Current State**: SetupIntent is created but payment method status is not updated automatically.

**Required Changes**:
1. Create webhook endpoint `/v1/webhooks/stripe`
2. Verify webhook signature using `STRIPE_WEBHOOK_SECRET`
3. Handle `setup_intent.succeeded` event
4. Update `MerchantPaymentMethod.status` to "ACTIVE"
5. Store `stripe_payment_method_id` from SetupIntent

**Files to Create/Modify**:
- `app/routers/stripe_webhooks.py` - New webhook handler
- `app/services/merchant_onboarding_service.py` - Update payment method status
- Register webhook endpoint in `main_simple.py`

## Merchant Billing

**Status**: Future

**Description**: Implement actual charging functionality (currently only card-on-file collection).

**Current State**: Only SetupIntent for card-on-file collection is implemented. No actual charges are made.

**Required Changes**:
1. Implement daily cap tracking
2. Create charge endpoint using stored payment method
3. Track spending against `daily_cap_cents`
4. Implement billing cycle logic

**Files to Create/Modify**:
- `app/routers/merchant_billing.py` - New billing endpoints
- `app/services/merchant_billing_service.py` - Billing logic
- Update `MerchantPlacementRule` to track daily spending

## Google Business Profile API Integration

**Status**: Partial (Mock mode implemented)

**Description**: Complete real Google Business Profile API integration.

**Current State**: Mock mode (`MERCHANT_AUTH_MOCK=true`) returns seeded fake locations.

**Required Changes**:
1. Implement real Google Business Profile API calls
2. Handle OAuth token refresh
3. Map GBP locations to Google Places place_ids
4. Handle API rate limits and errors

**Files to Modify**:
- `app/services/google_business_profile.py` - Implement real API calls
- Add error handling and retry logic

## Security Hardening

**Status**: TODO

**Description**: Additional security measures for production.

**Required Changes**:
1. Rate limiting on merchant endpoints
2. CSRF protection for OAuth callbacks
3. Input validation for placement rules
4. Audit logging for placement rule changes

**Files to Modify**:
- `app/routers/merchant_onboarding.py` - Add rate limiting
- `app/middleware/ratelimit.py` - Configure limits
- Add audit log model for placement changes



