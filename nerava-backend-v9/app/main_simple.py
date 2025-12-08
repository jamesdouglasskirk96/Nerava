from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from .db import Base, engine
from .config import settings
from .run_migrations import run_migrations

# Configure logging for production visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Use a consistent logger name for all app logs
logger = logging.getLogger("nerava")
logger.info("Starting Nerava Backend v9")

# CRITICAL DEBUG: Confirm this file is being loaded
print(">>>> Nerava main_simple.py LOADED <<<<", flush=True)
logger.info(">>>> Nerava main_simple.py LOADED <<<<")

# CRITICAL: Run migrations FIRST before importing any routers that might import models
# This ensures Base.metadata is clean and models are registered in the correct order
# Note: models_domain will be imported during migrations (via env.py) and again when routers load
# Python's module cache should prevent re-execution, but if duplicate table errors occur,
# it means models are being registered twice in the same metadata instance
try:
    logger.info("Running database migrations on startup (before router imports)...")
    run_migrations()
    logger.info("Database migrations completed successfully")
except Exception as e:
    logger.error(f"Failed to run migrations on startup: {e}", exc_info=True)
    # Don't fail startup if migrations fail - let the app start and log the error
    # This prevents the app from being completely broken if migrations have issues

from .middleware.logging import LoggingMiddleware
from .middleware.metrics import MetricsMiddleware
from .middleware.ratelimit import RateLimitMiddleware
from .middleware.region import RegionMiddleware, ReadWriteRoutingMiddleware, CanaryRoutingMiddleware
from .middleware.demo_banner import DemoBannerMiddleware

from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# Domain routers (imported AFTER migrations to avoid model registration conflicts)
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
from .routers import ev_smartcar

# Auth + JWT preferences
from .routers.auth import router as auth_router
from .routers.user_prefs import router as prefs_router

app = FastAPI(title="Nerava Backend v9", version="0.9.0")

# CRITICAL DEBUG: Confirm app object is created
print(">>>> Nerava REAL APP MODULE LOADED - app object created <<<<", flush=True)
logger.info(">>>> Nerava REAL APP MODULE LOADED - app object created <<<<")

