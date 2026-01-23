# HubSpot CRM Configuration

This document describes how to configure HubSpot CRM integration for the Nerava backend.

## Configuration

### Environment Variables

The backend uses the following environment variables for HubSpot:

- `HUBSPOT_PRIVATE_APP_TOKEN` - Your HubSpot private app access token (required)
- `HUBSPOT_PORTAL_ID` - Your HubSpot portal ID (required)
- `HUBSPOT_ENABLED` - Enable/disable HubSpot integration (defaults to `false`)
- `HUBSPOT_SEND_LIVE` - If `true`, sends live API calls. If `false`, dry-run mode (logs only)

### Current HubSpot Credentials

- **Private App Token**: `YOUR_HUBSPOT_PRIVATE_APP_TOKEN_HERE`
- **Portal ID**: `YOUR_HUBSPOT_PORTAL_ID_HERE`
- **Account**: Nerava

### Updating App Runner Service

To update the App Runner service with HubSpot credentials:

```bash
export HUBSPOT_PRIVATE_APP_TOKEN="YOUR_HUBSPOT_PRIVATE_APP_TOKEN_HERE"
export HUBSPOT_PORTAL_ID="YOUR_HUBSPOT_PORTAL_ID_HERE"
export HUBSPOT_ENABLED="true"
export HUBSPOT_SEND_LIVE="true"
export SERVICE_NAME="nerava-backend"

./scripts/update_hubspot.sh
```

Or use the deployment script which now includes HubSpot configuration:

```bash
export HUBSPOT_PRIVATE_APP_TOKEN="YOUR_HUBSPOT_PRIVATE_APP_TOKEN_HERE"
export HUBSPOT_PORTAL_ID="YOUR_HUBSPOT_PORTAL_ID_HERE"
export HUBSPOT_ENABLED="true"
export HUBSPOT_SEND_LIVE="true"

./scripts/deploy_api_apprunner.sh
```

## Modes

### Dry-Run Mode (Testing)

Set `HUBSPOT_SEND_LIVE=false` to enable dry-run mode:

```bash
export HUBSPOT_ENABLED="true"
export HUBSPOT_SEND_LIVE="false"
```

In dry-run mode:
- Events are logged but not sent to HubSpot
- Useful for testing without affecting HubSpot data
- No API calls are made

### Live Mode (Production)

Set `HUBSPOT_SEND_LIVE=true` to enable live API calls:

```bash
export HUBSPOT_ENABLED="true"
export HUBSPOT_SEND_LIVE="true"
export HUBSPOT_PRIVATE_APP_TOKEN="YOUR_HUBSPOT_PRIVATE_APP_TOKEN_HERE"
export HUBSPOT_PORTAL_ID="YOUR_HUBSPOT_PORTAL_ID_HERE"
```

In live mode:
- Events are sent to HubSpot API
- Contacts are created/updated in HubSpot
- Requires valid credentials

## HubSpot Integration Architecture

The integration uses an async outbox pattern:

```
User Action → Router → track_event() → outbox_events → Worker → HubSpot API
                                                              (with retry + rate limit)
```

- **Routers**: Enqueue events using `track_event(db, event_type, payload)`
- **Outbox**: Events stored in `outbox_events` table
- **Worker**: Background worker processes events asynchronously
- **HubSpot Client**: Sends events to HubSpot API with retry and rate limiting

## Event Types Tracked

The following lifecycle events are tracked:

- `driver_signed_up` - Driver registration
- `wallet_pass_installed` - Wallet pass installation
- `nova_earned` - Nova rewards earned
- `nova_redeemed` - Nova redemption
- `first_redemption_completed` - First redemption milestone
- `merchant_contact_created` - Merchant contact created
- `merchant_contact_updated` - Merchant contact updated

## Configuration Files

- HubSpot client: `nerava-backend-v9 2/app/integrations/hubspot.py`
- HubSpot sync worker: `nerava-backend-v9 2/app/workers/hubspot_sync.py`
- Backend config: `nerava-backend-v9 2/app/core/config.py`

## Features

- **Contact Management**: Create and update HubSpot contacts
- **Event Tracking**: Track lifecycle events in HubSpot
- **Async Processing**: Background worker processes events asynchronously
- **Retry Logic**: Automatic retry on failures
- **Rate Limiting**: Respects HubSpot API rate limits
- **Dry-Run Mode**: Test without sending live data

## Testing HubSpot

### 1. Check Configuration

Verify that HubSpot is configured correctly:

```bash
curl https://api.nerava.network/v1/health
```

Check the logs to see if HubSpot is initialized.

### 2. Trigger Events

Trigger events through normal app usage:
- Driver signup
- Wallet pass installation
- Nova earnings/redemptions
- Merchant contact creation

### 3. Check HubSpot Dashboard

Monitor contacts and events in HubSpot:
- Go to: https://app.hubspot.com/contacts/244844040
- Check contacts list
- View contact activity timeline

## Troubleshooting

### Events Not Appearing in HubSpot

1. Check that `HUBSPOT_ENABLED=true` is set
2. Verify `HUBSPOT_SEND_LIVE=true` for live mode
3. Check `HUBSPOT_PRIVATE_APP_TOKEN` is correct
4. Verify `HUBSPOT_PORTAL_ID` matches your HubSpot account
5. Check CloudWatch logs for HubSpot errors
6. Verify HubSpot sync worker is running

### HubSpot API Errors

1. Check HubSpot API rate limits
2. Verify private app token has correct permissions
3. Check HubSpot dashboard for API errors
4. Review CloudWatch logs for detailed error messages

### Worker Not Processing Events

1. Check that HubSpot sync worker started successfully
2. Verify outbox_events table has unprocessed events
3. Check CloudWatch logs for worker errors
4. Ensure database connection is working

## HubSpot Dashboard

Access your HubSpot dashboard at:
https://app.hubspot.com/

Key sections:
- **Contacts**: View and manage contacts
- **Deals**: Track deals and opportunities
- **Activities**: View contact activity timeline
- **Settings**: Configure integrations and API access

## Private App Permissions

Ensure your HubSpot private app has the following permissions:
- **Contacts**: Read and write access
- **Timeline Events**: Create events
- **CRM**: Read access (for contact lookups)

## Validation

The backend validates HubSpot configuration on startup:
- If `HUBSPOT_SEND_LIVE=true`, both `HUBSPOT_PRIVATE_APP_TOKEN` and `HUBSPOT_PORTAL_ID` must be set
- If validation fails, the application will fail to start with a clear error message


