from pydantic import BaseModel
import os
from datetime import timedelta
from typing import Dict, Any
from functools import lru_cache

class Settings(BaseModel):
    SECRET_KEY: str = os.getenv("NERAVA_SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET: str = os.getenv("JWT_SECRET", os.getenv("NERAVA_SECRET_KEY", "dev-secret-change-me"))  # JWT_SECRET env var
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nerava.db")
    
    @property
    def jwt_secret(self) -> str:
        """Lowercase alias for JWT_SECRET for backward compatibility"""
        return self.JWT_SECRET
    
    # Stripe configuration
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", os.getenv("STRIPE_SECRET", ""))  # Support both names
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8001")
    
    # Smartcar configuration
    # For local dev, use sandbox mode. In production, set SMARTCAR_MODE=live
    SMARTCAR_CLIENT_ID: str = os.getenv("SMARTCAR_CLIENT_ID", "")
    SMARTCAR_CLIENT_SECRET: str = os.getenv("SMARTCAR_CLIENT_SECRET", "")
    SMARTCAR_REDIRECT_URI: str = os.getenv("SMARTCAR_REDIRECT_URI", "")
    SMARTCAR_MODE: str = os.getenv("SMARTCAR_MODE", "sandbox")  # sandbox (dev) or live (production)
    SMARTCAR_BASE_URL: str = os.getenv("SMARTCAR_BASE_URL", "https://api.smartcar.com")
    SMARTCAR_AUTH_URL: str = os.getenv("SMARTCAR_AUTH_URL", "https://auth.smartcar.com")
    SMARTCAR_CONNECT_URL: str = os.getenv("SMARTCAR_CONNECT_URL", "https://connect.smartcar.com")
    SMARTCAR_STATE_SECRET: str = os.getenv("SMARTCAR_STATE_SECRET", "")  # Distinct secret for Smartcar state JWT
    SMARTCAR_ENABLED: bool = os.getenv("SMARTCAR_ENABLED", "false").lower() == "true"  # Feature flag to disable Smartcar
    
    @property
    def smartcar_enabled(self) -> bool:
        """
        Check if Smartcar integration is fully configured and enabled.
        Returns True only if SMARTCAR_ENABLED=true AND client_id, client_secret, and redirect_uri are all set.
        """
        if not self.SMARTCAR_ENABLED:
            return False
        return bool(
            self.SMARTCAR_CLIENT_ID and 
            self.SMARTCAR_CLIENT_SECRET and 
            self.SMARTCAR_REDIRECT_URI
        )
    
    # Google Places API (New) configuration
    GOOGLE_PLACES_API_KEY: str = os.getenv("GOOGLE_PLACES_API_KEY", "")
    
    # Merchant auth mock mode
    MERCHANT_AUTH_MOCK: bool = os.getenv("MERCHANT_AUTH_MOCK", "false").lower() == "true"
    
    # Intent capture configuration
    LOCATION_ACCURACY_THRESHOLD_M: float = float(os.getenv("LOCATION_ACCURACY_THRESHOLD_M", "100"))  # Default 100m
    INTENT_SESSION_ONBOARDING_THRESHOLD: int = int(os.getenv("INTENT_SESSION_ONBOARDING_THRESHOLD", "3"))  # Require onboarding after N sessions
    
    # Confidence tier thresholds (in meters)
    CONFIDENCE_TIER_A_THRESHOLD_M: float = float(os.getenv("CONFIDENCE_TIER_A_THRESHOLD_M", "120"))  # Tier A: <120m
    CONFIDENCE_TIER_B_THRESHOLD_M: float = float(os.getenv("CONFIDENCE_TIER_B_THRESHOLD_M", "400"))  # Tier B: <400m
    
    # Exclusive session configuration
    CHARGER_RADIUS_M: float = float(os.getenv("CHARGER_RADIUS_M", "150"))  # Charger radius for activation (meters)
    EXCLUSIVE_DURATION_MIN: int = int(os.getenv("EXCLUSIVE_DURATION_MIN", "60"))  # Exclusive session duration (minutes)
    
    # Google Places search radius
    GOOGLE_PLACES_SEARCH_RADIUS_M: int = int(os.getenv("GOOGLE_PLACES_SEARCH_RADIUS_M", "800"))  # 800m radius for merchant search
    
    # Merchant cache TTL (in seconds)
    MERCHANT_CACHE_TTL_SECONDS: int = int(os.getenv("MERCHANT_CACHE_TTL_SECONDS", "3600"))  # 1 hour default
    
    # Vehicle onboarding photo retention (in days)
    VEHICLE_ONBOARDING_RETENTION_DAYS: int = int(os.getenv("VEHICLE_ONBOARDING_RETENTION_DAYS", "90"))  # 90 days default
    
    # Perk unlock caps
    MAX_PERK_UNLOCKS_PER_SESSION: int = int(os.getenv("MAX_PERK_UNLOCKS_PER_SESSION", "1"))  # Max unlocks per intent session
    PERK_COOLDOWN_MINUTES_PER_MERCHANT: int = int(os.getenv("PERK_COOLDOWN_MINUTES_PER_MERCHANT", "60"))  # Cooldown in minutes per merchant
    
    # Platform fee configuration (in basis points, 1500 = 15%)
    PLATFORM_FEE_BPS: int = int(os.getenv("PLATFORM_FEE_BPS", "1500"))
    
    # Auth Provider Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    APPLE_CLIENT_ID: str = os.getenv("APPLE_CLIENT_ID", "")
    APPLE_TEAM_ID: str = os.getenv("APPLE_TEAM_ID", "")
    APPLE_KEY_ID: str = os.getenv("APPLE_KEY_ID", "")
    APPLE_PRIVATE_KEY: str = os.getenv("APPLE_PRIVATE_KEY", "")
    
    # Phone OTP Configuration (Twilio Verify)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_VERIFY_SERVICE_SID: str = os.getenv("TWILIO_VERIFY_SERVICE_SID", "")
    OTP_PROVIDER: str = os.getenv("OTP_PROVIDER", "stub")  # twilio_verify, twilio_sms, stub
    
    # SMS Configuration (for custom messages)
    OTP_FROM_NUMBER: str = os.getenv("OTP_FROM_NUMBER", "")  # Phone number to send SMS from
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")  # Alternative env var name
    
    # Normalize legacy "twilio" to "twilio_verify"
    @property
    def otp_provider_normalized(self) -> str:
        provider = self.OTP_PROVIDER.lower()
        if provider == "twilio":
            return "twilio_verify"
        return provider
    
    # Refresh Token Configuration
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # Demo Mode Settings
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    DEMO_ADMIN_KEY: str = os.getenv("DEMO_ADMIN_KEY", "")
    
    # Wallet and Nova Settings
    DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "America/Chicago")
    NOVA_TO_USD_CONVERSION_RATE_CENTS: int = int(os.getenv("NOVA_TO_USD_CONVERSION_RATE_CENTS", "10"))
    
    # Environment and Debug Settings
    ENV: str = os.getenv("ENV", "dev")  # dev, staging, prod
    DEBUG_RETURN_MAGIC_LINK: bool = os.getenv("DEBUG_RETURN_MAGIC_LINK", "false").lower() == "true"
    
    # Apple Wallet Configuration
    APPLE_WALLET_SIGNING_ENABLED: bool = os.getenv("APPLE_WALLET_SIGNING_ENABLED", "false").lower() == "true"
    APPLE_WALLET_PASS_TYPE_ID: str = os.getenv("APPLE_WALLET_PASS_TYPE_ID", "pass.com.nerava.wallet")
    APPLE_WALLET_TEAM_ID: str = os.getenv("APPLE_WALLET_TEAM_ID", "")
    APPLE_WALLET_CERT_P12_PATH: str = os.getenv("APPLE_WALLET_CERT_P12_PATH", "")
    APPLE_WALLET_CERT_P12_PASSWORD: str = os.getenv("APPLE_WALLET_CERT_P12_PASSWORD", "")
    APPLE_WALLET_APNS_KEY_ID: str = os.getenv("APPLE_WALLET_APNS_KEY_ID", "")
    APPLE_WALLET_APNS_TEAM_ID: str = os.getenv("APPLE_WALLET_APNS_TEAM_ID", "")
    APPLE_WALLET_APNS_AUTH_KEY_PATH: str = os.getenv("APPLE_WALLET_APNS_AUTH_KEY_PATH", "")
    
    # HubSpot Configuration
    HUBSPOT_ENABLED: bool = os.getenv("HUBSPOT_ENABLED", "false").lower() == "true"
    HUBSPOT_SEND_LIVE: bool = os.getenv("HUBSPOT_SEND_LIVE", "false").lower() == "true"
    HUBSPOT_PRIVATE_APP_TOKEN: str = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN", "")
    HUBSPOT_PORTAL_ID: str = os.getenv("HUBSPOT_PORTAL_ID", "")
    
    # Sentry Configuration
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENV", "dev"))
    SENTRY_RELEASE: str = os.getenv("SENTRY_RELEASE", "")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    SENTRY_ENABLED: bool = os.getenv("SENTRY_ENABLED", "true").lower() == "true"
    
    # Email Configuration
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "console")  # console, sendgrid
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@nerava.network")
    EMAIL_REPLY_TO: str = os.getenv("EMAIL_REPLY_TO", "")
    EMAIL_BASE_URL: str = os.getenv("EMAIL_BASE_URL", "https://nerava.network")
    
    # PostHog Configuration (backend - optional)
    POSTHOG_API_KEY: str = os.getenv("POSTHOG_API_KEY", "")
    POSTHOG_HOST: str = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"
    
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
    feature_virtual_card: bool = False  # Virtual card generation feature

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

