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
        
        # Test cache connection
        await cache.get("health_check")
        logger.info("Cache connection verified")
        
        # Test database connection
        from app.db import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection verified")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nerava Backend v9...")
    
    try:
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
