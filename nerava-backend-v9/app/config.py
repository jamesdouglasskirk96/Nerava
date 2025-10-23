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
    cors_allow_origins: str = "*"
    
    # Region
    region: str = "local"
    primary_region: str = "local"
    
    # Events
    events_driver: str = "inproc"
    
    # Feature flags
    enable_sync_credit: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
