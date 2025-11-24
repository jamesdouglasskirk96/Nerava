"""
Merchant Reports API Router

Provides endpoints for merchant reporting functionality.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.db import get_db
from app.services.merchant_reports import (
    get_merchant_report,
    MerchantReport,
    DEFAULT_AVG_TICKET_CENTS
)
from app.utils.log import get_logger

router = APIRouter(prefix="/v1/merchants", tags=["merchant-reports"])
logger = get_logger(__name__)


def _parse_period(period: str) -> tuple:
    """
    Parse period string into (period_start, period_end) datetime tuple.
    
    Supported periods:
    - "week": Last 7 days (including today)
    - "30d": Last 30 days (including today)
    """
    now = datetime.utcnow()
    
    if period == "week":
        period_start = now - timedelta(days=7)
        period_end = now
    elif period == "30d":
        period_start = now - timedelta(days=30)
        period_end = now
    else:
        raise ValueError(f"Unsupported period: {period}. Use 'week' or '30d'")
    
    return period_start, period_end


@router.get("/{merchant_id}/report", response_model=MerchantReport)
def get_merchant_report_endpoint(
    merchant_id: str,
    period: str = Query("week", description="Reporting period: 'week' or '30d'"),
    avg_ticket_cents: Optional[int] = Query(None, description="Average ticket size in cents (overrides default)"),
    db: Session = Depends(get_db)
):
    """
    Get merchant report for a specific merchant.
    
    Returns aggregated metrics for the specified period:
    - EV visits (verified merchant visits)
    - Unique drivers
    - Total Nova awarded
    - Total rewards in cents
    - Implied revenue (if avg_ticket_cents provided)
    
    Auth: Currently open for pilot (TODO: add admin/auth guard)
    """
    # Parse period
    try:
        period_start, period_end = _parse_period(period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get report
    try:
        report = get_merchant_report(
            db=db,
            merchant_id=merchant_id,
            period_start=period_start,
            period_end=period_end,
            avg_ticket_cents=avg_ticket_cents
        )
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate merchant report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

