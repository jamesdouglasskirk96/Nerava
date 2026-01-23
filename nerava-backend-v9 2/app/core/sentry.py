"""Sentry error tracking integration"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_sentry_initialized = False


def init_sentry() -> bool:
    """Initialize Sentry SDK. Returns True if initialized successfully."""
    global _sentry_initialized

    from app.core.config import settings

    if not settings.SENTRY_ENABLED:
        logger.info("[Sentry] Disabled via SENTRY_ENABLED=false")
        return False

    if not settings.SENTRY_DSN:
        logger.info("[Sentry] No DSN configured, skipping initialization")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            release=settings.SENTRY_RELEASE or None,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            # Scrub sensitive data
            before_send=scrub_sensitive_data,
            send_default_pii=False,
        )

        _sentry_initialized = True
        logger.info(f"[Sentry] Initialized for environment={settings.SENTRY_ENVIRONMENT}")
        return True

    except Exception as e:
        logger.warning(f"[Sentry] Failed to initialize: {e}")
        return False


def scrub_sensitive_data(event, hint):
    """Remove sensitive data from Sentry events."""
    # Scrub request headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "cookie", "x-api-key", "x-auth-token"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"

    # Scrub phone numbers in exception values
    if "exception" in event and "values" in event["exception"]:
        for exc in event["exception"]["values"]:
            if "value" in exc and exc["value"]:
                import re
                # Mask phone numbers
                exc["value"] = re.sub(r'\+?1?\d{10,14}', '[PHONE_REDACTED]', str(exc["value"]))

    return event


def capture_exception(exc: Exception, extra: Optional[dict] = None):
    """Capture exception to Sentry if initialized."""
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass  # Never let Sentry break the app


def capture_message(message: str, level: str = "info", extra: Optional[dict] = None):
    """Capture message to Sentry if initialized."""
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


