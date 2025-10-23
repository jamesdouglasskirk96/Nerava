from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.db import get_db
from app.config import settings
import redis
import asyncio

router = APIRouter()

@router.get("/healthz")
async def health_check():
    """Basic health check - always returns 200"""
    return {"ok": True}

@router.get("/readyz")
async def readiness_check(db = Depends(get_db)):
    """Readiness check - verifies dependencies"""
    try:
        # Check database
        db.execute(text("SELECT 1"))
        
        # Check Redis
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        
        return {"ok": True, "status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
