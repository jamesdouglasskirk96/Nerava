from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
from ..services.merchant_analytics import aggregate_per_merchant, get_top_merchants
from ..db import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/v1/merchant", tags=["merchant"])

@router.get("/insights")
async def get_merchant_insights(
    merchant_id: Optional[str] = Query(None, description="Merchant ID (optional)"),
    period: str = Query("month", description="Time period: month, week, or day"),
    db: Session = get_db()
):
    """Get merchant analytics insights."""
    try:
        insights = aggregate_per_merchant(db, period=period, merchant_id=merchant_id)
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

@router.get("/insights/top")
async def get_top_merchants_endpoint(
    limit: int = Query(10, description="Number of top merchants to return"),
    period: str = Query("month", description="Time period: month, week, or day"),
    db: Session = get_db()
):
    """Get top performing merchants."""
    try:
        top_merchants = get_top_merchants(db, limit=limit, period=period)
        return {
            'period': period,
            'limit': limit,
            'merchants': top_merchants
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top merchants: {str(e)}")

@router.get("/dashboard")
async def get_merchant_dashboard(
    merchant_id: str = Query(..., description="Merchant ID"),
    db: Session = get_db()
):
    """Get comprehensive dashboard data for a merchant."""
    try:
        # Get insights for different periods
        monthly = aggregate_per_merchant(db, period='month', merchant_id=merchant_id)
        weekly = aggregate_per_merchant(db, period='week', merchant_id=merchant_id)
        daily = aggregate_per_merchant(db, period='day', merchant_id=merchant_id)
        
        return {
            'merchant_id': merchant_id,
            'periods': {
                'month': monthly,
                'week': weekly,
                'day': daily
            },
            'summary': {
                'total_events_all_time': monthly['metrics']['total_events'],
                'unique_users_all_time': monthly['metrics']['unique_users'],
                'total_rewards_paid': monthly['metrics']['total_net_cents'],
                'co_fund_contribution': monthly['metrics']['co_fund_paid'],
                'estimated_incremental_spend': monthly['metrics']['estimated_incremental_spend']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")
