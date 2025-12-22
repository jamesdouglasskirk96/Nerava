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
        
        # Check for missing migrations (local-only, non-blocking)
        import os
        env = os.getenv("ENV", "dev").lower()
        is_local = env == "local" or settings.region.lower() == "local"
        
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
