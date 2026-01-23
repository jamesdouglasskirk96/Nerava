# Baseline Coverage Report
**Date:** 2025-01-XX  
**Phase:** Phase 0 - Baseline Reality Check

## Test Suite Status

- **Total Tests:** 609
- **Passed:** 277
- **Failed:** 264
- **Errors:** 65
- **Skipped:** 3
- **Status:** ❌ Test suite has failures and errors

## Current Coverage

- **Coverage:** 45%
- **Target:** 55%
- **Gap:** 10 percentage points needed

## Top 20 Uncovered Files by Statement Count

Based on coverage report analysis:

1. `app/services/verify_dwell.py` - 363 uncovered / 385 total (6% coverage)
2. `app/services/while_you_charge.py` - 197 uncovered / 430 total (54% coverage)
3. `app/services/nova_accrual.py` - 195 uncovered / 220 total (11% coverage)
4. `app/services/nova_service.py` - 180 uncovered / 220 total (18% coverage)
5. `app/services/merchant_service.py` - 175 uncovered / 200 total (13% coverage)
6. `app/services/rewards.py` - 91 uncovered / 103 total (12% coverage)
7. `app/services/purchases.py` - 90 uncovered / 135 total (33% coverage)
8. `app/services/stripe_service.py` - 105 uncovered / 129 total (19% coverage)
9. `app/services/smartcar_service.py` - 71 uncovered / 131 total (46% coverage)
10. `app/services/wallet.py` - 72 uncovered / 91 total (21% coverage)
11. `app/services/token_encryption.py` - 54 uncovered / 98 total (45% coverage)
12. `app/services/wallet_timeline.py` - 34 uncovered / 59 total (42% coverage)
13. `app/services/payouts_visa.py` - 34 uncovered / 53 total (36% coverage)
14. `app/services/square_orders.py` - 37 uncovered / 154 total (76% coverage)
15. `app/services/square_service.py` - 32 uncovered / 154 total (79% coverage)
16. `app/services/pool.py` - 29 uncovered / 42 total (31% coverage)
17. `app/services/rewards_engine.py` - 23 uncovered / 36 total (36% coverage)
18. `app/services/refresh_token_service.py` - 22 uncovered / 54 total (59% coverage)
19. `app/services/wallet_service.py` - 20 uncovered / 30 total (33% coverage)
20. `app/services/places_google.py` - 17 uncovered / 21 total (19% coverage)

## Test Failures Summary

### Import Errors
- Missing dependencies resolved: `freezegun`, `pytest-cov`, `coverage`
- Some tests have import path issues (need investigation)

### Flaky/Error-Prone Tests
- Many tests in `app/tests/` directory failing
- Integration tests requiring external services (need mocks)
- Database-related errors (AttributeError, SQLAlchemy issues)
- HTTP connection errors for live endpoint tests

### Categories of Failures
1. **Feature Flag Tests** - Multiple failures in `test_feature_flags.py`
2. **Observability Tests** - All tests failing in `test_observability.py`
3. **Rate Limiting Tests** - Multiple failures in `test_ratelimit.py`
4. **Security Tests** - Auth middleware and JWT tests failing
5. **Integration Tests** - External service dependencies causing errors
6. **Domain/Verification Tests** - Attribute errors and missing properties

## Prod Gate Status

- **Deployment Entrypoint:** ✅ Passed
- **TODO/FIXME Comments:** ⚠️ 194 found (warning)
- **Coverage Gate:** ❌ Below 55% threshold

## Next Steps

1. Fix test suite failures (Phase 2)
2. Make coverage honest (Phase 1)
3. Add high-impact tests to reach 55% (Phase 4)
4. Standardize error handling and env detection (Phases 5-6)










