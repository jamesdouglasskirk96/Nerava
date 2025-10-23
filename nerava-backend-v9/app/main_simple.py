from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .config import settings
from .middleware.logging import LoggingMiddleware
from .middleware.metrics import MetricsMiddleware
from .middleware.ratelimit import RateLimitMiddleware
from .middleware.region import RegionMiddleware, ReadWriteRoutingMiddleware, CanaryRoutingMiddleware

from fastapi.staticfiles import StaticFiles
import os

# Domain routers
from .routers import (
    users,
    hubs,
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
)

# Auth + JWT preferences
from .routers.auth import router as auth_router
from .routers.user_prefs import router as prefs_router

app = FastAPI(title="Nerava Backend v9", version="0.9.0")

# Mount UI after app is defined
UI_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui-mobile"))
if os.path.isdir(UI_DIR):
    app.mount("/app", StaticFiles(directory=UI_DIR, html=True), name="ui")

# Create tables on startup (SQLite dev)
Base.metadata.create_all(bind=engine)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
app.add_middleware(RegionMiddleware)
app.add_middleware(ReadWriteRoutingMiddleware)
app.add_middleware(CanaryRoutingMiddleware, canary_percentage=0.0)  # Disabled by default

# CORS (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins.split(",") if settings.cors_allow_origins != "*" else ["*"],
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
app.include_router(auth_router)
app.include_router(prefs_router)

# Legacy + domain routes
app.include_router(users.router)
app.include_router(merchants_router.router)
app.include_router(hubs.router, prefix="/v1/hubs", tags=["hubs"])
app.include_router(recommend.router, prefix="/v1", tags=["recommend"])
app.include_router(reservations.router, prefix="/v1/reservations", tags=["reservations"])
app.include_router(wallet.router)
app.include_router(chargers.router, prefix="/v1/chargers", tags=["chargers"])
app.include_router(webhooks.router)
app.include_router(users_register.router)
app.include_router(merchants_local.router, prefix="/v1/local", tags=["local_merchants"])
app.include_router(incentives.router)
app.include_router(energyhub.router)
