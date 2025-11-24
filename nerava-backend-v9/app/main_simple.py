from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from .db import Base, engine
from .config import settings
from .run_migrations import run_migrations

logger = logging.getLogger(__name__)
from .middleware.logging import LoggingMiddleware
from .middleware.metrics import MetricsMiddleware
from .middleware.ratelimit import RateLimitMiddleware
from .middleware.region import RegionMiddleware, ReadWriteRoutingMiddleware, CanaryRoutingMiddleware
from .middleware.demo_banner import DemoBannerMiddleware

from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

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
    intents,
    admin,
    ml,
    ledger,
    merchant_analytics,
    challenges,
    grid,
    payouts,
    profile,
    square,
    # 20 Feature Scaffold Routers
    merchant_intel,
    behavior_cloud,
    reward_routing,
    city_marketplace,
    multimodal,
    merchant_credits,
    verify_api,
    wallet_interop,
    coop_pools,
    sdk,
    energy_rep,
    offsets,
    fleet,
    iot,
    deals,
    events,
    tenant,
    ai_rewards,
    finance,
    ai_growth,
    demo,
    dual_zone,
)
from .routers import gpt, meta, sessions, stripe_api, purchase_webhooks, dev_tools, merchant_api, merchant_ui
from .routers import events_api, pool_api, offers_api
from .routers import sessions_verify
from .routers import debug_verify
from .routers import debug_pool
from .routers import discover_api, affiliate_api, insights_api
from .routers import while_you_charge, pilot, pilot_debug, merchant_reports, merchant_balance, pilot_redeem

# Auth + JWT preferences
from .routers.auth import router as auth_router
from .routers.user_prefs import router as prefs_router

app = FastAPI(title="Nerava Backend v9", version="0.9.0")

# Redirect root to /app
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app/")

# Serve OpenAPI spec for ChatGPT Actions
@app.get("/openapi-actions.yaml")
async def get_openapi_spec(request: Request):
    """Return OpenAPI spec for ChatGPT Actions"""
    from pathlib import Path
    import os
    from fastapi.responses import Response
    
    # Get the current server URL from the request
    current_url = str(request.url).replace("/openapi-actions.yaml", "")
    
    # Try to read the generated spec file (stored next to this module)
    spec_file = Path(__file__).parent / "openapi-actions.yaml"
    if spec_file.exists():
        content = spec_file.read_text()
        # Replace any old tunnel URLs with the current one
        content = content.replace("https://the-lightweight-mention-extensions.trycloudflare.com", current_url)
        content = content.replace("http://localhost:8001", current_url)
        return Response(content=content, media_type="text/yaml")
    
    # Fallback: generate a basic spec
    fallback_spec = f"""openapi: 3.0.0
info:
  title: Nerava API
  version: 1.0.0
  description: Nerava EV charging rewards platform
servers:
  - url: {current_url}
    description: Nerava API
paths:
  /v1/gpt/find_merchants:
    get:
      summary: Find nearby merchants
      operationId: find_merchants
      responses:
        '200':
          description: List of merchants
  /v1/gpt/find_charger:
    get:
      summary: Find nearby EV chargers
      operationId: find_charger
      responses:
        '200':
          description: List of chargers
  /v1/gpt/create_session_link:
    post:
      summary: Create a verify link
      operationId: create_session_link
      responses:
        '200':
          description: Verify link created
  /v1/gpt/me:
    get:
      summary: Get user profile and wallet
      operationId: get_me
      responses:
        '200':
          description: User profile
"""
    return Response(content=fallback_spec, media_type="text/yaml")

# Mount UI after app is defined
# Use Path(__file__) to resolve relative to this file's location
UI_DIR = Path(__file__).parent.parent.parent / "ui-mobile"
if UI_DIR.exists() and UI_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

# Mount /static for verify assets
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists() and STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=False), name="static")

# Run Alembic migrations on startup (creates all tables including sessions)
try:
    logger.info("Running database migrations on startup...")
    run_migrations()
    logger.info("Database migrations completed successfully")
except Exception as e:
    logger.error(f"Failed to run migrations on startup: {e}", exc_info=True)
    # Don't fail startup if migrations fail - let the app start and log the error
    # This prevents the app from being completely broken if migrations have issues

