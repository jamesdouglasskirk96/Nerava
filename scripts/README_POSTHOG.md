# PostHog Analytics Configuration

This document describes how to configure PostHog analytics for the Nerava backend and frontend.

## Backend Configuration

### Environment Variables

The backend uses the following environment variables for PostHog:

- `POSTHOG_API_KEY` - Your PostHog project API key (required)
- `POSTHOG_HOST` - PostHog host URL (defaults to `https://app.posthog.com`)
- `ANALYTICS_ENABLED` - Enable/disable analytics (defaults to `true`)

### Current PostHog API Key

```
phc_2v2xkQw2xNPPsvGnE4YVuHe0KnQb1czy8M5Bep5GBNO
```

### Updating App Runner Service

To update the App Runner service with PostHog API key:

```bash
export POSTHOG_API_KEY="phc_2v2xkQw2xNPPsvGnE4YVuHe0KnQb1czy8M5Bep5GBNO"
export POSTHOG_HOST="https://app.posthog.com"
export ANALYTICS_ENABLED="true"
export SERVICE_NAME="nerava-backend"

./scripts/update_posthog.sh
```

Or use the deployment script which now includes PostHog configuration:

```bash
export POSTHOG_API_KEY="phc_2v2xkQw2xNPPsvGnE4YVuHe0KnQb1czy8M5Bep5GBNO"
export POSTHOG_HOST="https://app.posthog.com"
export ANALYTICS_ENABLED="true"

./scripts/deploy_api_apprunner.sh
```

## Frontend Configuration

### Environment Variables

The frontend uses the following environment variables (set at build time):

- `VITE_POSTHOG_KEY` - Your PostHog project API key (required)
- `VITE_POSTHOG_HOST` - PostHog host URL (defaults to `https://app.posthog.com`)

### Building with PostHog

When deploying the frontend, set the PostHog key before building:

```bash
export VITE_POSTHOG_KEY="phc_2v2xkQw2xNPPsvGnE4YVuHe0KnQb1czy8M5Bep5GBNO"
export VITE_POSTHOG_HOST="https://app.posthog.com"

./scripts/deploy_static_sites.sh
```

Or set it in the deployment script:

```bash
export VITE_POSTHOG_KEY="phc_2v2xkQw2xNPPsvGnE4YVuHe0KnQb1czy8M5Bep5GBNO"
export VITE_POSTHOG_HOST="https://app.posthog.com"
export API_BASE_URL="https://api.nerava.network"

./scripts/deploy_static_sites.sh
```

## PostHog Dashboard

Access your PostHog dashboard at:
https://app.posthog.com/

## Configuration Files

- Backend PostHog initialization: `nerava-backend-v9 2/app/integrations/posthog.py`
- Frontend PostHog initialization: `nerava-app-driver/src/lib/analytics.ts`
- Backend config: `nerava-backend-v9 2/app/core/config.py`

## Features

### Backend
- Server-side event tracking
- User identification
- Custom event properties
- Fails silently if PostHog is unavailable (won't break requests)

### Frontend
- Client-side event tracking
- Page view tracking
- User identification
- Privacy settings (masking enabled)

## Events Tracked

### Backend Events
- `otp_verified` - OTP verification success
- `otp_started` - OTP request initiated
- `merchant_details_viewed` - Merchant details page viewed
- `exclusive_activated` - Exclusive session activated
- `qr_scanned` - QR code scanned
- `visit_verified` - Visit verified
- `merchant_portal_page_viewed` - Merchant portal page viewed

### Frontend Events
- `APP_OPENED` - App opened
- Page views (automatic)
- Custom events (via `track()` function)

## Testing PostHog

### 1. Check Configuration

Verify that PostHog is configured correctly:

```bash
curl https://api.nerava.network/v1/health
```

Check the logs to see if PostHog is initialized.

### 2. Trigger Events

Trigger events through normal app usage:
- Login/authentication
- View merchant details
- Activate exclusive sessions
- Scan QR codes

### 3. Check PostHog Dashboard

Monitor events in the PostHog dashboard:
- Go to: https://app.posthog.com/events
- Filter by your project
- Check live events stream

## Troubleshooting

### Events Not Appearing

1. Check that `ANALYTICS_ENABLED=true` is set (backend)
2. Verify `POSTHOG_API_KEY` is correct
3. Check PostHog dashboard for API key validity
4. Check CloudWatch logs for PostHog errors
5. Verify network connectivity to PostHog host

### Frontend Not Tracking

1. Check that `VITE_POSTHOG_KEY` is set at build time
2. Verify PostHog is initialized in browser console
3. Check browser network tab for PostHog requests
4. Verify no ad blockers are blocking PostHog

## PostHog Dashboard

Access your PostHog dashboard at:
https://app.posthog.com/

Key sections:
- **Events**: View all tracked events
- **Live Events**: Real-time event stream
- **Insights**: Create charts and funnels
- **Persons**: View user profiles
- **Settings**: Configure project settings


