# Production Auth Setup Guide

## Overview

This guide covers production setup for Twilio OTP and Google Business Profile SSO authentication.

## Twilio OTP Setup

### Option 1: Twilio Verify (Recommended)

Twilio Verify handles code generation, TTL, retries, and fraud tooling automatically.

1. **Create Twilio Verify Service**
   - Go to [Twilio Console](https://console.twilio.com/)
   - Navigate to Verify > Services
   - Create a new Verify Service
   - Copy the Service SID

2. **Configure Environment Variables**
   ```bash
   OTP_PROVIDER=twilio_verify
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_VERIFY_SERVICE_SID=VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. **Test in Production**
   - Ensure `ENV=prod` is set
   - Startup validation will fail if Twilio credentials are missing
   - Test with real phone numbers

### Option 2: Direct SMS (Fallback)

If you prefer direct SMS control:

1. **Get a Twilio Phone Number**
   - Purchase a phone number in Twilio Console
   - Copy the phone number (E.164 format)

2. **Configure Environment Variables**
   ```bash
   OTP_PROVIDER=twilio_sms
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   OTP_FROM_NUMBER=+14155551234
   ```

### Development/Staging

For development and staging, use stub provider:

```bash
OTP_PROVIDER=stub
OTP_DEV_ALLOWLIST=+14155551234,+14155555678  # Optional: restrict to specific phones
ENV=dev  # or staging
```

**Note:** Stub provider accepts code `000000` for allowlisted phones (or all phones if no allowlist).

## Google Business Profile SSO Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google Business Profile API"

### 2. Create OAuth 2.0 Credentials

1. Navigate to APIs & Services > Credentials
2. Click "Create Credentials" > "OAuth client ID"
3. Configure OAuth consent screen:
   - User Type: External (or Internal if using Google Workspace)
   - App name: Nerava
   - Scopes: Add `https://www.googleapis.com/auth/business.manage`
4. Create OAuth Client ID:
   - Application type: Web application
   - Authorized JavaScript origins:
     - `http://localhost:8001` (dev)
     - `https://staging.yourdomain.com` (staging)
     - `https://yourdomain.com` (prod)
   - Authorized redirect URIs:
     - `http://localhost:8001/merchant/auth/google/callback` (dev)
     - `https://staging.yourdomain.com/merchant/auth/google/callback` (staging)
     - `https://yourdomain.com/merchant/auth/google/callback` (prod)

### 3. Configure Environment Variables

```bash
GOOGLE_OAUTH_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret  # If using code exchange flow
GOOGLE_OAUTH_REDIRECT_URI=https://yourdomain.com/merchant/auth/google/callback
GOOGLE_GBP_REQUIRED=true  # Set to false to skip GBP access check (not recommended)
```

### 4. Test GBP Access

1. Sign in with a Google account that has access to a Google Business Profile
2. Verify that locations are returned
3. Check audit logs for `merchant_gbp_access_granted` events

## Common Issues

### "Invalid audience" Error

**Cause:** Frontend and backend are using different Client IDs

**Fix:**
- Ensure `GOOGLE_OAUTH_CLIENT_ID` matches the Client ID used in frontend
- Check that both use the exact same Client ID (no trailing spaces)

### "Redirect URI mismatch" Error

**Cause:** Redirect URI in request doesn't match configured redirect URIs

**Fix:**
- Add the exact redirect URI to Google Cloud Console
- Ensure protocol (http/https) and domain match exactly
- Check for trailing slashes

### Twilio Geo Permissions / Messaging Restrictions

**Cause:** Twilio account has geo restrictions or messaging service restrictions

**Fix:**
- Check Twilio Console > Settings > Geo Permissions
- Ensure target countries are allowed
- Check Messaging Service settings if using one

### "OTP_PROVIDER=stub is not allowed in production"

**Cause:** Stub provider is enabled in production

**Fix:**
- Set `OTP_PROVIDER=twilio_verify` or `OTP_PROVIDER=twilio_sms`
- Ensure all required Twilio credentials are set

### "No GBP locations found"

**Cause:** User doesn't have access to any Google Business Profile locations

**Fix:**
- Ensure user has manager access to at least one GBP location
- Check that Google Business Profile API is enabled
- Verify OAuth scopes include `business.manage`

## Environment Variable Reference

### OTP Configuration
- `OTP_PROVIDER`: `twilio_verify` | `twilio_sms` | `stub`
- `TWILIO_ACCOUNT_SID`: Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Twilio Auth Token
- `TWILIO_VERIFY_SERVICE_SID`: Twilio Verify Service SID (required for `twilio_verify`)
- `OTP_FROM_NUMBER`: Twilio phone number (required for `twilio_sms`)
- `OTP_DEV_ALLOWLIST`: Comma-separated phone numbers for stub provider

### Google OAuth Configuration
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth Client ID
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth Client Secret (if using code exchange)
- `GOOGLE_OAUTH_REDIRECT_URI`: OAuth redirect URI
- `GOOGLE_GBP_REQUIRED`: `true` | `false` (default: `true`)

### General
- `ENV`: `dev` | `staging` | `prod`
- `ANALYTICS_ENABLED`: `true` | `false`
- `POSTHOG_KEY`: PostHog project API key
- `POSTHOG_HOST`: PostHog host (default: `https://app.posthog.com`)

## Testing Checklist

- [ ] OTP send works with real phone numbers
- [ ] OTP verify works with correct code
- [ ] Rate limiting triggers after 3 start requests
- [ ] Rate limiting triggers after 6 verify attempts
- [ ] Lockout works after too many failures
- [ ] Google SSO login works
- [ ] GBP access check works (if enabled)
- [ ] Tokens include role claims
- [ ] Role enforcement works on protected endpoints
- [ ] Audit logs are created
- [ ] PostHog events are sent







