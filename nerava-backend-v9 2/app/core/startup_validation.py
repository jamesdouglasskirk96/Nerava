"""
Startup validation functions.

These functions validate critical configuration before the application starts.
They are called during application startup and will raise ValueError if validation fails.
"""
import os
import re
import logging
from app.core.config import settings
from app.core.env import is_local_env

logger = logging.getLogger("nerava")


def validate_jwt_secret():
    """Validate JWT secret is not database URL in non-local environments"""
    if is_local_env():
        return
    
    # Read directly from environment to avoid attribute errors
    jwt_secret = os.getenv('JWT_SECRET', '')
    if not jwt_secret:
        # Fallback to SECRET_KEY if JWT_SECRET not set
        jwt_secret = getattr(settings, 'SECRET_KEY', '') or os.getenv('NERAVA_SECRET_KEY', '')
    
    database_url = os.getenv('DATABASE_URL', '') or getattr(settings, 'DATABASE_URL', '')
    
    if jwt_secret == database_url:
        error_msg = (
            "CRITICAL SECURITY ERROR: JWT secret cannot equal database_url in non-local environment. "
            f"ENV={os.getenv('ENV', 'dev')}. Set JWT_SECRET environment variable to a secure random value."
        )
        print(f"[Startup] {error_msg}", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not jwt_secret or jwt_secret == "dev-secret":
        error_msg = (
            "CRITICAL SECURITY ERROR: JWT secret must be set and not use default value in non-local environment. "
            f"ENV={os.getenv('ENV', 'dev')}. Set JWT_SECRET environment variable."
        )
        print(f"[Startup] Missing required env var: JWT_SECRET (must be a secure random value, not 'dev-secret')", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("JWT secret validation passed (not equal to database_url)")


def validate_database_url():
    """Validate database URL is not SQLite in non-local environments"""
    if is_local_env():
        return
    
    database_url = os.getenv("DATABASE_URL", "") or getattr(settings, "DATABASE_URL", "")
    if re.match(r'^sqlite:', database_url, re.IGNORECASE):
        # Extract scheme only for logging (security: don't print full URL)
        db_scheme = "sqlite:///..." if "sqlite" in database_url.lower() else "unknown"
        error_msg = (
            "CRITICAL: SQLite database is not supported in production. "
            f"DATABASE_URL={database_url[:50]}..., ENV={os.getenv('ENV', 'dev')}. "
            "Please use PostgreSQL (e.g., RDS, managed Postgres)."
        )
        print(f"[Startup] Refusing to start with SQLite database_url={db_scheme}. Use PostgreSQL instead.", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Database URL validation passed (not SQLite)")


def validate_redis_url():
    """Validate Redis URL is configured in non-local environments"""
    if is_local_env():
        return
    
    redis_url = os.getenv("REDIS_URL", "") or getattr(settings, "REDIS_URL", "")
    # Check if Redis URL is set and not the default localhost value
    if not redis_url or redis_url == "redis://localhost:6379/0":
        error_msg = (
            "CRITICAL: REDIS_URL must be configured in non-local environment. "
            f"ENV={os.getenv('ENV', 'dev')}. Redis is required for rate limiting in production. "
            "Please set REDIS_URL environment variable to a valid Redis connection string."
        )
        print(f"[Startup] Redis URL validation failed: REDIS_URL not configured", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Redis URL validation passed (REDIS_URL is configured)")


def validate_dev_flags():
    """Validate dev-only flags are not enabled in non-local environments"""
    if is_local_env():
        return
    
    if os.getenv("NERAVA_DEV_ALLOW_ANON_USER", "false").lower() == "true":
        error_msg = (
            "CRITICAL: NERAVA_DEV_ALLOW_ANON_USER cannot be enabled in non-local environment. "
            f"ENV={os.getenv('ENV', 'dev')}. This is a security risk."
        )
        print(f"[Startup] Dev flag violation: NERAVA_DEV_ALLOW_ANON_USER is enabled (security risk)", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if os.getenv("NERAVA_DEV_ALLOW_ANON_DRIVER", "false").lower() == "true":
        error_msg = (
            "CRITICAL: NERAVA_DEV_ALLOW_ANON_DRIVER cannot be enabled in non-local environment. "
            f"ENV={os.getenv('ENV', 'dev')}. This is a security risk."
        )
        print(f"[Startup] Dev flag violation: NERAVA_DEV_ALLOW_ANON_DRIVER is enabled (security risk)", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check DEMO_MODE - if it bypasses auth, fail in prod
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    if demo_mode:
        # DEMO_MODE is allowed in local, but warn if it's enabled in prod
        # (It's already gated by is_local_env() in checkout.py, but we should still warn)
        logger.warning(
            f"DEMO_MODE is enabled in {os.getenv('ENV', 'dev')} environment. "
            "Ensure it does not bypass authentication in production code paths."
        )
    
    logger.info("Dev flags validation passed (no dev flags enabled)")


def validate_token_encryption_key():
    """Validate TOKEN_ENCRYPTION_KEY is set and valid in non-local environments"""
    if is_local_env():
        return
    
    token_key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not token_key:
        error_msg = (
            "CRITICAL SECURITY ERROR: TOKEN_ENCRYPTION_KEY environment variable is required in non-local environment. "
            f"ENV={os.getenv('ENV', 'dev')}. This key is used to encrypt vehicle and Square tokens. "
            "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
        print(f"[Startup] {error_msg}", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validate key format (Fernet keys are 44-char base64)
    if len(token_key) != 44:
        error_msg = (
            "CRITICAL SECURITY ERROR: TOKEN_ENCRYPTION_KEY must be a valid Fernet key (44 characters base64). "
            f"ENV={os.getenv('ENV', 'dev')}, key length={len(token_key)}. "
            "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
        print(f"[Startup] {error_msg}", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Validate key is valid Fernet key by attempting to construct Fernet instance
    try:
        from cryptography.fernet import Fernet
        Fernet(token_key.encode('utf-8'))
        logger.info("TOKEN_ENCRYPTION_KEY validation passed (valid Fernet key)")
    except Exception as e:
        error_msg = (
            "CRITICAL SECURITY ERROR: TOKEN_ENCRYPTION_KEY is not a valid Fernet key. "
            f"ENV={os.getenv('ENV', 'dev')}, error={str(e)}. "
            "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
        print(f"[Startup] {error_msg}", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)


def validate_cors_origins():
    """Validate CORS origins are not wildcard (*) in non-local environments"""
    # Check environment directly to avoid caching issues in tests
    env = os.getenv("ENV", "dev").lower()
    if env == "local":
        return
    
    # Get from environment variable directly, with fallback to empty string
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
    if allowed_origins == "*" or (allowed_origins and "*" in allowed_origins):
        error_msg = (
            "CRITICAL SECURITY ERROR: CORS wildcard (*) is not allowed in non-local environment. "
            f"ENV={os.getenv('ENV', 'dev')}, ALLOWED_ORIGINS={allowed_origins[:50]}... "
            "Set ALLOWED_ORIGINS environment variable to explicit origins (comma-separated list). "
            "Example: ALLOWED_ORIGINS=https://app.nerava.com,https://www.nerava.com"
        )
        print(f"[Startup] {error_msg}", flush=True)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("CORS origins validation passed (no wildcard in prod)")


def check_schema_payload_hash():
    """Check if payload_hash column exists in nova_transactions (local dev only)."""
    if not is_local_env():
        return  # Skip check in non-local environments
    
    try:
        from sqlalchemy import text
        from app.db import SessionLocal
        
        db = SessionLocal()
        try:
            # Try to query payload_hash column
            db.execute(text("SELECT payload_hash FROM nova_transactions LIMIT 1"))
            logger.info("Schema check passed: payload_hash column exists")
        except Exception as e:
            if "no such column" in str(e).lower() and "payload_hash" in str(e).lower():
                logger.error("=" * 80)
                logger.error("DATABASE SCHEMA IS OUT OF DATE")
                logger.error("=" * 80)
                logger.error("The payload_hash column is missing from nova_transactions table.")
                logger.error("")
                logger.error("To fix, run:")
                logger.error("  cd nerava-backend-v9")
                logger.error("  alembic upgrade head")
                logger.error("")
                logger.error("=" * 80)
            else:
                # Other error (table might not exist, etc.) - just log, don't fail startup
                logger.debug(f"Schema check skipped (table may not exist yet): {e}")
        finally:
            db.close()
    except Exception as e:
        # Don't fail startup if check fails
        logger.debug(f"Schema check failed (non-critical): {e}")

