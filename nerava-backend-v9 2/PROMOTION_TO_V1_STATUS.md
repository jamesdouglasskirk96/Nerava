# Promotion to Canonical v1 API - Status

## ✅ Step 1: Router Prefixes Promoted

All Domain routers now use canonical `/v1/*` prefixes (removed `/domain/`):

- ✅ `auth_domain.py` → `/v1/auth` (conflicts with existing `/auth` - need to handle)
- ✅ `drivers_domain.py` → `/v1/drivers`
- ✅ `merchants_domain.py` → `/v1/merchants` (conflicts with existing `/v1/merchants` - need to handle)
- ✅ `stripe_domain.py` → `/v1/stripe` (conflicts with existing `/v1` stripe_api - need to handle)
- ✅ `admin_domain.py` → `/v1/admin` (conflicts with existing `/v1/admin` - need to handle)
- ✅ `nova_domain.py` → `/v1/nova`

## ⚠️ Conflicts Identified

1. `/v1/auth` vs `/auth` - legacy auth.py uses `/auth`, new uses `/v1/auth`
2. `/v1/merchants` - existing merchants.py has `/nearby`, new has `/register`, `/me`, etc. (may coexist)
3. `/v1/stripe` - existing stripe_api.py uses `/v1` prefix (Stripe Connect), new uses `/v1/stripe` (Checkout)
4. `/v1/admin` - existing admin.py uses `/v1/admin`, new uses same prefix

## ✅ Step 2: EnergyEvent/Zone Models Added

- ✅ Added `Zone` model (geographic zones)
- ✅ Added `EnergyEvent` model (charge party events)
- ✅ Added migration `019_add_energy_events_zones.py`
- ✅ Updated `DomainMerchant` to use `zone_slug` instead of `domain_zone`
- ✅ Added `event_id` FK to `DomainChargingSession` and `NovaTransaction`

## ✅ Step 3: Endpoints Updated for Data-Scoping

- ✅ `POST /v1/drivers/charge_events/{event_slug}/join` - uses event_slug from path
- ✅ `GET /v1/drivers/merchants/nearby?zone_slug=...` - uses zone_slug query param
- ✅ `NovaService.grant_to_driver()` now accepts `event_id` parameter

## 🔄 Step 4: Pilot Routes - TODO

Need to create thin adapters or mark as deprecated.

## 🔄 Step 5: Documentation - TODO

Need to create API documentation for canonical v1 endpoints.

