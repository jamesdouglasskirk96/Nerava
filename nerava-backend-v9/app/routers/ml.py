from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
from ..services.ml_ranker import rank_hubs_and_perks, score_hub, score_perk
from ..db import get_db
from sqlalchemy.orm import Session
from ..models import Hub, Perk

router = APIRouter(prefix="/v1/ml", tags=["ml"])

@router.get("/recommend/hubs")
async def recommend_hubs(
    user_id: str = Query(..., description="User ID"),
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    limit: int = Query(5, description="Number of recommendations"),
    db: Session = get_db()
):
    """Get personalized hub recommendations for a user."""
    try:
        # Get all hubs (in a real app, you'd filter by proximity, availability, etc.)
        hubs = db.query(Hub).limit(20).all()
        
        # Convert to dict format
        hub_data = [
            {
                'id': hub.id,
                'name': hub.name,
                'lat': hub.lat,
                'lng': hub.lng,
                'city': hub.city,
                'state': hub.state
            }
            for hub in hubs
        ]
        
        # Get recommendations
        result = rank_hubs_and_perks(user_id, lat, lng, hub_data, [])
        
        return {
            'user_id': user_id,
            'recommendations': result['ranked_hubs'][:limit],
            'context': result['user_context']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@router.get("/recommend/perks")
async def recommend_perks(
    user_id: str = Query(..., description="User ID"),
    hub_id: str = Query(..., description="Hub ID"),
    limit: int = Query(3, description="Number of recommendations"),
    db: Session = get_db()
):
    """Get personalized perk recommendations for a user at a specific hub."""
    try:
        # Get perks for the hub
        perks = db.query(Perk).filter(Perk.hub_id == hub_id).limit(10).all()
        
        # Convert to dict format
        perk_data = [
            {
                'id': perk.id,
                'name': perk.name,
                'description': perk.description,
                'value_cents': perk.value_cents,
                'hub_id': perk.hub_id
            }
            for perk in perks
        ]
        
        # Get hub location for context
        hub = db.query(Hub).filter(Hub.id == hub_id).first()
        if not hub:
            raise HTTPException(status_code=404, detail="Hub not found")
        
        # Get recommendations (using hub location as user location for simplicity)
        result = rank_hubs_and_perks(user_id, hub.lat, hub.lng, [], perk_data)
        
        return {
            'user_id': user_id,
            'hub_id': hub_id,
            'recommendations': result['ranked_perks'][:limit],
            'context': result['user_context']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Perk recommendation failed: {str(e)}")

@router.get("/score/hub")
async def score_hub_endpoint(
    hub_id: str = Query(..., description="Hub ID"),
    user_id: str = Query(..., description="User ID"),
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    db: Session = get_db()
):
    """Get a score for a specific hub."""
    try:
        hub = db.query(Hub).filter(Hub.id == hub_id).first()
        if not hub:
            raise HTTPException(status_code=404, detail="Hub not found")
        
        hub_data = {
            'id': hub.id,
            'name': hub.name,
            'lat': hub.lat,
            'lng': hub.lng,
            'city': hub.city,
            'state': hub.state
        }
        
        context = {'user_lat': lat, 'user_lng': lng}
        score = score_hub(hub_data, user_id, context)
        
        return {
            'hub_id': hub_id,
            'score': score,
            'reason': f"Hub scored based on location, rewards, and social factors"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")
