"""
Environment helper utilities
Avoids circular imports by providing centralized env checks
"""
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def is_local_env() -> bool:
    """
    Check if running in local environment.
    
    P0-C Security: Only checks ENV, not REGION, to prevent spoofing in production.
    REGION can be set to 'local' in production deployments, which would bypass security.
    
    Cached to avoid repeated env lookups.
    """
    env = os.getenv("ENV", "dev").lower()
    # DO NOT check REGION - it can be spoofed in production
    return env in {"local", "dev"}

