# Promotion to Canonical v1 API - Complete

## ✅ Completed Steps

### Step 1: Router Prefixes Promoted ✅

All Domain routers now use canonical `/v1/*` prefixes (removed `/domain/`):

- ✅ `auth_domain.py` → `/v1/auth` (tags: `auth-v1`)
- ✅ `drivers_domain.py` → `/v1/drivers`
- ✅ `merchants_domain.py` → `/v1/merchants` (tags: `merchants-v1`)
- ✅ `stripe_domain.py` → `/v1/stripe` (tags: `stripe-v1`)
- ✅ `admin_domain.py` → `/v1/admin` (tags: `admin-v1`)
- ✅ `nova_domain.py` → `/v1/nova`

**Note:** These coexist with legacy routes but use different tags. Endpoints don't conflict because they serve different purposes:
- Legacy `/auth` vs new `/v1/auth/*`
- Legacy `/v1/merchants/nearby` (Google Places) vs new `/v1/merchants/register` (Domain merchants)
- Legacy `/v1/admin/settle` vs new `/v1/admin/overview`
- Legacy `/v1` stripe_api (payouts) vs new `/v1/stripe/*` (checkout)

### Step 2: EnergyEvent/Zone Models Added ✅

- ✅ Added `Zone` model (`zones` table) - geographic zones
- ✅ Added `EnergyEvent` model (`energy_events` table) - charge party events
- ✅ Created migration `019_add_energy_events_zones.py`:
  - Creates `zones` table
  - Creates `energy_events` table
  - Seeds `domain_austin` zone
  - Seeds `domain_jan_2025` event
  - Updates `domain_merchants` to use `zone_slug` instead of `domain_zone`
  - Adds `event_id` FK to `domain_charging_sessions` and `nova_transactions`

- ✅ Updated `DomainMerchant` model to use `zone_slug` instead of `domain_zone`
- ✅ Added `event_id` FK to `DomainChargingSession` and `NovaTransaction` models

### Step 3: Endpoints Updated for Data-Scoping ✅

- ✅ `POST /v1/drivers/charge_events/{event_slug}/join`
  - Looks up event by `event_slug`
  - Creates session with `event_id` FK
  - New events configured via data (EnergyEvent rows), not code

- ✅ `GET /v1/drivers/merchants/nearby?zone_slug=...`
  - Uses `zone_slug` query parameter
  - Filters merchants by zone
  - New zones configured via data (Zone rows), not code

- ✅ `NovaService.grant_to_driver()` now accepts `event_id` parameter
- ✅ Nova transactions include `event_id` when available
- ✅ Updated merchant registration to use zone validation from Zone table

### Step 4: Pilot Routes Deprecation Plan ✅

Created `PILOT_DEPRECATION.md` documenting:
- All pilot endpoints currently used by frontend
- Mapping to new v1 endpoints (where applicable)
- Migration strategy (thin adapters → frontend update → removal)

**Note:** Pilot routes are not included in `main.py` (only in `main_simple.py`). They remain available but should be migrated to thin adapters or removed after frontend updates.

### Step 5: Documentation ✅

- ✅ Created `PROMOTION_TO_V1_STATUS.md` - status tracking
- ✅ Created `PILOT_DEPRECATION.md` - deprecation plan
- ✅ Updated `alembic/env.py` comment - models_domain now canonical v1

## 📋 Current API Structure

### Canonical v1 Endpoints (Data-Scoped)

```
/v1/auth/register
/v1/auth/login
/v1/auth/logout
/v1/auth/me

/v1/drivers/charge_events/{event_slug}/join
/v1/drivers/merchants/nearby?zone_slug=...
/v1/drivers/nova/redeem
/v1/drivers/me/wallet

/v1/merchants/register
/v1/merchants/me
/v1/merchants/redeem_from_driver
/v1/merchants/transactions

/v1/stripe/create_checkout_session
/v1/stripe/webhook
/v1/stripe/packages

/v1/admin/overview
/v1/admin/merchants
/v1/admin/nova/grant

/v1/nova/grant
```

### Key Design Decisions

1. **Data-Scoped Events**: New charge parties are configured via `EnergyEvent` and `Zone` rows, not new code
2. **Zone-Based Filtering**: Merchants filtered by `zone_slug` query parameter
3. **Event-Based Sessions**: Charging sessions linked to events via `event_id` FK
4. **Transaction Tracking**: Nova transactions optionally reference events via `event_id`

## 🚀 Next Steps

1. **Run Migration**: Execute `alembic upgrade head` to create EnergyEvent/Zone tables
2. **Frontend Migration**: Update PWA to use new `/v1/*` endpoints
3. **Pilot Adapters**: Create thin adapters for pilot routes or remove after frontend migration
4. **Testing**: Test charge party flow with data-scoped events

## 📝 Files Modified

- `app/routers/auth_domain.py` - changed prefix to `/v1/auth`
- `app/routers/drivers_domain.py` - changed prefix, updated to use event_slug/zone_slug
- `app/routers/merchants_domain.py` - changed prefix, updated to use zone_slug
- `app/routers/stripe_domain.py` - changed prefix to `/v1/stripe`
- `app/routers/admin_domain.py` - changed prefix, updated to use zone_slug
- `app/routers/nova_domain.py` - changed prefix, passes event_id
- `app/models_domain.py` - added Zone/EnergyEvent models, updated to use zone_slug
- `app/services/nova_service.py` - added event_id parameter
- `alembic/versions/019_add_energy_events_zones.py` - new migration
- `app/main.py` - updated comments
- `alembic/env.py` - updated comment

