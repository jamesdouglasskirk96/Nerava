"""
Merchant API endpoints (authenticated by API key)
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime

from app.db import get_db
from app.services.merchant_analytics import merchant_summary, merchant_offers
from app.utils.log import get_logger

router = APIRouter(prefix="/v1/merchant", tags=["merchant"])

logger = get_logger(__name__)


def get_merchant_from_key(
    x_merchant_key: Optional[str] = Header(None, alias="X-Merchant-Key"),
    db: Session = Depends(get_db)
) -> int:
    """
    Resolve merchant_id from API key header.
    Raises 401 if key is missing or invalid.
    """
    if not x_merchant_key:
        raise HTTPException(status_code=401, detail="Missing X-Merchant-Key header")
    
    result = db.execute(text("""
        SELECT id FROM merchants WHERE api_key = :api_key LIMIT 1
    """), {"api_key": x_merchant_key}).first()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid merchant API key")
    
    return int(result[0])


@router.get("/summary")
async def get_merchant_summary(
    merchant_id: Optional[int] = Query(None),
    x_merchant_key: Optional[str] = Header(None, alias="X-Merchant-Key"),
    db: Session = Depends(get_db)
):
    """
    Get merchant analytics summary.
    
    Authenticated via X-Merchant-Key header OR merchant_id query param (for UI).
    """
    if x_merchant_key:
        # API key takes precedence
        resolved_merchant_id = get_merchant_from_key(x_merchant_key, db)
        # If merchant_id also provided, it must match
        if merchant_id and merchant_id != resolved_merchant_id:
            raise HTTPException(status_code=403, detail="Merchant ID mismatch")
    elif merchant_id:
        # Allow query param for UI access (no key required)
        resolved_merchant_id = merchant_id
    else:
        raise HTTPException(status_code=401, detail="Missing authentication (X-Merchant-Key header or merchant_id query param)")
    
    summary = merchant_summary(db, resolved_merchant_id)
    return summary


@router.get("/offers")
async def get_merchant_offers(
    merchant_id: Optional[int] = Query(None),
    x_merchant_key: Optional[str] = Header(None, alias="X-Merchant-Key"),
    db: Session = Depends(get_db)
):
    """
    Get local and external offers for a merchant.
    
    Authenticated via X-Merchant-Key header OR merchant_id query param (for UI).
    """
    if x_merchant_key:
        resolved_merchant_id = get_merchant_from_key(x_merchant_key, db)
        if merchant_id and merchant_id != resolved_merchant_id:
            raise HTTPException(status_code=403, detail="Merchant ID mismatch")
    elif merchant_id:
        resolved_merchant_id = merchant_id
    else:
        raise HTTPException(status_code=401, detail="Missing authentication (X-Merchant-Key header or merchant_id query param)")
    
    offers = merchant_offers(db, resolved_merchant_id)
    return offers