# Request/Response logging middleware
# CRITICAL: This middleware MUST execute for Railway logs to show requests/errors
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses for debugging in Railway"""
    # Skip detailed logging for static files to reduce noise
    is_static = request.url.path.startswith("/app/") or request.url.path.startswith("/static/")
    
    if not is_static:
        print(f">>>> REQUEST {request.method} {request.url.path} <<<<", flush=True)
        logger.info(">>>> REQUEST %s %s <<<<", request.method, request.url.path)
    
    try:
        response = await call_next(request)
        
        if not is_static:
            print(f">>>> RESPONSE {request.method} {request.url.path} -> {response.status_code} <<<<", flush=True)
            logger.info(">>>> RESPONSE %s %s -> %s <<<<", request.method, request.url.path, response.status_code)
        return response
    except Exception as e:
        # For static files, let the exception propagate without logging (StaticFiles will handle it)
        if is_static:
            raise
        
        # Log full stack trace in Railway logs for non-static requests
        print(f">>>> UNHANDLED ERROR during {request.method} {request.url.path}: {e} <<<<", flush=True)
        logger.exception(">>>> UNHANDLED ERROR during %s %s <<<<", request.method, request.url.path)
        raise

# CRITICAL DEBUG: Confirm middleware decorator was applied
print(">>>> Nerava Logging Middleware Decorator Applied <<<<", flush=True)
logger.info(">>>> Nerava Logging Middleware Decorator Applied <<<<")

# Redirect root to /app
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    try:
        return RedirectResponse(url="/app/")
    except Exception as e:
        logger.exception("Error in root redirect: %s", str(e))
        raise

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

# Mount UI AFTER all middleware to ensure it's processed last
# StaticFiles should handle its own errors (404 for missing files)
# Use Path(__file__) to resolve relative to this file's location
UI_DIR = Path(__file__).parent.parent.parent / "ui-mobile"
avatar_png = None
index_html = None
if UI_DIR.exists() and UI_DIR.is_dir():
    avatar_png = UI_DIR / "img" / "avatar-default.png"
    index_html = UI_DIR / "index.html"
    
    # Register direct route handlers BEFORE mount so they take precedence
    # Handler for /app (without trailing slash) - redirect to /app/
    @app.get("/app")
    async def serve_app_root():
        """Redirect /app to /app/ to ensure index.html is served"""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app/", status_code=301)
    
    # Handler for /app/ - serve index.html directly
    if index_html and index_html.exists():
        @app.get("/app/")
        async def serve_app_index():
            """Direct route handler for /app/ to serve index.html"""
            try:
                with open(index_html, 'rb') as f:
                    content = f.read()
                from fastapi.responses import Response
                return Response(content=content, media_type="text/html")
            except Exception as e:
                logger.error(f"Error serving index.html: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Error serving index.html: {str(e)}")
        logger.info("Added direct route handler for /app/")
    
    # Handler for avatar-default.png
    if avatar_png and avatar_png.exists():
        @app.get("/app/img/avatar-default.png")
        async def serve_avatar_default():
            """Direct route handler for avatar-default.png to bypass StaticFiles issues"""
            try:
                with open(avatar_png, 'rb') as f:
                    content = f.read()
                from fastapi.responses import Response
                return Response(
                    content=content,
                    media_type="image/svg+xml",  # File is SVG data URI
                    headers={"Content-Disposition": 'inline; filename="avatar-default.png"'}
                )
            except Exception as e:
                logger.error(f"Error in serve_avatar_default: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Error serving avatar: {str(e)}")
        logger.info("Added direct route handler for /app/img/avatar-default.png")
    
    # Now mount StaticFiles - routes registered above will take precedence
    try:
        # Use check_dir=False to prevent crashes if directory structure is unexpected
        # Mount AFTER middleware but AFTER route handlers to ensure routes take precedence
        app.mount("/app", StaticFiles(directory=str(UI_DIR), html=True, check_dir=False), name="ui")
        logger.info("Mounted UI at /app from directory: %s", str(UI_DIR))
        # Verify key files exist
        me_js = UI_DIR / "js" / "pages" / "me.js"
        if me_js.exists():
            logger.info("Verified: me.js exists at %s", str(me_js))
        else:
            logger.warning("me.js not found at %s", str(me_js))
        if avatar_png.exists():
            logger.info("Verified: avatar-default.png exists at %s", str(avatar_png))
        else:
            logger.warning("avatar-default.png not found at %s", str(avatar_png))
    except Exception as e:
        logger.exception("Failed to mount UI directory: %s", str(e))
        # Don't raise - allow app to start even if UI mount fails
        logger.error("UI mount failed, but continuing startup")
else:
    logger.warning("UI directory not found at: %s", str(UI_DIR))

# Route handlers are now registered BEFORE the mount (see above)
# This ensures they take precedence over StaticFiles

# Migrations already run at the top of this file (before router imports)
# This prevents model registration conflicts when routers import models_extra

# Create tables on startup as fallback (SQLite dev only - migrations should handle this)
# Base.metadata.create_all(bind=engine)

# Add middleware (BEFORE static mounts to ensure they process requests first)
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
    # CRITICAL: Include localhost:8001 for local UI testing against production backend
    allowed_origins = [
        "http://localhost:8001",  # Local dev UI
        "http://127.0.0.1:8001",  # Local dev UI (alternative)
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite default
        "https://app.nerava.app",  # Production frontend
        "https://www.nerava.app",  # Production frontend (www)
    ]
    
    # CRITICAL: If FRONTEND_URL is set with a path (e.g., "http://localhost:8001/app"),
    # extract just the origin (scheme://host:port) for CORS
    # CORS origins must be exactly scheme://host[:port] - NO PATH
    if hasattr(settings, 'FRONTEND_URL') and settings.FRONTEND_URL:
        from urllib.parse import urlparse
        parsed = urlparse(settings.FRONTEND_URL)
        frontend_origin = f"{parsed.scheme}://{parsed.netloc}"
        if frontend_origin not in allowed_origins:
            allowed_origins.append(frontend_origin)
            logger.info("Added FRONTEND_URL origin to CORS: %s (extracted from %s)", frontend_origin, settings.FRONTEND_URL)
    
    # Note: Vercel domains will be handled by custom CORS middleware below
else:
    # Split by comma and strip whitespace
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# CRITICAL: CORS must be on the real app
# Log the exact origins we're allowing for debugging
final_origins = allowed_origins + [
    "https://www.nerava.network",
    "https://nerava.network",
]
print(f">>>> CORS allowed origins: {final_origins} <<<<", flush=True)
logger.info(">>>> CORS allowed origins: %s <<<<", final_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|https://web-production-.*\.up\.railway\.app|https://.*\.nerava\.network",
    allow_origins=final_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(">>>> CORSMiddleware added successfully <<<<", flush=True)
logger.info(">>>> CORSMiddleware added successfully <<<<")

# Mount /static for verify assets (AFTER middleware)
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists() and STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=False), name="static")
    logger.info("Mounted /static from directory: %s", str(STATIC_DIR))

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

# Canonical v1 API routers (promoted from Domain Charge Party MVP)
# These are the production endpoints that the PWA uses
from .routers import (
    auth_domain,
    drivers_domain,
    merchants_domain,
    admin_domain,
    nova_domain
)

# Stripe router (optional - only load if stripe package is available)
try:
    from .routers import stripe_domain
    STRIPE_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    logger.warning(f"Stripe router not available (stripe package not installed): {e}")
    STRIPE_AVAILABLE = False
    stripe_domain = None

# These are now the canonical /v1/* endpoints (no /domain/ prefix)
app.include_router(auth_domain.router)  # /v1/auth/*
app.include_router(drivers_domain.router)  # /v1/drivers/* (includes /merchants/nearby)
app.include_router(merchants_domain.router)  # /v1/merchants/*
if STRIPE_AVAILABLE:
    app.include_router(stripe_domain.router)  # /v1/stripe/*
app.include_router(admin_domain.router)  # /v1/admin/*
app.include_router(nova_domain.router)  # /v1/nova/*

# EV/Smartcar integration
app.include_router(ev_smartcar.router)  # /v1/ev/* and /oauth/smartcar/callback

# Debug router for logging verification
from fastapi import APIRouter as DebugRouter
debug_router = DebugRouter()

@debug_router.get("/v1/debug/log-test")
async def debug_log_test():
    """Test endpoint to verify logging is working in Railway"""
    logger.info("DEBUG LOG TEST endpoint hit")
    # Intentionally raise an error to generate a traceback in logs
    from fastapi import HTTPException
    raise HTTPException(status_code=500, detail="Intentional test error for logging")

app.include_router(debug_router)

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
    """Global exception handler for unhandled errors"""
    # Skip exception handling for static file paths - let FastAPI/Starlette handle them
    # IMPORTANT: StaticFiles should handle its own errors (404 for missing files, etc.)
    path = request.url.path
    if path.startswith("/app/") or path.startswith("/static/"):
        # For static files, don't catch exceptions - let them propagate naturally
        # This allows StaticFiles to return proper 404 for missing files
        # and prevents our handler from converting errors to 500 JSON responses
        logger.warning(f"Exception in static file request {path}: {type(exc).__name__}: {exc}")
        # Re-raise immediately - don't process further
        # This allows FastAPI/Starlette to handle the error naturally
        raise exc
    
    import traceback
    error_detail = str(exc)
    error_traceback = traceback.format_exc()
    logger.error(f"Unhandled exception: {error_detail}\n{error_traceback}", exc_info=True)
    """Global exception handler to ensure CORS headers are always set."""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Re-raise HTTPException to use existing handlers
    if isinstance(exc, HTTPException):
        raise exc
    
    # For other exceptions, return a 500 with proper CORS headers
    from fastapi.responses import JSONResponse
    error_message = str(exc) if exc else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {error_message}"},
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
