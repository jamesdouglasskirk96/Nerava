# Observability & Error Tracking

This document describes how to configure and use error tracking and observability tools in the Nerava backend.

## Sentry Error Tracking

Sentry is integrated for error tracking and performance monitoring. It is automatically enabled when `SENTRY_DSN` is set and the environment is not local.

### Configuration

1. **Get a Sentry DSN:**
   - Sign up at https://sentry.io/
   - Create a new project
   - Copy your DSN from the project settings

2. **Set Environment Variable:**
   ```bash
   export SENTRY_DSN=https://your-key@sentry.io/your-project-id
   ```

3. **Add to `.env` file:**
   ```bash
   SENTRY_DSN=https://your-key@sentry.io/your-project-id
   ```

### Behavior

- **Local/Dev Environments:** Sentry is NOT initialized (even if DSN is set)
  - Prevents local development errors from polluting production error tracking
  - Logs indicate "Sentry DSN configured but not initializing in local environment"

- **Production/Staging:** Sentry is initialized when DSN is set
  - Errors are automatically captured and sent to Sentry
  - Performance monitoring is enabled (10% sample rate)
  - Profiling is enabled (10% sample rate)

### What Gets Tracked

- **Unhandled Exceptions:** All exceptions that reach the global exception handler
- **FastAPI Errors:** HTTP exceptions and validation errors
- **Database Errors:** SQLAlchemy errors
- **Logging Errors:** Errors logged at ERROR level
- **Performance:** Request traces (10% sample rate)
- **Profiles:** Performance profiles (10% sample rate)

### PII Scrubbing

Sentry is configured with `send_default_pii=False` to prevent sending personally identifiable information. The following data is automatically scrubbed:

- Email addresses
- User IDs
- Passwords
- Tokens
- API keys

### Testing Sentry in Staging

1. Set `ENV=staging` (or `ENV=prod`)
2. Set `SENTRY_DSN` to your Sentry project DSN
3. Trigger an error (e.g., visit a non-existent endpoint that raises an exception)
4. Check your Sentry dashboard for the error

### Sample Rate Configuration

Current configuration:
- **Traces Sample Rate:** 10% (`traces_sample_rate=0.1`)
- **Profiles Sample Rate:** 10% (`profiles_sample_rate=0.1`)

To adjust these rates, edit `app/main_simple.py`:
```python
sentry_sdk.init(
    ...
    traces_sample_rate=0.1,  # Adjust as needed
    profiles_sample_rate=0.1,  # Adjust as needed
)
```

### Disabling Sentry

To disable Sentry:
1. Remove or unset `SENTRY_DSN` environment variable
2. Restart the application

### Troubleshooting

**Sentry not initializing:**
- Check that `sentry-sdk` is installed: `pip list | grep sentry`
- Check that `SENTRY_DSN` is set correctly
- Check that `ENV` is not `local` or `dev`
- Check application logs for Sentry initialization messages

**Errors not appearing in Sentry:**
- Verify DSN is correct
- Check Sentry project settings
- Verify environment is not local/dev
- Check application logs for Sentry errors

## Logging

The application uses Python's standard `logging` module with structured logging to stdout. Logs include:

- Request/response logging (via `LoggingMiddleware`)
- Error logging with full tracebacks
- Startup validation messages
- Application lifecycle events

### Log Levels

- **INFO:** Normal application flow, request/response logging
- **WARNING:** Non-critical issues, validation warnings
- **ERROR:** Errors that don't crash the application
- **CRITICAL:** Critical errors that may crash the application

### Log Format

```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

Example:
```
2025-01-15 10:30:45,123 [INFO] nerava: Starting Nerava Backend v9
```

## Health Checks

The application provides health check endpoints:

- **`/healthz`:** Basic health check (always returns 200)
- **`/readyz`:** Readiness check (verifies database and Redis connectivity)

These endpoints can be used by load balancers and orchestration systems to determine service health.

## Related Documentation

- `docs/LEGACY_CODE_STATUS.md` - Legacy code documentation
- `docs/TEST_CLEANUP.md` - Test cleanup documentation
- `DEPENDENCIES.md` - Dependency management










