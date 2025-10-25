from fastapi import APIRouter

router = APIRouter(tags=["hubs"])

@router.get("/recommended")
def recommended():
    # simple static recommendation; front-end still has its own fallback
    return {"id":"fallback_hub","name":"Nerava Hub","lat":30.2672,"lng":-97.7431}

@router.get("/recommend")
def recommend():
    # Alias for /recommended to match frontend expectations
    return {"id":"fallback_hub","name":"Nerava Hub","lat":30.2672,"lng":-97.7431}