def validate_config():
    """Validate configuration at startup. Raises ValueError if invalid."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate Apple Wallet configuration if signing is enabled
    if settings.APPLE_WALLET_SIGNING_ENABLED:
        missing = []
        if not settings.APPLE_WALLET_PASS_TYPE_ID:
            missing.append("APPLE_WALLET_PASS_TYPE_ID")
        if not settings.APPLE_WALLET_TEAM_ID:
            missing.append("APPLE_WALLET_TEAM_ID")
        
        # Check for P12 or PEM cert/key
        has_p12 = bool(settings.APPLE_WALLET_CERT_P12_PATH and os.path.exists(settings.APPLE_WALLET_CERT_P12_PATH))
        cert_path = os.getenv("APPLE_WALLET_CERT_PATH", "")
        key_path = os.getenv("APPLE_WALLET_KEY_PATH", "")
        has_pem = bool(cert_path and os.path.exists(cert_path) and key_path and os.path.exists(key_path))
        
        if not (has_p12 or has_pem):
            missing.append("APPLE_WALLET_CERT_P12_PATH (or APPLE_WALLET_CERT_PATH + APPLE_WALLET_KEY_PATH)")
        
        if missing:
            error_msg = f"Apple Wallet signing enabled but missing required configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("Apple Wallet configuration validated")
    
    # Validate HubSpot configuration if send_live is enabled
    if settings.HUBSPOT_SEND_LIVE:
        if not settings.HUBSPOT_ENABLED:
            error_msg = "HUBSPOT_SEND_LIVE is true but HUBSPOT_ENABLED is false"
            logger.error(error_msg)
            raise ValueError(error_msg)
        missing = []
        if not settings.HUBSPOT_PRIVATE_APP_TOKEN:
            missing.append("HUBSPOT_PRIVATE_APP_TOKEN")
        if not settings.HUBSPOT_PORTAL_ID:
            missing.append("HUBSPOT_PORTAL_ID")
        if missing:
            error_msg = f"HubSpot send_live enabled but missing required configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("HubSpot configuration validated")
    
    # Validate Email configuration in production
    if settings.ENV == "prod" and settings.EMAIL_PROVIDER == "sendgrid":
        missing = []
        if not settings.SENDGRID_API_KEY:
            missing.append("SENDGRID_API_KEY")
        if not settings.EMAIL_FROM:
            missing.append("EMAIL_FROM")
        if missing:
            error_msg = f"SendGrid email enabled in prod but missing: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("Email configuration validated")
    
    # Validate OTP configuration
    otp_provider = settings.otp_provider_normalized
    if settings.ENV == "prod" and otp_provider == "twilio_verify":
        missing = []
        placeholders = ["your-", "xxx", "placeholder", "test"]
        
        if not settings.TWILIO_ACCOUNT_SID or any(p in settings.TWILIO_ACCOUNT_SID.lower() for p in placeholders):
            missing.append("TWILIO_ACCOUNT_SID")
        if not settings.TWILIO_AUTH_TOKEN or any(p in settings.TWILIO_AUTH_TOKEN.lower() for p in placeholders):
            missing.append("TWILIO_AUTH_TOKEN")
        if not settings.TWILIO_VERIFY_SERVICE_SID or not settings.TWILIO_VERIFY_SERVICE_SID.startswith("VA"):
            missing.append("TWILIO_VERIFY_SERVICE_SID (must start with VA)")
        
        if missing:
            error_msg = f"Twilio Verify in prod requires real credentials. Missing/invalid: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    # Prevent stub in production (unless DEMO_MODE)
    if settings.ENV == "prod" and otp_provider == "stub" and not settings.DEMO_MODE:
        error_msg = "OTP_PROVIDER=stub is not allowed in production (set DEMO_MODE=true to override)"
        logger.error(error_msg)
        raise ValueError(error_msg)
