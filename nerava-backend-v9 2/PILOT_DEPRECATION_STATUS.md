# Pilot Endpoint Deprecation Status

## Goal
Remove all `/v1/pilot/*` dependencies from the PWA frontend and backend hot path.

## Current Status

### ✅ Completed
- PWA now uses canonical `/v1/*` endpoints for:
  - Auth: `/v1/auth/*`
  - Drivers: `/v1/drivers/*`
  - Merchants: `/v1/merchants/*`
  - Nova: `/v1/nova/*`
  
### 🔄 In Progress
- Session ping/cancel endpoints created at `/v1/drivers/sessions/{id}/ping` and `/v1/drivers/sessions/{id}/cancel`
- PWA updated to use v1 endpoints for ping/cancel
- SessionService bridges DomainChargingSession with verify_dwell

### ⚠️ Known Issues
- SessionService currently bridges to old `sessions` table for verify_dwell
- TODO: Migrate verify_dwell to work directly with DomainChargingSession

### 🚫 Pilot Endpoints Still Active
The following pilot endpoints are still active in `app/routers/pilot.py`:
- `/v1/pilot/start_session` - DEPRECATED (use `/v1/drivers/charge_events/{event_slug}/join`)
- `/v1/pilot/verify_ping` - DEPRECATED (use `/v1/drivers/sessions/{id}/ping`)
- `/v1/pilot/session/cancel` - DEPRECATED (use `/v1/drivers/sessions/{id}/cancel`)
- `/v1/pilot/while_you_charge` - DEPRECATED (use `/v1/drivers/merchants/nearby`)
- `/v1/pilot/verify_visit` - May still be used for demo flow
- `/v1/pilot/activity` - DEPRECATED (use `/v1/drivers/activity` or wallet transactions)

## Next Steps
1. Verify PWA works with v1 endpoints only
2. Comment out pilot router inclusion in main.py
3. Delete pilot session endpoints after confirming v1 works

