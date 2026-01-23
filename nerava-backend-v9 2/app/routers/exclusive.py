"""
Exclusive Session Router
Handles POST /v1/exclusive/activate, POST /v1/exclusive/complete, GET /v1/exclusive/active
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_db
from app.models import User, Charger, Merchant, ExclusiveSession, ExclusiveSessionStatus
from app.dependencies.driver import get_current_driver
from app.services.geo import haversine_m
from app.core.config import settings
from app.utils.exclusive_logging import log_event

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger not found: {charger_id}"
        )
    
    distance_m = haversine_m(lat, lng, charger.lat, charger.lng)
    is_within_radius = distance_m <= CHARGER_RADIUS_M
    
    return distance_m, is_within_radius


@router.post("/activate", response_model=ActivateExclusiveResponse)
async def activate_exclusive(
    request: ActivateExclusiveRequest,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Activate an exclusive session for a driver.
    
    Requires:
    - Driver authentication
    - Driver must be within charger radius (150m)
    - No other active session for this driver
    
    Returns:
        ActivateExclusiveResponse with session details
    """
    try:
        # Validate merchant_id or merchant_place_id is provided
        if not request.merchant_id and not request.merchant_place_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either merchant_id or merchant_place_id is required"
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
        
        # Validate charger radius
        distance_m, is_within_radius = validate_charger_radius(
            db, request.charger_id, request.lat, request.lng
        )
        
        if not is_within_radius:
            log_event("exclusive_activation_blocked", {
                "driver_id": driver.id,
                "charger_id": request.charger_id,
                "distance_m": distance_m,
                "radius_m": CHARGER_RADIUS_M,
            })
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
        
        # Log activation event
        log_event("exclusive_activated", {
            "driver_id": driver.id,
            "exclusive_session_id": str(session.id),
            "merchant_id": request.merchant_id,
            "merchant_place_id": request.merchant_place_id,
            "charger_id": request.charger_id,
            "distance_m": distance_m,
            "expires_at": expires_at.isoformat(),
        })
        
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
        # Re-raise HTTP exceptions (400, 403, etc.)
        raise
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"Error activating exclusive session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate exclusive session: {str(e)}"
        )


@router.post("/complete", response_model=CompleteExclusiveResponse)
async def complete_exclusive(
    request: CompleteExclusiveRequest,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """
    Complete an exclusive session.
    
    Requires:
    - Driver authentication
    - Session must be ACTIVE
    - Session must belong to the driver
    """
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
    
    # Log completion event
    log_event("exclusive_completed", {
        "driver_id": driver.id,
        "exclusive_session_id": str(session.id),
        "merchant_id": session.merchant_id,
        "charger_id": session.charger_id,
        "duration_seconds": duration_seconds,
    })
    
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
    try:
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
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"Error getting active exclusive session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active exclusive session: {str(e)}"
        )

