# server/main_simple.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.db import Base, engine
from src.seed import run as seed_run
from sqlalchemy import text
import os
from src.routes_explore import router as explore
from src.routes_earn import router as earn
from src.routes_activity_wallet_me import router as awm
from src.routes_dev import router as dev
from src.routes_square import router as square

app = FastAPI(title="Nerava API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

Base.metadata.create_all(bind=engine)

# Run Square migration
try:
    migrations = [
        'migrations/20251025_square_mvp.sql',
        'migrations/20251025_square_indexes.sql', 
        'migrations/20251025_reward_events.sql',
        'migrations/20251025_reward_events_index.sql'
    ]
    
    for migration_file in migrations:
        migration_path = os.path.join(os.path.dirname(__file__), migration_file)
        if os.path.exists(migration_path):
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            with engine.connect() as conn:
                conn.execute(text(migration_sql))
                conn.commit()
            print(f"✅ Migration completed: {migration_file}")
except Exception as e:
    print(f"⚠️ Migration error (tables may already exist): {e}")

seed_run()

app.include_router(explore)
app.include_router(earn)
app.include_router(awm)
app.include_router(dev)
app.include_router(square)

# Serve static files from the ui-mobile directory at root
app.mount("/", StaticFiles(directory="../../ui-mobile", html=True), name="static")

@app.get("/health") 
def health(): return {"ok": True}
