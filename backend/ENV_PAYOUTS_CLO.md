# Stripe Payouts & Fidel CLO Environment Variables

## Stripe Express Payouts

```bash
# Enable/disable the feature
ENABLE_STRIPE_PAYOUTS=false  # Set to "true" for production

# Stripe keys (get from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_live_xxx  # Your Stripe secret key
STRIPE_PAYOUT_WEBHOOK_SECRET=whsec_xxx  # Webhook secret for payout events

# Business rules (optional, defaults shown)
MINIMUM_WITHDRAWAL_CENTS=2000  # $20 minimum withdrawal
WEEKLY_WITHDRAWAL_LIMIT_CENTS=100000  # $1000/week fraud cap
```

## Fidel CLO (Card Linked Offers)

```bash
# Enable/disable the feature
ENABLE_CLO=false  # Set to "true" for production

# Fidel API keys (get from Fidel Dashboard)
FIDEL_SECRET_KEY=sk_live_xxx
FIDEL_PROGRAM_ID=prg_xxx
FIDEL_WEBHOOK_SECRET=whsec_xxx
```

## API Endpoints

### Wallet Endpoints (`/v1/wallet/`)
- `GET /v1/wallet/balance` - Get driver balance
- `GET /v1/wallet/history` - Get payout history
- `POST /v1/wallet/withdraw` - Request withdrawal
- `POST /v1/wallet/stripe/account` - Create Stripe Express account
- `POST /v1/wallet/stripe/account-link` - Get onboarding link
- `POST /v1/wallet/stripe/webhook` - Stripe webhook handler

### CLO Endpoints (`/v1/clo/`)
- `GET /v1/clo/cards` - Get linked cards
- `POST /v1/clo/cards/link` - Link a card
- `DELETE /v1/clo/cards/{card_id}` - Unlink a card
- `GET /v1/clo/cards/session` - Get Fidel enrollment session
- `GET /v1/clo/transactions` - Get transaction history
- `POST /v1/clo/verify` - Manually verify transaction (testing)
- `POST /v1/clo/fidel/webhook` - Fidel webhook handler

## Database Migration

Run migration 073 to create required tables:
```bash
cd backend
alembic upgrade head
```

## Mock Mode

When API keys are not set or feature flags are `false`:
- Payouts are auto-marked as "paid"
- Cards are enrolled with mock IDs
- Transactions are auto-eligible if they meet spend requirements

This allows full testing without real integrations.
