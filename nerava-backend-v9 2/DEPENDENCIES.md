# Dependency Management

This project uses [pip-tools](https://github.com/jazzband/pip-tools) for deterministic dependency locking.

## Overview

- **`requirements.in`** - Direct production dependencies only (human-editable)
- **`requirements-dev.in`** - Development and test dependencies (human-editable)
- **`requirements.txt`** - Compiled production dependencies with pinned transitive versions (auto-generated)
- **`requirements-dev.txt`** - Compiled dev dependencies with pinned transitive versions (auto-generated)

## Installation

### Production

```bash
pip install -r requirements.txt
```

### Development

```bash
# Install all dependencies (production + dev/test)
pip install -r requirements-dev.txt

# OR use pip-sync for exact version matching
pip install pip-tools
pip-sync requirements-dev.txt
```

## Updating Dependencies

### Adding a New Production Dependency

1. Add the dependency to `requirements.in`:
   ```ini
   # Example: adding a new package
   new-package>=1.0.0
   ```

2. Regenerate `requirements.txt`:
   ```bash
   pip-compile requirements.in
   ```

3. Install the updated dependencies:
   ```bash
   pip-sync requirements.txt  # Production
   # OR
   pip-sync requirements-dev.txt  # Development (includes prod deps)
   ```

### Adding a New Development Dependency

1. Add the dependency to `requirements-dev.in`:
   ```ini
   # Example: adding a test utility
   pytest-mock>=3.0.0
   ```

2. Regenerate `requirements-dev.txt`:
   ```bash
   pip-compile requirements-dev.in
   ```

3. Install the updated dependencies:
   ```bash
   pip-sync requirements-dev.txt
   ```

### Updating Existing Dependencies

1. Edit the version constraint in `requirements.in` or `requirements-dev.in`
2. Regenerate the compiled file:
   ```bash
   pip-compile requirements.in
   pip-compile requirements-dev.in
   ```
3. Review the changes in the compiled file
4. Install updated dependencies:
   ```bash
   pip-sync requirements-dev.txt
   ```

## Important Notes

### httpx Version Constraint

`httpx` is pinned to `<0.27.0` in `requirements.in` for compatibility with Starlette's `TestClient`. Versions 0.27.0+ removed the `app` parameter from `httpx.Client`, which breaks `TestClient` initialization.

```ini
# requirements.in
httpx>=0.24.0,<0.27.0
```

This ensures compatibility with:
- Starlette 0.27.0
- FastAPI 0.103.2
- pytest test suite

### Production vs Development

- **Production** (`requirements.txt`): Only runtime dependencies needed to run the application
- **Development** (`requirements-dev.txt`): Includes production dependencies plus:
  - `pytest` - Testing framework
  - `pytest-asyncio` - Async test support
  - `freezegun` - Time mocking for tests
  - `pytest-cov` - Test coverage reporting
  - `coverage` - Coverage measurement tool

### CI/CD Usage

In CI/CD pipelines, use the compiled files for deterministic builds:

```bash
# Production deployment
pip install --no-deps -r requirements.txt

# Development/testing
pip install --no-deps -r requirements-dev.txt
```

## Troubleshooting

### Version Conflicts

If you encounter version conflicts:

1. Check if a dependency is specified in both `requirements.in` and `requirements-dev.in`
2. Ensure version constraints are compatible
3. Regenerate both compiled files:
   ```bash
   pip-compile requirements.in
   pip-compile requirements-dev.in
   ```

### Outdated Compiled Files

If `requirements.txt` or `requirements-dev.txt` seem outdated:

1. Regenerate them:
   ```bash
   pip-compile --upgrade requirements.in
   pip-compile --upgrade requirements-dev.in
   ```

2. Review the changes carefully
3. Test the application after updating

### Missing Dependencies

If a dependency is missing:

1. Check if it's in `requirements.in` (production) or `requirements-dev.in` (dev)
2. Add it to the appropriate `.in` file
3. Regenerate the compiled file
4. Install: `pip-sync requirements-dev.txt`

## Test Coverage

To run tests with coverage reporting:

```bash
# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View HTML report (opens in browser)
open htmlcov/index.html
```

Coverage reports show which lines of code are covered by tests. The `--cov-report=term-missing` option shows missing lines in the terminal output.

