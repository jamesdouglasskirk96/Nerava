from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./nerava.db"
    read_database_url: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Logging
    log_level: str = "INFO"
    
    # Request handling
    request_timeout_s: int = 5
    rate_limit_per_minute: int = 120
    
    # EnergyHub
    energyhub_allow_demo_at: bool = True
    cache_ttl_windows: int = 60
    
    # CORS
    cors_allow_origins: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Public base URL
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8001")
    
    # Region
    region: str = "local"
    primary_region: str = "local"
    
    # Events
    events_driver: str = "inproc"
    
    # Feature flags
    enable_sync_credit: bool = False
    
    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret")
    jwt_alg: str = os.getenv("JWT_ALG", "HS256")
    
    # Verify Rewards
    verify_reward_cents: int = int(os.getenv("VERIFY_REWARD_CENTS", "200"))
    verify_pool_pct: int = int(os.getenv("VERIFY_POOL_PCT", "10"))
    
    # Stripe Connect
    stripe_secret: str = os.getenv("STRIPE_SECRET", "")
    stripe_connect_client_id: str = os.getenv("STRIPE_CONNECT_CLIENT_ID", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Payout Policy
    payout_min_cents: int = int(os.getenv("PAYOUT_MIN_CENTS", "100"))
    payout_max_cents: int = int(os.getenv("PAYOUT_MAX_CENTS", "10000"))
    payout_daily_cap_cents: int = int(os.getenv("PAYOUT_DAILY_CAP_CENTS", "20000"))
    
    # Purchase Rewards
    purchase_reward_flat_cents: int = int(os.getenv("PURCHASE_REWARD_FLAT_CENTS", "150"))
    purchase_match_radius_m: int = int(os.getenv("PURCHASE_MATCH_RADIUS_M", "120"))
    purchase_session_ttl_min: int = int(os.getenv("PURCHASE_SESSION_TTL_MIN", "30"))
    webhook_shared_secret: str = os.getenv("WEBHOOK_SHARED_SECRET", "")
    
    # Anti-Fraud
    max_verify_per_hour: int = int(os.getenv("MAX_VERIFY_PER_HOUR", "6"))
    max_sessions_per_hour: int = int(os.getenv("MAX_SESSIONS_PER_HOUR", "6"))
    max_different_ips_per_day: int = int(os.getenv("MAX_DIFFERENT_IPS_PER_DAY", "5"))
    min_allowed_accuracy_m: float = float(os.getenv("MIN_ALLOWED_ACCURACY_M", "100"))
    max_geo_jump_km: float = float(os.getenv("MAX_GEO_JUMP_KM", "50"))
    block_score_threshold: int = int(os.getenv("BLOCK_SCORE_THRESHOLD", "100"))
    
    # Merchant Dashboard
    dashboard_enable: bool = os.getenv("DASHBOARD_ENABLE", "true").lower() == "true"
    
    # Events & Verification
    push_enabled: bool = os.getenv("PUSH_ENABLED", "true").lower() == "true"
    city_fallback: str = os.getenv("CITY_FALLBACK", "Austin")
    max_push_per_day_per_user: int = int(os.getenv("MAX_PUSH_PER_DAY_PER_USER", "2"))
    verify_geo_radius_m: int = int(os.getenv("VERIFY_GEO_RADIUS_M", "120"))
    verify_default_radius_m: int = int(os.getenv("VERIFY_DEFAULT_RADIUS_M", "120"))
    verify_min_accuracy_m: int = int(os.getenv("VERIFY_MIN_ACCURACY_M", "100"))
    verify_dwell_required_s: int = int(os.getenv("VERIFY_DWELL_REQUIRED_S", "60"))
    verify_ping_max_step_s: int = int(os.getenv("VERIFY_PING_MAX_STEP_S", "15"))
    verify_allow_start_without_target: bool = os.getenv("VERIFY_ALLOW_START_WITHOUT_TARGET", "true").lower() == "true"
    debug_verbose: bool = os.getenv("DEBUG_VERBOSE", "true").lower() == "true"
    verify_time_window_lead_min: int = int(os.getenv("VERIFY_TIME_WINDOW_LEAD_MIN", "10"))
    verify_time_window_tail_min: int = int(os.getenv("VERIFY_TIME_WINDOW_TAIL_MIN", "15"))
    pool_reward_cap_cents: int = int(os.getenv("POOL_REWARD_CAP_CENTS", "150"))
    
    # Demo Mode (relaxes time window restrictions for testing)
    demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