# Create tables on startup as fallback (SQLite dev only - migrations should handle this)
# Base.metadata.create_all(bind=engine)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
app.add_middleware(RegionMiddleware)
app.add_middleware(ReadWriteRoutingMiddleware)
app.add_middleware(CanaryRoutingMiddleware, canary_percentage=0.0)  # Disabled by default
app.add_middleware(DemoBannerMiddleware)

# CORS (tighten in prod)
# Parse ALLOWED_ORIGINS from env or use defaults
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_str == "*":
    # When using credentials, cannot use "*" - allow localhost/127.0.0.1 explicitly for dev
    # Base list of allowed origins
    allowed_origins = [
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite default
    ]
    # Note: Vercel domains will be handled by custom CORS middleware below
else:
    # Split by comma and strip whitespace
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|https://web-production-.*\.up\.railway\.app|https://.*\.nerava\.network",
    allow_origins=allowed_origins + [
        "https://www.nerava.network",
        "https://nerava.network",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Api-Key", "X-Merchant-Key"],
)

# Operations routes
app.include_router(ops.router)
app.include_router(flags.router)
app.include_router(analytics.router)

# Health first
app.include_router(health.router, prefix="/v1", tags=["health"])

# Meta routes (health, version, debug)
app.include_router(meta.router)

# GPT routes
app.include_router(gpt.router)

# Sessions/Verify routes (public)
app.include_router(sessions.router)

# Auth + JWT prefs
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
app.include_router(intents.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(ml.router)
app.include_router(ledger.router)
app.include_router(merchant_analytics.router)
app.include_router(challenges.router)
app.include_router(grid.router)
app.include_router(payouts.router)
app.include_router(stripe_api.router)
app.include_router(purchase_webhooks.router)
app.include_router(dev_tools.router)
app.include_router(merchant_api.router)
app.include_router(merchant_ui.router)
app.include_router(square.router)
app.include_router(events_api.router)
app.include_router(pool_api.router)
app.include_router(offers_api.router)
app.include_router(sessions_verify.router)
app.include_router(debug_verify.router)
app.include_router(debug_pool.router)

# vNext routers
app.include_router(discover_api.router)
app.include_router(affiliate_api.router)
app.include_router(insights_api.router)
app.include_router(while_you_charge.router)
app.include_router(pilot.router)
app.include_router(pilot_debug.router)
app.include_router(merchant_reports.router)
app.include_router(merchant_balance.router)
app.include_router(pilot_redeem.router)

# Add PWA error normalization for pilot endpoints
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.utils.pwa_responses import shape_error

@app.exception_handler(HTTPException)
async def pilot_error_handler(request: Request, exc: HTTPException):
    """Normalize errors for pilot/PWA endpoints."""
    # Only apply to pilot endpoints
    if request.url.path.startswith("/v1/pilot/"):
        status_code_map = {
            400: "BadRequest",
            401: "Unauthorized",
            403: "Unauthorized",
            404: "NotFound",
            500: "Internal"
        }
        error_type = status_code_map.get(exc.status_code, "Internal")
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=shape_error(error_type, detail)
        )
    # For non-pilot endpoints, re-raise to use default FastAPI behavior
    raise exc

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Normalize validation errors for pilot/PWA endpoints."""
    if request.url.path.startswith("/v1/pilot/"):
        return JSONResponse(
            status_code=400,
            content=shape_error("BadRequest", "Invalid request data")
        )
    raise exc

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure CORS headers are always set."""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Re-raise HTTPException to use existing handlers
    if isinstance(exc, HTTPException):
        raise exc
    
    # For other exceptions, return a 500 with proper CORS headers
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Api-Key, X-Merchant-Key",
        }
    )

# 20 Feature Scaffold Routers (all behind flags)
app.include_router(merchant_intel.router)
app.include_router(behavior_cloud.router)
app.include_router(reward_routing.router)
app.include_router(city_marketplace.router)
app.include_router(multimodal.router)
app.include_router(merchant_credits.router)
app.include_router(verify_api.router)
app.include_router(wallet_interop.router)
app.include_router(coop_pools.router)
app.include_router(sdk.router)
app.include_router(energy_rep.router)
app.include_router(offsets.router)
app.include_router(fleet.router)
app.include_router(iot.router)
app.include_router(deals.router)
app.include_router(events.router)
app.include_router(tenant.router)
app.include_router(ai_rewards.router)
app.include_router(finance.router)
app.include_router(ai_growth.router)
app.include_router(demo.router)
app.include_router(dual_zone.router)
