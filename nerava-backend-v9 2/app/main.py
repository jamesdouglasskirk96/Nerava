from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, get_engine
from .config import settings
from .middleware.logging import LoggingMiddleware
from .middleware.metrics import MetricsMiddleware
from .middleware.ratelimit import RateLimitMiddleware
from .middleware.region import RegionMiddleware, ReadWriteRoutingMiddleware, CanaryRoutingMiddleware
from .middleware.auth import AuthMiddleware
from .middleware.audit import AuditMiddleware
from .services.async_wallet import async_wallet
from .lifespan import lifespan

from fastapi.staticfiles import StaticFiles
import os

# Domain routers
from .routers import (
    users,
    hubs,
    places,
    recommend,
    reservations,
    health,
    chargers,
    wallet,
    merchants as merchants_router,
    users_register,
    merchants_local,
    webhooks,
    incentives,
    energyhub,
    ops,
    flags,
    analytics,
    social,
    activity,
    intent,
    exclusive,
)
from .routers import vehicle_onboarding, perks

# Auth + JWT preferences
from .routers.auth import router as auth_router
from .routers.user_prefs import router as prefs_router

app = FastAPI(title="Nerava Backend v9", version="0.9.0", lifespan=lifespan)

# Mount UI after app is defined
UI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui-mobile"))
if os.path.isdir(UI_DIR):
    app.mount("/app", StaticFiles(directory=UI_DIR, html=True), name="ui")

# Mount assets directory
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui-mobile", "assets"))
if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# Mount demo charger photos directory (MUST be before /static mount)
DEMO_CHARGERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "demo_chargers"))
if os.path.isdir(DEMO_CHARGERS_DIR):
    app.mount("/static/demo_chargers", StaticFiles(directory=DEMO_CHARGERS_DIR), name="demo_chargers")

# Mount merchant photos directory for static photo serving (Asadas Grill, etc.)
MERCHANT_PHOTOS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "merchant_photos_asadas_grill"))
if os.path.isdir(MERCHANT_PHOTOS_DIR):
    app.mount("/static/merchant_photos_asadas_grill", StaticFiles(directory=MERCHANT_PHOTOS_DIR), name="merchant_photos")

# Mount Google Places merchant photos directory
GOOGLE_PHOTOS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "merchant_photos_google"))
if os.path.isdir(GOOGLE_PHOTOS_DIR):
    app.mount("/static/merchant_photos_google", StaticFiles(directory=GOOGLE_PHOTOS_DIR), name="merchant_photos_google")

# Mount general static directory (should be last)
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Create tables on startup (SQLite dev)
Base.metadata.create_all(bind=get_engine())

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
app.add_middleware(RegionMiddleware)
app.add_middleware(ReadWriteRoutingMiddleware)
app.add_middleware(CanaryRoutingMiddleware, canary_percentage=0.0)  # Disabled by default
app.add_middleware(AuthMiddleware)
app.add_middleware(AuditMiddleware)

# CORS configuration (P1 security fix)
# Validate CORS origins in non-local environments
import os
env = os.getenv("ENV", "dev").lower()
region = settings.region.lower()
is_local = env == "local" or region == "local"

if not is_local and settings.cors_allow_origins == "*":
    error_msg = (
        "CRITICAL SECURITY ERROR: CORS wildcard (*) is not allowed in non-local environment. "
        f"ENV={env}, REGION={region}. Set ALLOWED_ORIGINS environment variable to explicit origins."
    )
    raise ValueError(error_msg)

# Allow localhost for local dev UI testing against production backend
cors_origins = [
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://localhost:3000",
    "http://localhost:5173",
    "https://app.nerava.app",
    "https://www.nerava.app",
]

# Add any additional origins from env if set
if settings.cors_allow_origins and settings.cors_allow_origins != "*":
    env_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",")]
    cors_origins.extend(env_origins)
    # Remove duplicates
    cors_origins = list(dict.fromkeys(cors_origins))
elif settings.cors_allow_origins == "*" and is_local:
    # In local dev, allow wildcard
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Operations routes
app.include_router(ops.router)
app.include_router(flags.router)
app.include_router(analytics.router)

# Health first
app.include_router(health.router, prefix="/v1", tags=["health"])

# Auth + JWT prefs
# LEGACY: auth_router kept for backward compatibility, but auth_domain is canonical
app.include_router(auth_router)
app.include_router(prefs_router)

# Legacy + domain routes
app.include_router(users.router)
app.include_router(merchants_router.router)
app.include_router(hubs.router, prefix="/v1/hubs", tags=["hubs"])
app.include_router(places.router)
app.include_router(recommend.router, prefix="/v1", tags=["recommend"])
app.include_router(reservations.router, prefix="/v1/reservations", tags=["reservations"])
app.include_router(wallet.router)
app.include_router(chargers.router, prefix="/v1/chargers", tags=["chargers"])
app.include_router(webhooks.router)
app.include_router(users_register.router)
app.include_router(merchants_local.router, prefix="/v1/local", tags=["local_merchants"])
app.include_router(incentives.router)
app.include_router(energyhub.router)
app.include_router(social.router)
app.include_router(activity.router)
app.include_router(intent.router)
app.include_router(vehicle_onboarding.router)
app.include_router(perks.router)
app.include_router(exclusive.router)

# Canonical v1 API routers (promoted from Domain Charge Party MVP)
from .routers import (
    auth_domain,
    drivers_domain,
    merchants_domain,
    stripe_domain,
    admin_domain,
    nova_domain,
    ev_smartcar,
    virtual_cards,
    client_telemetry,
    notifications,
    account,
    support,
)

# These are now the canonical /v1/* endpoints (no /domain/ prefix)
app.include_router(auth_domain.router)  # /v1/auth/*
app.include_router(drivers_domain.router)  # /v1/drivers/*
app.include_router(merchants_domain.router)  # /v1/merchants/*
app.include_router(stripe_domain.router)  # /v1/stripe/*
app.include_router(admin_domain.router)  # /v1/admin/*
app.include_router(nova_domain.router)  # /v1/nova/*
app.include_router(ev_smartcar.router)  # /v1/ev/* and /oauth/smartcar/callback
app.include_router(virtual_cards.router)  # /v1/virtual_cards/*
app.include_router(client_telemetry.router)  # /v1/telemetry/*
app.include_router(notifications.router)  # /v1/notifications/*
app.include_router(account.router)  # /v1/account/*
app.include_router(support.router)  # /v1/support/*

# Lifespan events are now handled in lifespan.py
