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
    
    Returns True if ENV == "local" OR REGION == "local"
    Cached to avoid repeated env lookups.
    """
    env = os.getenv("ENV", "dev").lower()
    region = os.getenv("REGION", "local").lower()
    return env == "local" or region == "local"

