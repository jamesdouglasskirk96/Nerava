"""
Application lifespan management for startup and shutdown events
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from app.config import settings
from app.services.async_wallet import async_wallet
from app.services.cache import cache
from app.workers.outbox_relay import outbox_relay
from app.workers.prewarm import cache_prewarmer
from app.analytics.batch_writer import analytics_batch_writer
from app.subscribers.wallet_credit import *  # Import to register subscribers

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting Nerava Backend v9...")
    
    try:
        # Initialize async wallet processor
        await async_wallet.start_worker()
        logger.info("Async wallet processor started")
        
        # Start outbox relay
        await outbox_relay.start()
        logger.info("Outbox relay started")
        
        # Start cache prewarmer
        await cache_prewarmer.start()
        logger.info("Cache prewarmer started")
        
        # Start analytics batch writer
        await analytics_batch_writer.start()
        logger.info("Analytics batch writer started")
        
        # Test cache connection
        await cache.get("health_check")
        logger.info("Cache connection verified")
        
        # Test database connection
        from app.db import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection verified")
        
        # P1-G: Prevent SQLite in production
        import re
        database_url = os.getenv("DATABASE_URL", settings.database_url)
        if not is_local and re.match(r'^sqlite:', database_url, re.IGNORECASE):
            error_msg = (
                f"CRITICAL: SQLite database is not supported in production. "
                f"DATABASE_URL={database_url[:50]}..., ENV={env}. "
                f"Please use PostgreSQL (e.g., RDS, managed Postgres)."
            )
            print(f"[Startup] Refusing to start in {env} with SQLite database_url=sqlite:///... Use PostgreSQL instead.", flush=True)
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Validate required secrets in production (P0-1: secrets hardening)
        import os
        env = os.getenv("ENV", "dev").lower()
        # P0-C: DO NOT check REGION - can be spoofed in production
        is_local = env in {"local", "dev"}
        
        # P0-C: Prevent dev flags in non-local environments
        if not is_local:
            if os.getenv("NERAVA_DEV_ALLOW_ANON_USER", "false").lower() == "true":
                error_msg = (
                    "CRITICAL: NERAVA_DEV_ALLOW_ANON_USER cannot be enabled in non-local environment. "
                    f"ENV={env}. This is a security risk."
                )
                print(f"[Startup] Dev flag violation in {env}: NERAVA_DEV_ALLOW_ANON_USER is enabled (security risk)", flush=True)
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            if os.getenv("NERAVA_DEV_ALLOW_ANON_DRIVER", "false").lower() == "true":
                error_msg = (
                    "CRITICAL: NERAVA_DEV_ALLOW_ANON_DRIVER cannot be enabled in non-local environment. "
                    f"ENV={env}. This is a security risk."
                )
                print(f"[Startup] Dev flag violation in {env}: NERAVA_DEV_ALLOW_ANON_DRIVER is enabled (security risk)", flush=True)
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        if not is_local and env == "prod":
            # Production: validate required secrets are present
            missing_secrets = []
            
            # Required secrets for production
            if not os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET") == "dev-secret":
                missing_secrets.append("JWT_SECRET (must be a secure random value)")
            
            if not os.getenv("TOKEN_ENCRYPTION_KEY"):
                missing_secrets.append("TOKEN_ENCRYPTION_KEY (required for secure token storage)")
            
            if not os.getenv("STRIPE_WEBHOOK_SECRET"):
                missing_secrets.append("STRIPE_WEBHOOK_SECRET (required for webhook verification)")
            
            if missing_secrets:
                # Extract just the env var names for the print statement (security: don't print full descriptions)
                missing_names = [s.split(" ")[0] for s in missing_secrets]
                error_msg = (
                    f"CRITICAL: Missing required secrets in production environment. "
                    f"Missing: {', '.join(missing_secrets)}. "
                    f"Set these environment variables before starting the application."
                )
                print(f"[Startup] Missing required env vars in prod: {', '.join(missing_names)}", flush=True)
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            logger.info("Production secrets validation passed")
        
        # Check for missing migrations (local-only, non-blocking)
        if is_local:
            try:
                from sqlalchemy import text
                with engine.connect() as conn:
                    # Lightweight schema check: try to query encryption_version column
                    conn.execute(text("SELECT encryption_version FROM vehicle_tokens LIMIT 1"))
                logger.debug("Migration schema check passed")
            except Exception as e:
                error_msg = str(e).lower()
                if "no such column" in error_msg or "encryption_version" in error_msg:
                    logger.warning(
                        "⚠️ Local database schema is behind. Run: cd nerava-backend-v9 && alembic upgrade head"
                    )
                else:
                    # Other errors (table doesn't exist, etc.) are fine - just log debug
                    logger.debug(f"Migration check skipped (expected in some setups): {e}")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nerava Backend v9...")
    
    try:
        # Stop analytics batch writer
        await analytics_batch_writer.stop()
        logger.info("Analytics batch writer stopped")
        
        # Stop cache prewarmer
        await cache_prewarmer.stop()
        logger.info("Cache prewarmer stopped")
        
        # Stop outbox relay
        await outbox_relay.stop()
        logger.info("Outbox relay stopped")
        
        # Stop async wallet processor
        await async_wallet.stop_worker()
        logger.info("Async wallet processor stopped")
        
        # Close database connections
        from app.db import engine
        engine.dispose()
        logger.info("Database connections closed")
        
        logger.info("Application shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Export for use in main.py
__all__ = ['lifespan']
