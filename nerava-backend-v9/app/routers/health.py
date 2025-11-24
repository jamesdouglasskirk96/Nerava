from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db import engine
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
def health():
    """
    Basic health check endpoint.
    
    Returns:
        {
            "status": "ok",
            "db": "ok"
        }
    """
    try:
        # Test database connection with a trivial query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return {
            "status": "ok",
            "db": "ok"
        }
    except Exception:
        # Return 500 on database failure
        raise HTTPException(status_code=500, detail="Database connection failed")

@router.get("/healthz")
async def healthz():
    """Detailed health check with database connectivity (legacy endpoint)"""
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
