from fastapi import FastAPI
from .db import Base, engine
from .routers.auth import router as auth_router
from .routers.user_prefs import router as prefs_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from .routers import webhooks
from .routers import webhooks
from app.routers import users, hubs, recommend, reservations, health
from app.routers import users, hubs, recommend, reservations, health
from app.routers import chargers
from app.routers import chargers
from app.routers import wallet
from app.routers import wallet
from app.routers import merchants as merchants_router
from app.routers import merchants as merchants_router
from app.routers import users_register
from app.routers import users_register
from app.routers import merchants_local
from app.routers import merchants_local


app = FastAPI(title="Nerava Backend v9", version="0.9.0")
app = FastAPI(title="Nerava Backend v9", version="0.9.0")
Base.metadata.create_all(bind=engine)


app.add_middleware(
app.add_middleware(
    CORSMiddleware,
    CORSMiddleware,
    allow_origins=["*"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_credentials=True,
    allow_methods=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_headers=["*"],
)
)


app.include_router(health.router, prefix="/v1", tags=["health"])
app.include_router(health.router, prefix="/v1", tags=["health"])
app.include_router(users.router)
app.include_router(users.router)
app.include_router(merchants_router.router)
app.include_router(merchants_router.router)
app.include_router(hubs.router, prefix="/v1/hubs", tags=["hubs"])
app.include_router(hubs.router, prefix="/v1/hubs", tags=["hubs"])
app.include_router(recommend.router, prefix="/v1", tags=["recommend"])
app.include_router(recommend.router, prefix="/v1", tags=["recommend"])
app.include_router(reservations.router, prefix="/v1/reservations", tags=["reservations"])
app.include_router(reservations.router, prefix="/v1/reservations", tags=["reservations"])
app.include_router(wallet.router)
app.include_router(wallet.router)
app.include_router(chargers.router, prefix="/v1/chargers", tags=["chargers"])
app.include_router(chargers.router, prefix="/v1/chargers", tags=["chargers"])
app.include_router(webhooks.router)
app.include_router(webhooks.router)
app.include_router(hubs.router, prefix="/v1/hubs", tags=["hubs"])
app.include_router(hubs.router, prefix="/v1/hubs", tags=["hubs"])
app.include_router(users_register.router)
app.include_router(users_register.router)
app.include_router(merchants_local.router)
app.include_router(merchants_local.router)
