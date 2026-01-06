"""
Centralized environment detection utilities.

This module provides a single source of truth for environment detection.
All functions check ENV only, never REGION, to prevent spoofing in production.

P0 Security: REGION can be set to 'local' in production deployments, which would
bypass security checks. Always use ENV for environment detection.
"""
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_env_name() -> str:
    """
    Get the current environment name from ENV variable.
    
    Returns:
        Environment name (lowercase): 'local', 'dev', 'staging', 'prod', etc.
        Defaults to 'dev' if not set.
    
    Security Note:
        Only checks ENV variable, never REGION. REGION can be spoofed.
    """
    return os.getenv("ENV", "dev").lower()


@lru_cache(maxsize=1)
def is_local_env() -> bool:
    """
    Check if running in local environment.
    
    Returns:
        True if ENV is 'local' or 'dev', False otherwise.
    
    Security Note:
        Only checks ENV, not REGION, to prevent spoofing in production.
        REGION can be set to 'local' in production deployments, which would bypass security.
    
    Cached to avoid repeated env lookups.
    """
    env = get_env_name()
    # DO NOT check REGION - it can be spoofed in production
    return env in {"local", "dev"}


@lru_cache(maxsize=1)
def is_production_env() -> bool:
    """
    Check if running in production environment.
    
    Returns:
        True if ENV is 'prod' or 'production', False otherwise.
    
    Security Note:
        Only checks ENV, not REGION, to prevent spoofing in production.
    """
    env = get_env_name()
    return env in {"prod", "production"}


@lru_cache(maxsize=1)
def is_staging_env() -> bool:
    """
    Check if running in staging environment.
    
    Returns:
        True if ENV is 'staging' or 'stage', False otherwise.
    """
    env = get_env_name()
    return env in {"staging", "stage"}







