# Financial Flow Test Coverage Documentation

This document describes the test coverage for high-risk financial flows in the Nerava platform.

## Overview

Financial flow tests ensure that Nova/wallet/redemption/payout logic cannot silently drift and maintain data integrity. These tests are **critical for production safety**.

## Test Files

- `tests/test_financial_flows.py` - Main financial flow tests
- `tests/helpers/financial_helpers.py` - Test helper utilities

## Test Coverage

### Ledger Invariants

**Test**: `TestLedgerInvariants.test_double_entry_sums_to_zero_per_transaction_group`

Verifies that for each transaction group (grant/redemption), debits == credits (double-entry accounting).

**Coverage**:
- Nova grants create correct transaction records
- Nova redemptions create correct transaction records
- Balance updates match transaction amounts

### Balance Integrity

**Tests**:
- `TestBalanceIntegrity.test_balance_after_credits_debits_equals_expected`
- `TestBalanceIntegrity.test_balance_after_redemptions`
- `TestBalanceIntegrity.test_no_negative_balances_allowed`

Verifies that:
- Balance after N credits/debits equals expected sum
- Balance matches ledger sum (no drift)
- Negative balances are prevented

**Coverage**:
- Multiple grants accumulate correctly
- Multiple redemptions deduct correctly
- Balance always matches sum of transactions
- Negative balance attempts are rejected

### Redemption Flow

**Tests**:
- `TestRedemptionFlow.test_redemption_creates_correct_ledger_entries`
- `TestRedemptionFlow.test_redemption_idempotency`
- `TestRedemptionFlow.test_redemption_insufficient_funds`
- `TestRedemptionFlow.test_redemption_invalid_merchant`

Verifies that:
- Redemption creates correct ledger entries
- Idempotency keys prevent duplicate redemptions
- Insufficient funds are rejected
- Invalid merchants are rejected

**Coverage**:
- Transaction creation
- Balance updates
- Idempotency handling
- Error cases

### Payout Flow

**Tests**:
- `TestPayoutFlow.test_payout_flow_exists`
- `TestPayoutFlow.test_payout_no_duplicate_stripe_session`

Verifies that:
- Payout models exist and can be used
- Duplicate Stripe session IDs are prevented
- Status transitions are validated

**Coverage**:
- StripePayment model
- Unique constraints
- Status transitions

### Failure Modes

**Tests**:
- `TestFinancialFlowFailureModes.test_insufficient_funds_error`
- `TestFinancialFlowFailureModes.test_duplicate_idempotency_key`
- `TestFinancialFlowFailureModes.test_invalid_state_transition`

Verifies that:
- Insufficient funds return clear errors
- Duplicate idempotency keys return cached results
- Invalid state transitions are prevented

## Running Tests

```bash
# Run all financial flow tests
pytest tests/test_financial_flows.py -v

# Run specific test class
pytest tests/test_financial_flows.py::TestBalanceIntegrity -v

# Run with coverage
pytest tests/test_financial_flows.py --cov=app.services.nova_service --cov-report=term-missing
```

## Test Helpers

The `tests/helpers/financial_helpers.py` module provides:

- `create_test_user_with_wallet()` - Create user + wallet
- `create_test_merchant()` - Create merchant
- `post_nova_grant()` - Grant Nova helper
- `post_redemption()` - Redeem Nova helper
- `verify_ledger_balance()` - Verify balance matches ledger
- `get_wallet_balance()` - Get wallet balance

## Coverage Goals

- **Happy path**: All financial operations work correctly
- **Error cases**: Insufficient funds, invalid merchants, duplicate requests
- **Edge cases**: Zero amounts, maximum amounts, concurrent operations
- **Data integrity**: Balance always matches ledger sum

## Future Enhancements

Potential additional tests:
- Payout flow end-to-end (Stripe webhook → payout creation)
- Merchant balance reconciliation
- Transaction rollback scenarios
- Multi-currency support (if added)
- Fee calculation accuracy







