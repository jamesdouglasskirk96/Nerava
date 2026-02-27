"""
Intent Capture Router
Handles POST /v1/intent/capture endpoint
"""
import logging
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from cachetools import TTLCache

from app.db import get_db
from app.models import User, Charger
from app.dependencies_domain import get_current_user_optional
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
    find_nearest_chargers,
)
from app.services.analytics import get_analytics_client
from fastapi import Request

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter for intent capture endpoint
# Key: client IP, Value: (last_request_time, request_count_in_window)
# Bounded TTLCache: max 10,000 IPs, entries expire after 10 seconds
_intent_rate_limit: TTLCache = TTLCache(maxsize=10000, ttl=10.0)
RATE_LIMIT_WINDOW_SEC = 5.0  # Window in seconds
RATE_LIMIT_MAX_REQUESTS = 2  # Max requests per window per IP

# Response cache - cache responses by rounded coordinates
# This reduces load when clients repeatedly request the same location
# Bounded TTLCache: max 1,000 entries, auto-expire after 60 seconds
_response_cache: TTLCache = TTLCache(maxsize=1000, ttl=60.0)
RESPONSE_CACHE_TTL_SEC = 60.0  # Cache responses for 60 seconds

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
    
    Confidence Tiers (metadata only — merchants always returned):
    - Tier A: Charger within ~120m (high confidence)
    - Tier B: Charger within ~400m (medium confidence)
    - Tier C: No charger nearby (includes fallback message alongside merchants)

    Always searches for nearby merchants within 800m radius regardless of tier.
    """
)
async def capture_intent(
    request: CaptureIntentRequest,
    http_request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Capture user intent based on location and charger proximity.

    Validates location accuracy, finds nearest charger, assigns confidence tier,
    and returns nearby merchants or fallback message.
    """
    now = time.time()

    # Response cache check - return cached response for same coordinates
    # Round coordinates to 4 decimal places (~11m precision) to improve cache hits
    rounded_lat = round(request.lat, 4)
    rounded_lng = round(request.lng, 4)
    cache_key = f"{rounded_lat},{rounded_lng}"

    if cache_key in _response_cache:
        cached_response = _response_cache[cache_key]
        logger.debug(f"Intent capture cache hit for {cache_key}")
        return CaptureIntentResponse(**cached_response)

    # Rate limiting check - protect against infinite fetch loops from buggy clients
    # Uses sliding window: max 2 requests per 5 seconds per IP
    # Get real client IP from X-Forwarded-For header (behind load balancer)
    forwarded_for = http_request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (http_request.client.host if http_request.client else "unknown")
    window_start, request_count = _intent_rate_limit.get(client_ip, (0.0, 0))

    # Check if we're still in the same window
    if now - window_start < RATE_LIMIT_WINDOW_SEC:
        request_count += 1
        if request_count > RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for {client_ip}: {request_count} requests in window")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait before retrying."
            )
        _intent_rate_limit[client_ip] = (window_start, request_count)
    else:
        # New window - reset counter
        _intent_rate_limit[client_ip] = (now, 1)

    try:
        # Parse client timestamp if provided
        client_ts = None
        if request.client_ts:
            try:
                client_ts = datetime.fromisoformat(request.client_ts.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Failed to parse client_ts: {e}")

        # For anonymous users, skip intent session creation but still find chargers/merchants
        session = None
        confidence_tier = "C"
        charger_summary = None
        charger_id = None
        charger_distance_m = None

        # Find nearest chargers (works for both auth and anon)
        from app.services.intent_service import find_nearest_charger, assign_confidence_tier, validate_location_accuracy

        if not validate_location_accuracy(request.accuracy_m):
            from app.core.config import settings
            raise ValueError(f"Location accuracy {request.accuracy_m}m exceeds threshold {settings.LOCATION_ACCURACY_THRESHOLD_M}m")

        # Find up to 5 nearest chargers within 25km
        charger_results = find_nearest_chargers(db, request.lat, request.lng, radius_m=25000, limit=5)
        chargers_list = []

        for charger, distance in charger_results:
            chargers_list.append(ChargerSummary(
                id=charger.id,
                name=charger.name,
                distance_m=round(distance),
                network_name=charger.network_name,
            ))

        # Enrich chargers with campaign reward info
        try:
            from app.services.campaign_service import CampaignService
            from app.services.geo import haversine_m as campaign_haversine
            active_campaigns = CampaignService.get_active_campaigns(db)
            for cs in chargers_list:
                best_reward = 0
                for camp in active_campaigns:
                    # Check charger_id targeting
                    if camp.rule_charger_ids and cs.id not in camp.rule_charger_ids:
                        continue
                    # Check geo targeting
                    if camp.rule_geo_center_lat and camp.rule_geo_center_lng and camp.rule_geo_radius_m:
                        # Use charger's actual location from results
                        charger_obj = next((c for c, _ in charger_results if c.id == cs.id), None)
                        if charger_obj:
                            dist = campaign_haversine(
                                charger_obj.lat, charger_obj.lng,
                                camp.rule_geo_center_lat, camp.rule_geo_center_lng
                            )
                            if dist > camp.rule_geo_radius_m:
                                continue
                    if camp.cost_per_session_cents > best_reward:
                        best_reward = camp.cost_per_session_cents
                if best_reward > 0:
                    cs.campaign_reward_cents = best_reward
        except Exception as e:
            logger.warning(f"Failed to enrich chargers with campaign rewards: {e}")
            try:
                db.rollback()
            except Exception:
                pass

        # Use the nearest charger for backward compatibility and confidence tier
        if charger_results:
            charger, distance = charger_results[0]
            charger_id = charger.id
            charger_distance_m = distance
            confidence_tier = assign_confidence_tier(distance)
            charger_summary = chargers_list[0] if chargers_list else None
        # Note: charger_summary can be None if no chargers exist in database
        # In that case, confidence_tier remains "C" and fallback_message will be set below

        # Create intent session only for authenticated users
        if current_user:
            session = await create_intent_session(
                db=db,
                user_id=current_user.id,
                lat=request.lat,
                lng=request.lng,
                accuracy_m=request.accuracy_m,
                client_ts=client_ts,
                source="web",
            )
            confidence_tier = session.confidence_tier

        # Always search for merchants regardless of confidence tier
        fallback_message = None

        merchants_data = await get_merchants_for_intent(
            db=db,
            lat=request.lat,
            lng=request.lng,
            confidence_tier=confidence_tier,
            charger_id=charger_id,  # Pass charger_id to use ChargerMerchant links
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

        # Tier C: include fallback message as additional info alongside merchants
        if confidence_tier == "C":
            from app.core.copy import TIER_C_FALLBACK_COPY
            fallback_message = TIER_C_FALLBACK_COPY

        # Check if vehicle onboarding is required (only for authenticated users)
        require_onboarding = False
        if current_user:
            require_onboarding = requires_vehicle_onboarding(db, current_user.id, confidence_tier)

        # Build response
        session_id = session.id if session else None
        response = CaptureIntentResponse(
            session_id=session_id,
            confidence_tier=confidence_tier,
            charger_summary=charger_summary,
            chargers=chargers_list,  # Up to 5 nearest chargers
            merchants=merchants,
            fallback_message=fallback_message,
            next_actions=NextActions(
                request_wallet_pass=False,  # Not implemented yet
                require_vehicle_onboarding=require_onboarding,
            ),
        )

        logger.info(
            f"Intent captured: session={session_id}, tier={confidence_tier}, "
            f"chargers={len(chargers_list)}, merchants={len(merchants)}, "
            f"onboarding_required={require_onboarding}, authenticated={current_user is not None}"
        )
        
        # Analytics: Capture intent capture success
        request_id = getattr(http_request.state, "request_id", None)
        analytics = get_analytics_client()
        distinct_id = current_user.public_id if current_user else "anonymous"
        analytics.capture(
            event="server.driver.intent.capture.success",
            distinct_id=distinct_id,
            request_id=request_id,
            user_id=current_user.public_id if current_user else None,
            session_id=str(session_id) if session_id else None,
            charger_id=charger_id,
            lat=request.lat,
            lng=request.lng,
            accuracy_m=request.accuracy_m,
            ip=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
            properties={
                "location_accuracy": request.accuracy_m,
                "charger_count": len(chargers_list),
                "merchant_count": len(merchants),
                "confidence_tier": confidence_tier,
                "is_anonymous": current_user is None,
            }
        )

        # Cache the response for future requests with same coordinates
        # Only cache anonymous responses (session_id is None)
        if session_id is None:
            _response_cache[cache_key] = response.model_dump()

        return response
        
    except ValueError as e:
        # Location accuracy validation error
        # Analytics: Capture intent capture failure
        request_id = getattr(http_request.state, "request_id", None)
        analytics = get_analytics_client()
        distinct_id = current_user.public_id if current_user else "anonymous"
        analytics.capture(
            event="server.driver.intent.capture.fail",
            distinct_id=distinct_id,
            request_id=request_id,
            user_id=current_user.public_id if current_user else None,
            ip=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
            lat=request.lat,
            lng=request.lng,
            accuracy_m=request.accuracy_m,
            properties={
                "error": str(e),
                "location_accuracy": request.accuracy_m,
                "is_anonymous": current_user is None,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error capturing intent: {e}", exc_info=True)
        # Analytics: Capture intent capture failure
        request_id = getattr(http_request.state, "request_id", None)
        analytics = get_analytics_client()
        distinct_id = current_user.public_id if current_user else "anonymous"
        analytics.capture(
            event="server.driver.intent.capture.fail",
            distinct_id=distinct_id,
            request_id=request_id,
            user_id=current_user.public_id if current_user else None,
            ip=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
            lat=request.lat if request else None,
            lng=request.lng if request else None,
            accuracy_m=request.accuracy_m if request else None,
            properties={
                "error": str(e),
                "is_anonymous": current_user is None,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture intent",
        )

