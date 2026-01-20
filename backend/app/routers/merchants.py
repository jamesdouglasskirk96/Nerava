"""
Merchant Details Router
Handles GET /v1/merchants/{merchant_id} endpoint
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.models.while_you_charge import FavoriteMerchant, Merchant as WYCMerchant
from app.schemas.merchants import MerchantDetailsResponse
from app.services.merchant_details import get_merchant_details
from app.dependencies.driver import get_current_driver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/merchants", tags=["merchants"])


# IMPORTANT: Static routes must be defined BEFORE dynamic /{merchant_id} routes
@router.get("/favorites")
def list_favorites(
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """List user's favorite merchants"""
    favorites = db.query(FavoriteMerchant).filter(
        FavoriteMerchant.user_id == driver.id
    ).all()

    merchant_ids = [f.merchant_id for f in favorites]
    merchants = db.query(WYCMerchant).filter(WYCMerchant.id.in_(merchant_ids)).all() if merchant_ids else []

    return {
        "favorites": [
            {
                "merchant_id": m.id,
                "name": m.name,
                "category": m.category,
                "photo_url": m.primary_photo_url or m.photo_url,
            }
            for m in merchants
        ]
    }


@router.post("/{merchant_id}/favorite")
def add_favorite(
    merchant_id: str,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Add a merchant to favorites (idempotent)"""
    # Verify merchant exists
    merchant = db.query(WYCMerchant).filter(WYCMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=404,
            detail="Merchant not found"
        )

    # Check if already favorited
    favorite = db.query(FavoriteMerchant).filter(
        FavoriteMerchant.user_id == driver.id,
        FavoriteMerchant.merchant_id == merchant_id
    ).first()

    if favorite:
        return {"ok": True, "is_favorite": True}

    # Create favorite
    favorite = FavoriteMerchant(
        user_id=driver.id,
        merchant_id=merchant_id
    )
    db.add(favorite)
    db.commit()

    return {"ok": True, "is_favorite": True}


@router.delete("/{merchant_id}/favorite")
def remove_favorite(
    merchant_id: str,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Remove a merchant from favorites"""
    favorite = db.query(FavoriteMerchant).filter(
        FavoriteMerchant.user_id == driver.id,
        FavoriteMerchant.merchant_id == merchant_id
    ).first()

    if favorite:
        db.delete(favorite)
        db.commit()

    return {"ok": True, "is_favorite": False}


@router.get("/{merchant_id}/share-link")
def get_share_link(
    merchant_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get shareable link for a merchant with optional referral param"""
    # Verify merchant exists
    merchant = db.query(WYCMerchant).filter(WYCMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=404,
            detail="Merchant not found"
        )

    # Build share URL
    from app.core.config import settings
    from app.dependencies.driver import get_current_driver_optional
    base_url = getattr(settings, 'FRONTEND_URL', 'https://app.nerava.network')
    url = f"{base_url}/merchant/{merchant_id}"

    # Try to get authenticated user (optional)
    try:
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        if not token:
            token = request.cookies.get("access_token")

        if token:
            driver = get_current_driver_optional(request, token, db)
            if driver:
                url += f"?ref={driver.public_id}"
    except:
        pass

    return {
        "url": url,
        "title": f"Check out {merchant.name}",
        "description": merchant.description or f"Visit {merchant.name} while you charge"
    }


@router.get(
    "/{merchant_id}",
    response_model=MerchantDetailsResponse,
    summary="Get merchant details",
    description="""
    Get detailed information about a merchant including:
    - Merchant info (name, category, photo, address, rating)
    - Moment info (distance, walk time, charge window fit)
    - Perk info (title, badge, description)
    - Wallet state (can add, current state)
    - Actions (add to wallet, get directions)
    
    Optionally provide session_id query param for distance calculation.
    """
)
async def get_merchant_details_endpoint(
    merchant_id: str,
    http_request: Request,
    session_id: Optional[str] = Query(None, description="Optional intent session ID for context"),
    db: Session = Depends(get_db),
):
    """
    Get merchant details for a given merchant ID.
    """
    try:
        result = await get_merchant_details(db, merchant_id, session_id)
        
        # PostHog: Fire merchant_details_viewed event
        from app.services.analytics import get_analytics_client
        analytics = get_analytics_client()
        request_id = getattr(http_request.state, "request_id", None) if hasattr(http_request, 'state') else None
        
        analytics.capture(
            event="merchant_details_viewed",
            distinct_id="anonymous",  # No user auth required for this endpoint
            request_id=request_id,
            merchant_id=merchant_id,
            ip=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent") if hasattr(http_request, 'headers') else None,
            properties={
                "source": "driver"
            }
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching merchant details for {merchant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch merchant details: {str(e)}")
