# Test Cleanup Documentation

**Date:** 2025-01-XX  
**Purpose:** Document removed dead tests and rationale

## Overview

This document tracks test files and test cases that have been removed because they reference non-existent functions or modules.

## Removed Test Files

### `app/tests/test_disaster_recovery.py`

**Status:** DELETED

**Reason:** All tests were skipped because the modules `app.scripts.db_backup` and `app.scripts.db_restore` do not exist. The entire test file was marked with `@pytest.mark.skip` and contained no functional tests.

**Action Taken:** File deleted. If disaster recovery functionality is implemented in the future, tests should be re-added.

### `app/tests/demo/test_demo_tour.py`

**Status:** DELETED

**Reason:** All tests were skipped because the `run_tour` function no longer exists in `app.routers.demo`. All 4 test functions were marked with `@pytest.mark.skip(reason="run_tour function no longer exists in demo router")`.

**Action Taken:** File deleted. If tour functionality is re-implemented, tests should be re-added.

## Modified Test Files

### `app/tests/demo/test_demo_state.py`

**Status:** MODIFIED - Removed dead tests

**Reason:** Two test functions (`test_get_state_empty` and `test_get_state_with_scenarios`) were skipped because the `get_state` function no longer exists in `app.routers.demo`.

**Action Taken:** Removed the two skipped test functions. The file still contains valid tests for `set_scenario` function.

**Removed Tests:**
- `test_get_state_empty` - Test for getting state when no scenarios are set
- `test_get_state_with_scenarios` - Test for getting state with existing scenarios

## Impact

- **Test Suite:** Removed ~15 skipped test cases that were cluttering test output
- **Coverage:** No impact on actual test coverage (tests were already skipped)
- **Maintenance:** Reduced maintenance burden by removing dead code

## Future Considerations

If any of the removed functionality is re-implemented:
1. Re-add corresponding test files/functions
2. Update this document to reflect restoration
3. Ensure tests are not skipped and actually run

## Related Files

- `app/tests/test_disaster_recovery.py` - DELETED
- `app/tests/demo/test_demo_tour.py` - DELETED
- `app/tests/demo/test_demo_state.py` - MODIFIED (removed 2 tests)










