# app/routers/chargers.py
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
from app.services.chargers_openmap import fetch_chargers

router = APIRouter()  # main.py mounts with prefix="/v1/chargers"

@router.get("/nearby", response_model=List[Dict[str, Any]])
async def nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(2.0, ge=0.1, le=50.0),
    max_results: int = Query(50, ge=1, le=200)
):
    try:
        items = await fetch_chargers(lat=lat, lng=lng, radius_km=radius_km, max_results=max_results)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"chargers_fetch_failed: {e}")
