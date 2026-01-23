"""
Exclusive Session Router
Handles POST /v1/exclusive/activate, POST /v1/exclusive/complete, GET /v1/exclusive/active
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_db
from app.models import User
from app.models.while_you_charge import Charger, Merchant
from app.models.exclusive_session import ExclusiveSession, ExclusiveSessionStatus
from app.dependencies.driver import get_current_driver, get_current_driver_optional
from app.services.geo import haversine_m
from app.core.config import settings
from app.utils.exclusive_logging import log_event
from app.services.analytics import get_analytics_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/exclusive", tags=["exclusive"])

# Constants
CHARGER_RADIUS_M = settings.CHARGER_RADIUS_M
EXCLUSIVE_DURATION_MIN = settings.EXCLUSIVE_DURATION_MIN


# Request/Response Models
class ActivateExclusiveRequest(BaseModel):
    merchant_id: Optional[str] = None
    merchant_place_id: Optional[str] = None
    charger_id: str
    charger_place_id: Optional[str] = None
    intent_session_id: Optional[str] = None
    lat: float
    lng: float
    accuracy_m: Optional[float] = None


class ExclusiveSessionResponse(BaseModel):
    id: str
    merchant_id: Optional[str]
    charger_id: Optional[str]
    expires_at: str
    activated_at: str
    remaining_seconds: int


class ActivateExclusiveResponse(BaseModel):
    status: str
    exclusive_session: ExclusiveSessionResponse


class CompleteExclusiveRequest(BaseModel):
    exclusive_session_id: str
    feedback: Optional[dict] = None  # thumbs_up: bool, tags: list[str]


class CompleteExclusiveResponse(BaseModel):
    status: str


class ActiveExclusiveResponse(BaseModel):
    exclusive_session: Optional[ExclusiveSessionResponse] = None


def generate_session_id() -> str:
    """Generate a UUID string for session ID"""
    return str(uuid.uuid4())


def validate_charger_radius(
    db: Session,
    charger_id: str,
    lat: float,
    lng: float
) -> tuple:
    """
    Validate that activation location is within charger radius.
    
    Returns:
        tuple: (distance_m, is_within_radius)
    """
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if not charger:
        # Log available chargers for debugging
        all_chargers = db.query(Charger).limit(10).all()
        charger_ids = [c.id for c in all_chargers]
        logger.warning(
            f"Charger {charger_id} not found. Available chargers: {charger_ids}",
            extra={"requested_charger_id": charger_id, "available_charger_ids": charger_ids}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "charger_not_found",
                "message": f"Charger not found: {charger_id}. Please run bootstrap endpoint first.",
                "available_chargers": charger_ids[:5]  # Show first 5 for debugging
            }
        )
    
    distance_m = haversine_m(lat, lng, charger.lat, charger.lng)
    is_within_radius = distance_m <= CHARGER_RADIUS_M
    
    return distance_m, is_within_radius


@router.post("/activate", response_model=ActivateExclusiveResponse)
async def activate_exclusive(
    request: ActivateExclusiveRequest,
    http_request: Request,
    driver: User = Depends(get_current_driver),  # Required auth - OTP must be verified first
    db: Session = Depends(get_db)
):
    """
    Activate an exclusive session for a driver at a merchant/charger.
    
    Requires driver authentication (OTP must be verified first).
    
    Returns 401 if not authenticated, 428 if OTP not verified, 400 for invalid inputs, 500 for unexpected errors (with logging).
    """
    try:
        # Verify OTP authentication: user must have auth_provider="phone"
        # For v1, treat "driver JWT exists" as "OTP verified" if auth_provider is phone
        if driver.auth_provider != "phone":
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="OTP_REQUIRED"
            )
    
        # Validate merchant_id or merchant_place_id is provided
        if not request.merchant_id and not request.merchant_place_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "missing_merchant",
                    "message": "Either merchant_id or merchant_place_id is required"
                }
            )
        
        # Check for existing active session
        existing_active = db.query(ExclusiveSession).filter(
            ExclusiveSession.driver_id == driver.id,
            ExclusiveSession.status == ExclusiveSessionStatus.ACTIVE
        ).first()
        
        if existing_active:
            # Check if expired
            if existing_active.expires_at < datetime.utcnow():
                # Mark as expired
                existing_active.status = ExclusiveSessionStatus.EXPIRED
                existing_active.updated_at = datetime.utcnow()
                db.commit()
                log_event("exclusive_expired", {
                    "driver_id": driver.id,
                    "exclusive_session_id": str(existing_active.id),
                    "merchant_id": existing_active.merchant_id,
                })
            else:
                # Return existing active session
                remaining_seconds = int((existing_active.expires_at - datetime.utcnow()).total_seconds())
                return ActivateExclusiveResponse(
                    status="ACTIVE",
                    exclusive_session=ExclusiveSessionResponse(
                        id=str(existing_active.id),
                        merchant_id=existing_active.merchant_id,
                        charger_id=existing_active.charger_id,
                        expires_at=existing_active.expires_at.isoformat(),
                        activated_at=existing_active.activated_at.isoformat(),
                        remaining_seconds=max(0, remaining_seconds)
                    )
                )
        
        # Validate charger_id and location are provided
        if not request.charger_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "missing_charger_id",
                    "message": "charger_id is required"
                }
            )
        
        if request.lat is None or request.lng is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "missing_location",
                    "message": "lat and lng are required"
                }
            )
        
        # Validate charger radius
        try:
            distance_m, is_within_radius = validate_charger_radius(
                db, request.charger_id, request.lat, request.lng
            )
        except HTTPException as e:
            # Log the charger not found error with more context
            logger.warning(
                f"Charger not found: {request.charger_id}",
                extra={
                    "charger_id": request.charger_id,
                    "merchant_id": request.merchant_id,
                    "lat": request.lat,
                    "lng": request.lng
                }
            )
            # Re-raise HTTP exceptions (e.g., charger not found)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "charger_not_found",
                    "message": f"Charger not found: {request.charger_id}. Please run bootstrap endpoint first."
                }
            )
        except Exception as e:
            logger.exception(
                "Failed to validate charger radius",
                extra={
                    "charger_id": request.charger_id,
                    "lat": request.lat,
                    "lng": request.lng,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "charger_validation_failed",
                    "message": "Failed to validate charger location"
                }
            )
        
        if not is_within_radius:
            log_event("exclusive_activation_blocked", {
                "driver_id": driver.id,
                "charger_id": request.charger_id,
                "distance_m": distance_m,
                "radius_m": CHARGER_RADIUS_M,
            })
            
            # Analytics: Capture blocked activation
            request_id = getattr(http_request.state, "request_id", None)
            analytics = get_analytics_client()
            analytics.capture(
                event="server.driver.exclusive.activate.blocked",
                distinct_id=driver.public_id,
                request_id=request_id,
                user_id=driver.public_id,
                merchant_id=request.merchant_id,
                charger_id=request.charger_id,
                ip=http_request.client.host if http_request.client else None,
                user_agent=http_request.headers.get("user-agent"),
                properties={
                    "distance_m": distance_m,
                    "required_radius_m": CHARGER_RADIUS_M,
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You must be at the charger to activate. Distance: {distance_m:.0f}m, required: {CHARGER_RADIUS_M}m"
            )
        
        # Create exclusive session
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=EXCLUSIVE_DURATION_MIN)
        
        session = ExclusiveSession(
            id=generate_session_id(),
            driver_id=driver.id,
            merchant_id=request.merchant_id,
            merchant_place_id=request.merchant_place_id,
            charger_id=request.charger_id,
            charger_place_id=request.charger_place_id,
            intent_session_id=request.intent_session_id,
            status=ExclusiveSessionStatus.ACTIVE,
            activated_at=now,
            expires_at=expires_at,
            activation_lat=request.lat,
            activation_lng=request.lng,
            activation_accuracy_m=request.accuracy_m,
            activation_distance_to_charger_m=distance_m,
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Log activation event (both structured log and standard logger)
        log_event("exclusive_activated", {
            "driver_id": driver.id,
            "exclusive_session_id": str(session.id),
            "merchant_id": request.merchant_id,
            "merchant_place_id": request.merchant_place_id,
            "charger_id": request.charger_id,
            "distance_m": distance_m,
            "expires_at": expires_at.isoformat(),
        })
        logger.info(
            f"[Exclusive][Activate] Session {session.id} activated for driver {driver.id}, "
            f"merchant {request.merchant_id}, charger {request.charger_id}, "
            f"distance {distance_m:.1f}m, expires at {expires_at.isoformat()}"
        )
        
        # PostHog: Fire exclusive_activated event
        request_id = getattr(http_request.state, "request_id", None)
        analytics = get_analytics_client()
        
        # Get cluster_id if available (from charger)
        cluster_id = None
        if request.charger_id:
            from app.models.while_you_charge import ChargerCluster
            cluster = db.query(ChargerCluster).filter(ChargerCluster.charger_id == request.charger_id).first()
            if cluster:
                cluster_id = str(cluster.id)
        
        analytics.capture(
            event="exclusive_activated",
            distinct_id=driver.public_id,  # Use user.public_id as distinct_id
            request_id=request_id,
            user_id=driver.public_id,
            merchant_id=request.merchant_id,
            charger_id=request.charger_id,
            session_id=str(session.id),
            ip=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
            properties={
                "distance_m": distance_m,
                "expires_at": expires_at.isoformat(),
                "cluster_id": cluster_id,
                "merchant_id": request.merchant_id,
                "session_id": str(session.id),
                "source": "driver"
            }
        )
        
        remaining_seconds = int((expires_at - now).total_seconds())
        
        return ActivateExclusiveResponse(
            status="ACTIVE",
            exclusive_session=ExclusiveSessionResponse(
                id=str(session.id),
                merchant_id=session.merchant_id,
                charger_id=session.charger_id,
                expires_at=expires_at.isoformat(),
                activated_at=now.isoformat(),
                remaining_seconds=remaining_seconds
            )
        )
    except HTTPException:
        # Re-raise HTTP exceptions (they already have proper status codes)
        raise
    except Exception as e:
        # Log the full exception with context
        logger.exception(
            "Exclusive activation failed with unexpected error",
            extra={
                "merchant_id": request.merchant_id if request else None,
                "charger_id": request.charger_id if request else None,
                "driver_id": driver.id if driver else None,
                "lat": request.lat if request else None,
                "lng": request.lng if request else None,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        
        # Return a 500 with a clear message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "Exclusive activation failed due to an unexpected error",
                "request_id": getattr(http_request.state, "request_id", None)
            }
        )


@router.post("/complete", response_model=CompleteExclusiveResponse)
async def complete_exclusive(
    request: CompleteExclusiveRequest,
    http_request: Request,
    driver: Optional[User] = Depends(get_current_driver_optional),  # Optional auth for demo
    db: Session = Depends(get_db)
):
    """
    Complete an exclusive session.
    
    Requires:
    - Driver authentication (optional for demo)
    - Session must be ACTIVE
    - Session must belong to the driver
    """
    # Create a default driver if not authenticated (for demo)
    if not driver:
        default_driver = db.query(User).filter(User.email == "demo@nerava.local").first()
        if not default_driver:
            from app.models import User as UserModel
            default_driver = UserModel(
                id=1,
                email="demo@nerava.local",
                password_hash="demo",
                is_active=True,
                role_flags="driver",
                auth_provider="local"
            )
            db.add(default_driver)
            db.commit()
            db.refresh(default_driver)
        driver = default_driver
    
    session = db.query(ExclusiveSession).filter(
        ExclusiveSession.id == request.exclusive_session_id,
        ExclusiveSession.driver_id == driver.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exclusive session not found"
        )
    
    if session.status != ExclusiveSessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session is not active. Current status: {session.status.value}"
        )
    
    # Mark as completed
    now = datetime.utcnow()
    session.status = ExclusiveSessionStatus.COMPLETED
    session.completed_at = now
    session.updated_at = now
    db.commit()
    
    # Calculate duration
    duration_seconds = int((now - session.activated_at).total_seconds())
    
    # Log completion event (both structured log and standard logger)
    log_event("exclusive_completed", {
        "driver_id": driver.id,
        "exclusive_session_id": str(session.id),
        "merchant_id": session.merchant_id,
        "charger_id": session.charger_id,
        "duration_seconds": duration_seconds,
    })
    logger.info(
        f"[Exclusive][Complete] Session {session.id} completed for driver {driver.id}, "
        f"merchant {session.merchant_id}, duration {duration_seconds}s"
    )
    
    # Analytics: Capture completion event
    request_id = getattr(http_request.state, "request_id", None)
    analytics = get_analytics_client()
    analytics.capture(
        event="server.driver.exclusive.complete.success",
        distinct_id=driver.public_id,
        request_id=request_id,
        user_id=driver.public_id,
        merchant_id=session.merchant_id,
        charger_id=session.charger_id,
        session_id=str(session.id),
        ip=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
        properties={
            "duration_seconds": duration_seconds,
        }
    )
    
    # HubSpot: Update driver contact on completion
    # Check if this is the first completion for this driver
    completed_count = db.query(ExclusiveSession).filter(
        ExclusiveSession.driver_id == driver.id,
        ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED
    ).count()
    
    hubspot = get_hubspot_client()
    hubspot_properties = {
        "exclusive_completions": completed_count,
        "last_exclusive_completed_at": now.isoformat() + "Z",
    }
    
    # If first completion, set lifecycle stage
    if completed_count == 1:
        hubspot_properties["lifecycle_stage"] = "engaged_driver"
    
    # Update contact by phone (if available) or by driver_id
    if driver.phone:
        contact_id = hubspot.upsert_contact(
            phone=driver.phone,
            properties=hubspot_properties
        )
        if contact_id:
            hubspot.update_contact_properties(contact_id, hubspot_properties)
    
    return CompleteExclusiveResponse(status="COMPLETED")


@router.get("/active", response_model=ActiveExclusiveResponse)
async def get_active_exclusive(
    include_expired: bool = Query(False, description="Include expired sessions"),
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Get the currently active exclusive session for the driver.
    
    If session is expired, marks it as EXPIRED and returns null.
    """
    active_session = db.query(ExclusiveSession).filter(
        ExclusiveSession.driver_id == driver.id,
        ExclusiveSession.status == ExclusiveSessionStatus.ACTIVE
    ).first()
    
    if not active_session:
        return ActiveExclusiveResponse(exclusive_session=None)
    
    # Check if expired
    if active_session.expires_at < datetime.utcnow():
        # Mark as expired
        active_session.status = ExclusiveSessionStatus.EXPIRED
        active_session.updated_at = datetime.utcnow()
        db.commit()
        
        log_event("exclusive_expired", {
            "driver_id": driver.id,
            "exclusive_session_id": str(active_session.id),
            "merchant_id": active_session.merchant_id,
        })
        
        if include_expired:
            remaining_seconds = 0
        else:
            return ActiveExclusiveResponse(exclusive_session=None)
    else:
        remaining_seconds = int((active_session.expires_at - datetime.utcnow()).total_seconds())
    
    return ActiveExclusiveResponse(
        exclusive_session=ExclusiveSessionResponse(
            id=str(active_session.id),
            merchant_id=active_session.merchant_id,
            charger_id=active_session.charger_id,
            expires_at=active_session.expires_at.isoformat(),
            activated_at=active_session.activated_at.isoformat(),
            remaining_seconds=max(0, remaining_seconds)
        )
    )

