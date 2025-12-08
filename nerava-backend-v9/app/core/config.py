from pydantic import BaseModel
import os
from datetime import timedelta
from typing import Dict, Any
from functools import lru_cache

class Settings(BaseModel):
    SECRET_KEY: str = os.getenv("NERAVA_SECRET_KEY", "dev-secret-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nerava.db")
    
    # Stripe configuration
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8001")
    
    # Smartcar configuration
    SMARTCAR_CLIENT_ID: str = os.getenv("SMARTCAR_CLIENT_ID", "")
    SMARTCAR_CLIENT_SECRET: str = os.getenv("SMARTCAR_CLIENT_SECRET", "")
    SMARTCAR_REDIRECT_URI: str = os.getenv("SMARTCAR_REDIRECT_URI", "")
    SMARTCAR_MODE: str = os.getenv("SMARTCAR_MODE", "live")  # live or sandbox
    SMARTCAR_BASE_URL: str = os.getenv("SMARTCAR_BASE_URL", "https://api.smartcar.com")
    SMARTCAR_AUTH_URL: str = os.getenv("SMARTCAR_AUTH_URL", "https://auth.smartcar.com")
    SMARTCAR_CONNECT_URL: str = os.getenv("SMARTCAR_CONNECT_URL", "https://connect.smartcar.com")
    
    # Demo Mode Settings
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # Environment and Debug Settings
    ENV: str = os.getenv("ENV", "dev")  # dev, staging, prod
    DEBUG_RETURN_MAGIC_LINK: bool = os.getenv("DEBUG_RETURN_MAGIC_LINK", "false").lower() == "true"
    
    # Feature Flags (default OFF for safety)
    feature_merchant_intel: bool = False
    feature_behavior_cloud: bool = False
    feature_autonomous_reward_routing: bool = False
    feature_city_marketplace: bool = False
    feature_multimodal: bool = False
    feature_merchant_credits: bool = False
    feature_charge_verify_api: bool = False
    feature_energy_wallet_ext: bool = False
    feature_merchant_utility_coops: bool = False
    feature_whitelabel_sdk: bool = False
    feature_energy_rep: bool = False
    feature_carbon_micro_offsets: bool = False
    feature_fleet_workplace: bool = False
    feature_smart_home_iot: bool = False
    feature_contextual_commerce: bool = False
    feature_energy_events: bool = False
    feature_uap_partnerships: bool = False
    feature_ai_reward_opt: bool = False
    feature_esg_finance_gateway: bool = False
    feature_ai_growth_automation: bool = False
    feature_dual_radius_verification: bool = False

settings = Settings()
ACCESS_TOKEN_EXPIRE = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

# Feature flag cache
_flag_cache: Dict[str, bool] = {}

def flag_enabled(key: str) -> bool:
    """Check if a feature flag is enabled with in-memory cache"""
    if key not in _flag_cache:
        # In production, this would query the FeatureFlag table
        # For now, use environment variables as fallback
        env_key = f"FEATURE_{key.upper()}"
        _flag_cache[key] = os.getenv(env_key, "false").lower() == "true"
    return _flag_cache[key]

def clear_flag_cache():
    """Clear the flag cache (useful for testing)"""
    global _flag_cache
    _flag_cache.clear()

def is_demo() -> bool:
    """Check if demo mode is enabled."""
    return settings.DEMO_MODE
