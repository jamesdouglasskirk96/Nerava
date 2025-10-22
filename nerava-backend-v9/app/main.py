from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine

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
)

# Auth + JWT preferences
from .routers.auth import router as auth_router
from .routers.user_prefs import router as prefs_router

app = FastAPI(title="Nerava Backend v9", version="0.9.0")

# Create tables on startup (SQLite dev)
Base.metadata.create_all(bind=engine)

# CORS (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
