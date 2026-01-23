# Pilot Routes Deprecation Plan

## Current Pilot Routes (to be deprecated)

The following `/v1/pilot/*` endpoints are still used by the PWA frontend and will be replaced with thin adapters:

### Frontend Usage (from `ui-mobile/js/`)

1. **`/v1/pilot/app/bootstrap`** - Bootstrap endpoint
   - Used by: `api.js`
   - **Replacement**: TBD (may need to merge with new v1 bootstrap or keep as adapter)

2. **`/v1/pilot/while_you_charge`** - Get merchants/perks
   - Used by: `explore.js`
   - **Replacement**: `/v1/drivers/merchants/nearby?zone_slug=domain_austin`

3. **`/v1/pilot/merchant_offer`** - Merchant offer codes
   - Used by: `api.js`
   - **Replacement**: TBD (merchant offer codes may be separate from charge party flow)

4. **`/v1/pilot/start_session`** - Start charging session
   - Used by: `explore.js`
   - **Replacement**: `/v1/drivers/charge_events/{event_slug}/join`

5. **`/v1/pilot/verify_ping`** - Verify location during session
   - Used by: `earn.js`
   - **Replacement**: TBD (may need to keep as adapter or merge with v1 session ping)

6. **`/v1/pilot/verify_visit`** - Verify merchant visit
   - Used by: `earn.js`
   - **Replacement**: TBD (visit verification may be separate flow)

7. **`/v1/pilot/session/cancel`** - Cancel session
   - Used by: `earn.js`
   - **Replacement**: TBD (cancel endpoint needed in v1)

8. **`/v1/pilot/activity`** - Get activity feed
   - Used by: `activity.js`
   - **Replacement**: TBD (activity feed may be separate from charge party)

## Migration Strategy

### Phase 1: Create Thin Adapters (Current)
- Keep pilot routes as thin wrappers that call new v1 services
- Mark all pilot routes with `@deprecated` comments
- Log deprecation warnings

### Phase 2: Frontend Migration
- Update frontend to use new `/v1/*` endpoints
- Test thoroughly

### Phase 3: Remove Pilot Routes
- After frontend migration is complete
- Remove pilot routers from `main.py`
- Delete pilot router files

## Notes

- Pilot routes use hardcoded `user_id=123` which needs to be mapped to real users
- Pilot routes use fake/simulated wallets which should be replaced with real `driver_wallets`
- Some pilot endpoints may not have direct v1 equivalents yet

