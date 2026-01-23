"""PostHog analytics integration (server-side)."""
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

_posthog = None


def init_posthog():
    """Initialize PostHog client if configured."""
    global _posthog

    if not settings.ANALYTICS_ENABLED:
        logger.info("[PostHog] Disabled via ANALYTICS_ENABLED=false")
        return

    if not settings.POSTHOG_API_KEY:
        logger.info("[PostHog] No API key configured")
        return

    try:
        import posthog
        posthog.project_api_key = settings.POSTHOG_API_KEY
        posthog.host = settings.POSTHOG_HOST
        _posthog = posthog
        logger.info("[PostHog] Initialized")
    except ImportError:
        logger.warning("[PostHog] posthog package not installed")
    except Exception as e:
        logger.warning(f"[PostHog] Failed to initialize: {e}")


def track(
    distinct_id: str,
    event: str,
    properties: Optional[Dict[str, Any]] = None,
):
    """Track an event. Fails silently if PostHog not initialized."""
    if _posthog is None:
        return

    try:
        _posthog.capture(distinct_id, event, properties or {})
    except Exception as e:
        logger.debug(f"[PostHog] Failed to track {event}: {e}")


