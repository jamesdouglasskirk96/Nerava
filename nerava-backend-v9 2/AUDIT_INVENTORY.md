# Domain Charge Party MVP - Audit Inventory

## Step 0: Repo Reconnaissance - Complete

### New/Modified Migration Files:
- ✅ `alembic/versions/018_domain_charge_party_mvp.py` - Creates domain_merchants, driver_wallets, nova_transactions, domain_charging_sessions, stripe_payments

### New/Modified Models:
- ✅ `app/models_domain.py` - NEW: DomainMerchant, DriverWallet, NovaTransaction, DomainChargingSession, StripePayment
- ⚠️ `app/models.py` - MODIFIED: User model extended with display_name, role_flags, auth_provider, oauth_sub, updated_at

### New Services:
- ✅ `app/services/auth_service.py` - NEW: AuthService for registration, authentication, role management
- ✅ `app/services/nova_service.py` - NEW: NovaService for Nova balance transactions
- ✅ `app/services/stripe_service.py` - NEW: StripeService for Stripe Checkout and webhooks

### New Dependencies:
- ✅ `app/dependencies_domain.py` - NEW: Role-based access control dependencies

### New Routers:
- ✅ `app/routers/auth_domain.py` - NEW: /auth/register, /auth/login, /auth/logout, /auth/me
- ✅ `app/routers/drivers_domain.py` - NEW: Driver endpoints
- ✅ `app/routers/merchants_domain.py` - NEW: Merchant endpoints
- ✅ `app/routers/stripe_domain.py` - NEW: Stripe endpoints
- ✅ `app/routers/admin_domain.py` - NEW: Admin endpoints
- ✅ `app/routers/nova_domain.py` - NEW: Nova grant endpoint

### Modified Core Files:
- ✅ `app/core/config.py` - MODIFIED: Added STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, FRONTEND_URL
- ✅ `app/main.py` - MODIFIED: Wired all new routers at bottom
- ✅ `alembic/env.py` - MODIFIED: Added import for models_domain

## Potential Issues Identified:

1. **Auth Router Conflict**: Both `auth.py` and `auth_domain.py` exist - need to check if they conflict on `/auth/*` paths
2. **User Model Extension**: Need to verify migration matches model extension
3. **Import Dependencies**: Need to verify all imports work correctly

## Next Steps:

- Step 1: Schema & Migration Sanity
- Step 2: Auth & Roles Unification
- Step 3: Nova Flows Verification
- Step 4: Stripe Integration Safety
- Step 5: Router Wiring Verification
- Step 6: End-to-End Test Script

