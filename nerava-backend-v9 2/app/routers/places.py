from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/v1/places", tags=["places"])

class Place(BaseModel):
    id: str
    name: str
    rating: float
    source: str = "Yelp"
    photo: Optional[str] = None
    distance_mi: float

class NearbyResp(BaseModel):
    places: List[Place]

@router.get("/nearby", response_model=NearbyResp)
async def nearby(lat: float = Query(...), lng: float = Query(...), limit: int = 6):
    demo = [
        Place(id="starbucks", name="Starbucks", rating=2.5, distance_mi=0.3, photo=""),
        Place(id="pierinos", name="Pierinos", rating=4.5, distance_mi=0.5, photo=""),
        Place(id="target", name="Target", rating=4.3, distance_mi=0.8, photo=""),
        Place(id="arepitas", name="Arepitas", rating=4.6, distance_mi=0.7, photo=""),
        Place(id="tacos", name="Taco Zone", rating=4.2, distance_mi=1.1, photo=""),
        Place(id="bakery", name="Sunrise Bakery", rating=4.8, distance_mi=0.9, photo=""),
    ]
    return NearbyResp(places=demo[:limit])
