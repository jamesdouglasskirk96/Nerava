# HubSpot Integration

## Overview

The HubSpot integration syncs lifecycle events from Nerava to HubSpot CRM. It uses an async outbox pattern for reliable delivery with retry logic and rate limiting.

## Architecture

```
User Action → Router → track_event() → outbox_events → Worker → HubSpot API
                                                              (with retry + rate limit)
```

- **Routers**: Enqueue events using `track_event(db, event_type, payload)`
- **Outbox**: Events stored in `outbox_events` table
- **Worker**: Background worker processes events asynchronously
- **HubSpot Client**: Sends events to HubSpot API with retry and rate limiting

## Configuration

### Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `HUBSPOT_ENABLED` | `false` | No | Master enable/disable flag |
| `HUBSPOT_SEND_LIVE` | `false` | No | If `true`, sends live API calls. If `false`, dry-run mode (logs only) |
| `HUBSPOT_PRIVATE_APP_TOKEN` | (empty) | Yes (if live) | HubSpot private app access token |
| `HUBSPOT_PORTAL_ID` | (empty) | Yes (if live) | HubSpot portal ID |

### Setup

1. **Dry-Run Mode (Recommended for Testing)**
   ```bash
   HUBSPOT_ENABLED=true
   HUBSPOT_SEND_LIVE=false
   ```
   Events will be logged but not sent to HubSpot.

2. **Live Mode**
   ```bash
   HUBSPOT_ENABLED=true
   HUBSPOT_SEND_LIVE=true
   HUBSPOT_PRIVATE_APP_TOKEN=your_token_here
   HUBSPOT_PORTAL_ID=your_portal_id_here
   ```
   Events will be sent to HubSpot API.

## Event Types

The following lifecycle events are tracked:

- `driver_signed_up` - Driver registration
- `wallet_pass_installed` - Wallet pass installation
- `nova_earned` - Nova rewards earned
- `nova_redeemed` - Nova redemption
- `first_redemption_completed` - First redemption milestone

## Usage

### In Routers

```python
from app.services.hubspot import track_event

# Track a lifecycle event
track_event(db, "driver_signed_up", {
    "user_id": str(user.id),
    "email": user.email,
    "auth_provider": "otp",
    "created_at": datetime.utcnow().isoformat() + "Z",
})
```

### Worker

The worker runs automatically when the application starts (if `HUBSPOT_ENABLED=true`). It:
- Polls `outbox_events` table every 10 seconds
- Processes up to 50 events per batch
- Retries failed events up to 3 times
- Rate limits to 8 requests/second

## Testing

### Smoke Test

Run the end-to-end smoke test:

```bash
cd backend
python scripts/hubspot_smoke_test.py
```

The test will:
1. Create a test event in the outbox
2. Process it with the worker
3. Verify it was marked as processed

### Manual Testing

1. **Enable dry-run mode:**
   ```bash
   export HUBSPOT_ENABLED=true
   export HUBSPOT_SEND_LIVE=false
   ```

2. **Trigger an event** (e.g., user signup)

3. **Check logs** for `[DRY-RUN]` messages

4. **Check database:**
   ```sql
   SELECT * FROM outbox_events WHERE processed_at IS NOT NULL;
   ```

## Monitoring

### Check Worker Status

The worker logs its status:
- `HubSpot sync worker started` - Worker is running
- `HubSpot sync worker not started (HUBSPOT_ENABLED=false)` - Worker disabled

### Check Event Processing

```sql
-- Unprocessed events
SELECT COUNT(*) FROM outbox_events WHERE processed_at IS NULL;

-- Failed events
SELECT * FROM outbox_events WHERE attempt_count >= 3;

-- Recent processed events
SELECT * FROM outbox_events 
WHERE processed_at IS NOT NULL 
ORDER BY processed_at DESC 
LIMIT 10;
```

## Troubleshooting

### Events Not Processing

1. Check `HUBSPOT_ENABLED=true`
2. Check worker logs for errors
3. Verify database connection
4. Check for events with `attempt_count >= 3` (max retries exceeded)

### Rate Limiting

The worker automatically rate limits to 8 requests/second. If you see 429 errors:
- Worker will automatically retry with backoff
- Check HubSpot API limits in your account

### Dry-Run vs Live

- **Dry-run**: Events logged with `[DRY-RUN]` prefix, no API calls
- **Live**: Events sent to HubSpot API, check HubSpot dashboard for contacts

## Migration

Run the migration to add retry fields:

```bash
cd backend
alembic upgrade head
```

This adds `attempt_count` and `last_error` columns to `outbox_events` table.

## Safety

- **Fail-open**: HubSpot errors never crash requests
- **Safe defaults**: `HUBSPOT_ENABLED=false`, `HUBSPOT_SEND_LIVE=false`
- **Retry logic**: Automatic retry with exponential backoff
- **Rate limiting**: Prevents API limit violations



