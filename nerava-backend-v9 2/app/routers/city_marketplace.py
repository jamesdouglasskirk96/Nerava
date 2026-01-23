from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
import logging
import uuid
from app.core.config import flag_enabled
from app.services.city_marketplace import get_impact

router = APIRouter(prefix="/v1/city", tags=["city-marketplace"])
logger = logging.getLogger(__name__)

@router.get("/impact")
async def get_city_impact(
    city_slug: str = Query(..., description="City slug (e.g., austin)"),
    # TODO: Add auth dependency when available
    # current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get city impact data with MWh saved, rewards paid, and leaderboard"""
    
    # Check feature flag
    if not flag_enabled("feature_city_marketplace"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = str(uuid.uuid4())
    logger.info(f"city_impact_request", extra={
        "trace_id": trace_id,
        "route": "city_impact",
        "city_slug": city_slug
    })
    
    try:
        result = get_impact(city_slug)
        
        logger.info(f"city_impact_success", extra={
            "trace_id": trace_id,
            "route": "city_impact",
            "city_slug": city_slug
        })
        
        return result
        
    except Exception as e:
        logger.error(f"city_impact_error", extra={
            "trace_id": trace_id,
            "route": "city_impact",
            "city_slug": city_slug,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
