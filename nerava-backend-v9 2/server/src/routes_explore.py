# server/src/routes_explore.py
from fastapi import APIRouter
router = APIRouter(prefix="/v1")

@router.get("/hubs/recommend")
def hubs_recommend():
    return {
        "origin": {"lat":30.264, "lng":-97.742},
        "dest":   {"lat":30.401, "lng":-97.725},
        "eta_min": 15,
        "network": {"name":"Tesla", "color":"#e11d48"}
    }

@router.get("/deals/nearby")
def deals_nearby():
    return {
        "id":"perk-starbucks-1",
        "merchant":"Starbucks",
        "logo":"https://logo.clearbit.com/starbucks.com",
        "address":"310 E 5th St, Austin, TX",
        "window_text":"Free coffee 2–4pm",
        "distance_text":"3 min walk",
        "station_id":"station-5th-st",
        "station_name":"Starbucks 5th St"
    }
