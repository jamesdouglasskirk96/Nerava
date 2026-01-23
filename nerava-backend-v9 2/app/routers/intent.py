"""
Intent Capture Router
Handles POST /v1/intent/capture endpoint
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, Charger
from app.dependencies_domain import get_current_user
from app.schemas.intent import (
    CaptureIntentRequest,
    CaptureIntentResponse,
    ChargerSummary,
    MerchantSummary,
    NextActions,
)
from app.services.intent_service import (
    create_intent_session,
    get_merchants_for_intent,
    requires_vehicle_onboarding,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/intent", tags=["intent"])


@router.post(
    "/capture",
    response_model=CaptureIntentResponse,
    summary="Capture charging intent",
    description="""
    Capture user intent based on location and charger proximity.
    
    This is the primary endpoint for the Nerava Network production launch.
    It validates location accuracy, finds the nearest public charger, assigns a confidence tier,
    and returns nearby walkable merchants or a fallback message.
    
    Confidence Tiers:
    - Tier A: Charger within ~120m (high confidence)
    - Tier B: Charger within ~400m (medium confidence)
    - Tier C: No charger nearby (returns fallback message)
    
    If Tier A or B, searches Google Places API for nearby merchants within 800m radius.
    """
)
async def capture_intent(
    request: CaptureIntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Capture user intent based on location and charger proximity.
    
    Validates location accuracy, finds nearest charger, assigns confidence tier,
    and returns nearby merchants or fallback message.
    """
    try:
        # Parse client timestamp if provided
        client_ts = None
        if request.client_ts:
            try:
                client_ts = datetime.fromisoformat(request.client_ts.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Failed to parse client_ts: {e}")
        
        # Create intent session
        session = await create_intent_session(
            db=db,
            user_id=current_user.id,
            lat=request.lat,
            lng=request.lng,
            accuracy_m=request.accuracy_m,
            client_ts=client_ts,
            source="web",
        )
        
        # Get charger summary if charger found
        charger_summary = None
        if session.charger_id:
            charger = db.query(Charger).filter(Charger.id == session.charger_id).first()
            if charger:
                charger_summary = ChargerSummary(
                    id=charger.id,
                    name=charger.name,
                    distance_m=round(session.charger_distance_m or 0),
                    network_name=charger.network_name,
                )
        
        # Get merchants based on confidence tier
        merchants = []
        fallback_message = None
        
        if session.confidence_tier in ["A", "B"]:
            # Search for merchants
            merchants_data = await get_merchants_for_intent(
                db=db,
                lat=request.lat,
                lng=request.lng,
                confidence_tier=session.confidence_tier,
            )
            
            # Transform to MerchantSummary
            merchants = [
                MerchantSummary(
                    place_id=m.get("place_id", ""),
                    name=m.get("name", ""),
                    lat=m.get("lat", 0),
                    lng=m.get("lng", 0),
                    distance_m=m.get("distance_m", 0),
                    types=m.get("types", []),
                    photo_url=m.get("photo_url"),
                    icon_url=m.get("icon_url"),
                    badges=m.get("badges"),
                    daily_cap_cents=m.get("daily_cap_cents"),
                )
                for m in merchants_data
            ]
        else:
            # Tier C: Return fallback message
            from app.core.copy import TIER_C_FALLBACK_COPY
            fallback_message = TIER_C_FALLBACK_COPY
        
        # Check if vehicle onboarding is required
        require_onboarding = requires_vehicle_onboarding(db, current_user.id, session.confidence_tier)
        
        # Build response
        response = CaptureIntentResponse(
            session_id=session.id,
            confidence_tier=session.confidence_tier,
            charger_summary=charger_summary,
            merchants=merchants,
            fallback_message=fallback_message,
            next_actions=NextActions(
                request_wallet_pass=False,  # Not implemented yet
                require_vehicle_onboarding=require_onboarding,
            ),
        )
        
        logger.info(
            f"Intent captured: session={session.id}, tier={session.confidence_tier}, "
            f"merchants={len(merchants)}, onboarding_required={require_onboarding}"
        )
        
        return response
        
    except ValueError as e:
        # Location accuracy validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error capturing intent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture intent",
        )

