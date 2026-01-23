# Test Decisions and Exclusions

This document tracks decisions about test exclusions, skips, and rationale for test infrastructure choices.

## Test Exclusions

None currently. All tests should pass.

## Test Infrastructure Decisions

### DB Session Management
- All tests use the `db` fixture from `tests/conftest.py` which provides transaction rollback isolation
- FastAPI dependency override uses `app.dependencies.get_db` (not `app.db.get_db`)
- Tests should NOT directly patch `SessionLocal` - use dependency overrides instead

## Failure Clusters Identified

### Cluster 1: DB Session/Object Deletion Issues
- **Root Cause**: SQLAlchemy objects being accessed after session rollback or deletion
- **Examples**: `ObjectDeletedError: Instance has been deleted, or its row is otherwise not present`
- **Fix**: Ensure proper session management and avoid accessing expired objects

### Cluster 2: Import Path Mismatches
- **Root Cause**: Tests importing from wrong modules (e.g., `app.main_simple` vs `app.core.startup_validation`)
- **Examples**: `test_config_validation.py` importing `validate_cors_origins` from wrong location
- **Fix**: Update imports to match actual module locations

### Cluster 3: Missing Test Data/Constraints
- **Root Cause**: Tests creating records without required fields
- **Examples**: `NOT NULL constraint failed: merchant_perks.title`
- **Fix**: Ensure test fixtures provide all required fields

### Cluster 4: Fixture Scope Mismatches
- **Root Cause**: Fixtures with incompatible scopes (session vs function vs module)
- **Examples**: `test_demo_runner.py` health_check fixture scope issues
- **Fix**: Align fixture scopes with test requirements

### Cluster 5: External Service Dependencies
- **Root Cause**: Tests requiring real external services (Redis, external APIs)
- **Examples**: Rate limiting tests, chaos tests, security tests
- **Fix**: Mock external dependencies at client boundary










