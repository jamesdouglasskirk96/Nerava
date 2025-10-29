from fastapi import APIRouter
from datetime import datetime
from app.db import engine
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
def health():
    """Basic health check endpoint"""
    return {"ok": True, "time": datetime.utcnow().isoformat()}

@router.get("/healthz")
async def healthz():
    """Detailed health check with database connectivity"""
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return {
            "ok": True,
            "database": "connected",
            "time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "ok": False,
            "database": "disconnected",
            "error": str(e),
            "time": datetime.utcnow().isoformat()
        }, 503
