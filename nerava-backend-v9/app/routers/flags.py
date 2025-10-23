"""
Feature flags and configuration endpoint
"""
from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/v1/flags", tags=["flags"])

@router.get("/")
async def get_flags():
    """Get current feature flags and configuration"""
    return {
        "region": settings.region,
        "primary_region": settings.primary_region,
        "enable_multi_region": settings.region != settings.primary_region,
        "events_driver": settings.events_driver,
        "enable_sync_credit": settings.enable_sync_credit,
        "energyhub_allow_demo_at": settings.energyhub_allow_demo_at,
        "cache_ttl_windows": settings.cache_ttl_windows,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "cors_allow_origins": settings.cors_allow_origins,
        "log_level": settings.log_level
    }

@router.get("/health")
async def get_health_flags():
    """Get health-related flags"""
    return {
        "database_connected": True,  # Would check actual DB connection
        "redis_connected": True,     # Would check actual Redis connection
        "region": settings.region,
        "primary_region": settings.primary_region,
        "canary_enabled": False,    # Would check canary configuration
        "maintenance_mode": False   # Would check maintenance mode flag
    }
