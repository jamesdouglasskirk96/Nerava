# app/routers/merchants.py
from fastapi import APIRouter, Query
from typing import Optional
from ..services.merchants_google import search_nearby

router = APIRouter(prefix="/v1/merchants", tags=["merchants"])

@router.get("/nearby")
def merchants_nearby(
    lat: float,
    lng: float,
    radius_m: int = 600,
    max_results: int = 12,
    prefs: Optional[str] = Query(default=None),
    hub_id: Optional[str] = Query(default="hub_unknown")
):
    pref_list = [p.strip() for p in (prefs or "").split(",") if p.strip()]
    return search_nearby(lat=lat, lng=lng, radius_m=radius_m, limit=max_results, prefs=pref_list, hub_id=hub_id)
