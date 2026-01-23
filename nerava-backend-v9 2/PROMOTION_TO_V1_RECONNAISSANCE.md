# Step 0: Reconnaissance - Current Router State

## Current Domain Routers (to be promoted to /v1/*)
- `auth_domain.py` → `/v1/domain/auth`
- `drivers_domain.py` → `/v1/domain/drivers`
- `merchants_domain.py` → `/v1/domain/merchants`
- `stripe_domain.py` → `/v1/domain/stripe`
- `admin_domain.py` → `/v1/domain/admin`
- `nova_domain.py` → `/v1/domain/nova`

## Existing /v1/* Routers (potential conflicts)
- `auth.py` → `/auth` (legacy, minimal)
- `merchants.py` → `/v1/merchants` (has `/nearby` endpoint)
- `stripe_api.py` → `/v1` prefix (Stripe Connect for payouts)
- `admin.py` → `/v1/admin`
- `wallet.py` → `/v1` prefix

## Pilot Routers (to be deprecated)
- `pilot.py` → `/v1/pilot`
- `pilot_redeem.py` → `/v1/pilot`
- `pilot_debug.py` → `/v1/pilot/debug`

## Frontend Pilot Endpoint Usage (from grep)
Need to check which pilot endpoints are actually called by the PWA.

