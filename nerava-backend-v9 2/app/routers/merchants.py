"""
Merchant Details Router
Handles GET /v1/merchants/{merchant_id} endpoint
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.merchants import MerchantDetailsResponse
from app.services.merchant_details import get_merchant_details
from app.models.while_you_charge import MerchantFavorite, Merchant
from app.dependencies.driver import get_current_driver_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/merchants", tags=["merchants"])


@router.get("/favorites")
async def get_favorites(
    current_user = Depends(get_current_driver_optional),
    db: Session = Depends(get_db)
):
    """Get user's favorite merchants"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    favorites = db.query(MerchantFavorite).filter(
        MerchantFavorite.user_id == current_user.id
    ).all()

    if not favorites:
        return []

    merchant_ids = [f.merchant_id for f in favorites]
    merchants = db.query(Merchant).filter(Merchant.id.in_(merchant_ids)).all()

    return [
        {
            "id": m.id,
            "name": m.name,
            "category": m.category,
            "photo_url": m.photo_url or getattr(m, 'primary_photo_url', None) or "",
            "address": m.address,
            "rating": m.rating
        }
        for m in merchants
    ]


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
    session_id: Optional[str] = Query(None, description="Optional intent session ID for context"),
    db: Session = Depends(get_db),
):
    """
    Get merchant details for a given merchant ID.
    """
    try:
        result = get_merchant_details(db, merchant_id, session_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching merchant details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch merchant details")
