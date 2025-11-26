# Domain Charge Party MVP - Implementation Summary

## ✅ Completed Components

### 1. Database Layer
- **Migration**: `alembic/versions/018_domain_charge_party_mvp.py`
  - Extends `users` table with `display_name`, `role_flags`, `auth_provider`, `oauth_sub`, `updated_at`
  - Creates `domain_merchants` table
  - Creates `driver_wallets` table
  - Creates `nova_transactions` table
  - Creates `domain_charging_sessions` table
  - Creates `stripe_payments` table

- **Models**: `app/models_domain.py`
  - `DomainMerchant` - Merchant entities
  - `DriverWallet` - Driver Nova balances
  - `NovaTransaction` - Transaction ledger
  - `DomainChargingSession` - Charging sessions
  - `StripePayment` - Stripe payment records

- **Extended User Model**: `app/models.py`
  - Added Domain Charge Party fields to existing `User` model

### 2. Services Layer

#### AuthService (`app/services/auth_service.py`)
- `register_user()` - Register with roles
- `authenticate_user()` - Email/password auth
- `create_session_token()` - JWT token generation
- `get_user_roles()` - Parse role flags
- `has_role()` - Role checking
- `get_user_merchant()` - Get merchant for merchant_admin

#### NovaService (`app/services/nova_service.py`)
- `grant_to_driver()` - Grant Nova to driver
- `redeem_from_driver()` - Redeem from driver to merchant (handles both sides)
- `grant_to_merchant()` - Grant Nova to merchant (Stripe purchases)
- `get_driver_wallet()` - Get/create driver wallet
- `get_driver_transactions()` - Driver transaction history
- `get_merchant_transactions()` - Merchant transaction history

#### StripeService (`app/services/stripe_service.py`)
- `create_checkout_session()` - Create Stripe Checkout session
- `handle_webhook()` - Process Stripe webhooks
- Supports Nova packages: `nova_100`, `nova_500`, `nova_1000`

### 3. Dependencies & Security

#### Role-Based Access (`app/dependencies_domain.py`)
- `get_current_user_id()` - Extract user ID from JWT/cookie
- `get_current_user()` - Get user object
- `require_role()` - Role-based dependency factory
- `require_driver` - Driver-only endpoint dependency
- `require_merchant_admin` - Merchant admin dependency
- `require_admin` - Admin-only dependency

### 4. API Routes

#### Auth Router (`app/routers/auth_domain.py`)
- `POST /auth/register` - Register user (driver/merchant_admin)
- `POST /auth/login` - Login with email/password
- `POST /auth/logout` - Logout (clear cookie)
- `GET /auth/me` - Get current user info + linked merchant

#### Driver Router (`app/routers/drivers_domain.py`)
- `POST /v1/drivers/events/charge_party/join` - Join charge party event
- `GET /v1/drivers/merchants/nearby` - Get nearby merchants
- `POST /v1/drivers/nova/redeem` - Redeem Nova at merchant
- `GET /v1/drivers/me/wallet` - Get driver wallet balance

#### Merchant Router (`app/routers/merchants_domain.py`)
- `POST /v1/merchants/register` - Register new merchant (creates user + merchant)
- `GET /v1/merchants/me` - Get merchant dashboard data
- `POST /v1/merchants/redeem_from_driver` - Merchant redeems from driver
- `GET /v1/merchants/transactions` - Merchant transaction history

## 🔧 Next Steps: Wiring Everything Together

### Step 1: Update Config (`app/core/config.py`)
Add Stripe and frontend URL config:
```python
class Settings(BaseModel):
    # ... existing fields ...
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
```

### Step 2: Register Routers (`app/main.py`)
Add the new routers to your FastAPI app:
```python
from app.routers import auth_domain, drivers_domain, merchants_domain

app.include_router(auth_domain.router)
app.include_router(drivers_domain.router)
app.include_router(merchants_domain.router)
```

### Step 3: Create Stripe Router (`app/routers/stripe_domain.py`)
Create Stripe checkout and webhook endpoints:
- `POST /v1/stripe/create_checkout_session`
- `POST /v1/stripe/webhook`

### Step 4: Create Admin Router (`app/routers/admin_domain.py`)
Create admin endpoints:
- `GET /admin/overview`
- `GET /admin/merchants`
- `POST /admin/nova/grant`

### Step 5: Run Migration
```bash
cd nerava-backend-v9
alembic upgrade head
```

### Step 6: Seed Demo Accounts
Create a seed script to create:
- `driver+demo@nerava.local` / password
- `merchant+demo@nerava.local` / password
- `admin+demo@nerava.local` / password

### Step 7: Environment Variables
Add to your `.env` or Railway config:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=https://your-frontend.com
```

## ✅ Additional Completed Components

### Stripe Router (`app/routers/stripe_domain.py`)
- `POST /v1/stripe/create_checkout_session` - Create Stripe Checkout session
- `POST /v1/stripe/webhook` - Handle Stripe webhook events
- `GET /v1/stripe/packages` - List available Nova packages

### Admin Router (`app/routers/admin_domain.py`)
- `GET /admin/overview` - Admin dashboard statistics
- `GET /admin/merchants` - List merchants with filters
- `POST /admin/nova/grant` - Manually grant Nova to driver/merchant

### Nova Grant Router (`app/routers/nova_domain.py`)
- `POST /v1/nova/grant` - Admin-only endpoint to grant Nova after session verification

### Config Updates (`app/core/config.py`)
- Added `STRIPE_SECRET_KEY` config
- Added `STRIPE_WEBHOOK_SECRET` config
- Added `FRONTEND_URL` config

## 📋 Still TODO

1. **Wire Routers** - Add Domain Charge Party routers to `main.py`
2. **Run Migration** - Execute Alembic migration
3. **Frontend Screens** - Auth, driver wallet, merchant dashboard
4. **Seed Script** - Demo accounts (driver+demo, merchant+demo, admin+demo)
5. **Tests** - Core flow tests

## 🎯 Key Design Decisions

1. **Separate Models**: Domain Charge Party models are separate from "While You Charge" models to avoid conflicts
2. **Role Flags**: Simple comma-separated string for roles (can be upgraded to JSON later)
3. **Domain Zone**: Hardcoded to "domain_austin" for MVP, easily extensible
4. **Nova Units**: Integer values (e.g., 1000 = 1000 Nova), can represent cents or points
5. **Transaction Types**: Clear enum-like strings for auditability
6. **Idempotency**: Stripe webhooks use `stripe_event_id` for idempotency

## 📝 Notes

- All endpoints use existing JWT token auth pattern
- NovaService handles all balance updates transactionally
- Stripe integration supports test mode
- Domain radius validation: 1000m from Domain center (configurable)
- Merchant registration auto-activates (status="active") for MVP

