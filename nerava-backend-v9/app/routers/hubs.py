# app/routers/hubs.py
from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from ..services import hubs_dynamic

router = APIRouter()  # main.py already mounts with prefix="/v1/hubs"

@router.get("/nearby")
async def hubs_nearby(
    lat: float,
    lng: float,
    radius_km: float = 2.0,
    max_results: int = 10
):
    hubs = await hubs_dynamic.build_dynamic_hubs(lat=lat, lng=lng, radius_km=radius_km, max_results=max_results)
    for h in hubs:
        h["merchants_url"] = f"/v1/merchants/nearby?lat={h['lat']}&lng={h['lng']}&radius_m=600&max_results=12"
    return hubs

@router.get("/recommend")
async def hubs_recommend(
    lat: float,
    lng: float,
    radius_km: float = 2.0,
    prefs: Optional[str] = None
):
    hubs = await hubs_dynamic.build_dynamic_hubs(lat=lat, lng=lng, radius_km=radius_km, max_results=8)
    pref_list = [p.strip() for p in (prefs or "").split(",") if p.strip()]
    scored = [hubs_dynamic.score_hub(h, pref_list) for h in hubs]
    if not scored:
        return {}
    best = sorted(scored, key=lambda x: x.get("score", 0.0), reverse=True)[0]
    best["merchants_url"] = f"/v1/merchants/nearby?lat={best['lat']}&lng={best['lng']}&radius_m=600&max_results=12"
    return best

@router.get("/hydrated")
async def hubs_hydrated(
    lat: float,
    lng: float,
    radius_km: float = 2.0,
    max_results: int = 8,
    prefs: Optional[str] = Query(default=None, description="comma list like coffee_bakery,quick_bite")
):
    pref_list = [p.strip() for p in (prefs or "").split(",") if p.strip()]
    hubs = await hubs_dynamic.build_dynamic_hubs(lat=lat, lng=lng, radius_km=radius_km, max_results=max_results)
    hydrated = [hubs_dynamic.hydrate_hub(h, lat, lng, pref_list) for h in hubs]
    return hydrated

# Apple Maps-style summary endpoint
class ModelInfo(BaseModel):
    vendor: str
    speed_kw: int
    count: int

class HubSummary(BaseModel):
    hub_id: str
    name: str
    chargers: int
    pricing: str
    distance_mi: float
    phone: Optional[str] = "+1 (877) 798-3752"
    website: Optional[str] = "https://tesla.com/supercharger"
    maps_url: Optional[str] = "https://maps.apple.com/?q=Tesla+Supercharger"
    models: List[ModelInfo] = [ModelInfo(vendor="Tesla", speed_kw=250, count=12)]

@router.get("/summary", response_model=HubSummary)
async def summary(lat: float = Query(...), lng: float = Query(...)):
    return HubSummary(
        hub_id="hub_domain_A",
        name="Tesla Supercharger",
        chargers=12,
        pricing="Paid",
        distance_mi=3.4,
    )
