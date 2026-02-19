# PostHog Geo Coordinates Integration

## Overview

Geo coordinates (latitude, longitude, and accuracy) are now automatically included in PostHog events when available. This enables location-based analytics, heatmaps, and geographic insights in PostHog.

## Frontend (Driver App)

### Automatic Geo Inclusion

The `capture()` function automatically includes geo coordinates from the browser's geolocation API:

```typescript
import { capture, DRIVER_EVENTS } from './analytics'

// Automatically includes lat/lng/accuracy_m if location permission granted
capture(DRIVER_EVENTS.MERCHANT_CLICKED, {
  merchant_id: 'asadas_grill',
  merchant_name: 'Asadas Grill'
})
```

### Manual Geo Override

You can explicitly provide coordinates to override auto-detection:

```typescript
// Provide your own coordinates
capture(DRIVER_EVENTS.MERCHANT_CLICKED, {
  merchant_id: 'asadas_grill',
  lat: 30.2672,
  lng: -97.7431,
  accuracy_m: 10
})
```

### Disable Auto Geo

To disable automatic geo inclusion for a specific event:

```typescript
capture(DRIVER_EVENTS.SOME_EVENT, { /* properties */ }, false)
```

### How It Works

1. When `capture()` is called with `includeGeo: true` (default):
   - Checks if `lat`/`lng` are already in properties
   - If not, requests location from `navigator.geolocation.getCurrentPosition()`
   - Uses cached location if available (< 1 minute old)
   - Silently fails if permission denied or unavailable
   - Includes `lat`, `lng`, and `accuracy_m` in event properties

2. Location is cached for 60 seconds to avoid excessive API calls

3. The function is non-blocking - it fires location request asynchronously and doesn't delay event capture

## Backend (API)

### Adding Geo to Events

The `analytics.capture()` method now accepts `lat`, `lng`, and `accuracy_m` parameters:

```python
from app.services.analytics import get_analytics_client

analytics = get_analytics_client()
analytics.capture(
    event="server.driver.intent.capture.success",
    distinct_id=user_id,
    lat=request.lat,
    lng=request.lng,
    accuracy_m=request.accuracy_m,
    # ... other parameters
)
```

### Example: Intent Capture

```python
# backend/app/routers/intent.py
analytics.capture(
    event="server.driver.intent.capture.success",
    distinct_id=distinct_id,
    request_id=request_id,
    user_id=current_user.public_id if current_user else None,
    lat=request.lat,  # ✅ Geo coordinates included
    lng=request.lng,
    accuracy_m=request.accuracy_m,
    properties={
        "merchant_count": len(merchants),
        "confidence_tier": confidence_tier,
    }
)
```

### Example: OTP Events

For OTP events, geo coordinates can be included if available from the request:

```python
# If request includes location data
analytics.capture(
    event="server.otp.verified",
    distinct_id=f"phone:{phone_hash}",
    lat=request.lat if hasattr(request, 'lat') else None,
    lng=request.lng if hasattr(request, 'lng') else None,
    # ... other parameters
)
```

## PostHog Dashboard

### Viewing Geo Data

1. **In Event Properties**: Geo coordinates appear as `lat`, `lng`, and `accuracy_m` properties
2. **Configure Columns**: Use "Configure columns" button to add `lat` and `lng` columns to the activity feed
3. **Map Visualization**: PostHog can visualize events on a map if geo coordinates are present
4. **Filtering**: Filter events by geographic region using property filters

### Example Query

In PostHog, you can filter events by location:

```
Event: server.driver.intent.capture.success
Properties:
  - lat: between 30.0 and 30.5
  - lng: between -98.0 and -97.0
```

## Privacy Considerations

1. **User Consent**: Browser geolocation requires user permission
2. **Accuracy**: Only includes accuracy when available (may be missing for some events)
3. **Optional**: Geo coordinates are optional - events work fine without them
4. **Backend**: Backend events only include geo when explicitly provided in the request

## Implementation Status

✅ **Frontend**: Auto-includes geo coordinates when available  
✅ **Backend**: Accepts lat/lng/accuracy_m parameters  
✅ **Intent Capture**: Includes geo in success/failure events  
✅ **OTP Events**: Can include geo if available in request  
⏳ **Exclusive Events**: Can be updated to include geo from session data  

## Future Enhancements

- [ ] Add geo to exclusive activation/completion events
- [ ] Add geo to merchant click events (already has location context)
- [ ] Add geo-based filtering in PostHog insights
- [ ] Create geographic heatmaps of user activity
