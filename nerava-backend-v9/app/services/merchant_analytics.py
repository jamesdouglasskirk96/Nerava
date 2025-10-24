from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from ..models_extra import RewardEvent, FollowerShare

def aggregate_per_merchant(db: Session, period: str = 'month', merchant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Aggregate merchant analytics for a given period.
    
    Args:
        db: Database session
        period: 'month', 'week', or 'day'
        merchant_id: Specific merchant ID (None for all)
        
    Returns:
        Dict with aggregated metrics
    """
    # Calculate date range
    now = datetime.utcnow()
    if period == 'month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    else:  # day
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Base query for reward events
    query = db.query(RewardEvent).filter(RewardEvent.created_at >= start_date)
    
    if merchant_id:
        # Filter by merchant (assuming merchant_id is in meta)
        query = query.filter(RewardEvent.meta.contains({'merchant_id': merchant_id}))
    
    events = query.all()
    
    # Calculate metrics
    total_events = len(events)
    unique_users = len(set(event.user_id for event in events))
    total_gross_cents = sum(event.gross_cents for event in events)
    total_community_cents = sum(event.community_cents for event in events)
    total_net_cents = sum(event.net_cents for event in events)
    
    # Estimate incremental spend (assume 3x multiplier on rewards)
    estimated_incremental_spend = total_net_cents * 3
    
    # Get co-fund paid (community portion)
    co_fund_paid = total_community_cents
    
    # Calculate average reward per user
    avg_reward_per_user = total_net_cents / unique_users if unique_users > 0 else 0
    
    return {
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': now.isoformat(),
        'merchant_id': merchant_id,
        'metrics': {
            'total_events': total_events,
            'unique_users': unique_users,
            'total_gross_cents': total_gross_cents,
            'total_net_cents': total_net_cents,
            'total_community_cents': total_community_cents,
            'estimated_incremental_spend': estimated_incremental_spend,
            'co_fund_paid': co_fund_paid,
            'avg_reward_per_user': avg_reward_per_user
        }
    }

def get_top_merchants(db: Session, limit: int = 10, period: str = 'month') -> List[Dict[str, Any]]:
    """
    Get top performing merchants by metrics.
    
    Args:
        db: Database session
        limit: Number of top merchants to return
        period: Time period for analysis
        
    Returns:
        List of merchant performance data
    """
    # Calculate date range
    now = datetime.utcnow()
    if period == 'month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    else:  # day
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get all events in period
    events = db.query(RewardEvent).filter(RewardEvent.created_at >= start_date).all()
    
    # Group by merchant_id (from meta)
    merchant_stats = {}
    for event in events:
        merchant_id = event.meta.get('merchant_id', 'unknown') if event.meta else 'unknown'
        
        if merchant_id not in merchant_stats:
            merchant_stats[merchant_id] = {
                'merchant_id': merchant_id,
                'total_events': 0,
                'unique_users': set(),
                'total_gross_cents': 0,
                'total_net_cents': 0,
                'total_community_cents': 0
            }
        
        stats = merchant_stats[merchant_id]
        stats['total_events'] += 1
        stats['unique_users'].add(event.user_id)
        stats['total_gross_cents'] += event.gross_cents
        stats['total_net_cents'] += event.net_cents
        stats['total_community_cents'] += event.community_cents
    
    # Convert to list and calculate final metrics
    results = []
    for merchant_id, stats in merchant_stats.items():
        results.append({
            'merchant_id': merchant_id,
            'total_events': stats['total_events'],
            'unique_users': len(stats['unique_users']),
            'total_gross_cents': stats['total_gross_cents'],
            'total_net_cents': stats['total_net_cents'],
            'total_community_cents': stats['total_community_cents'],
            'estimated_incremental_spend': stats['total_net_cents'] * 3,
            'co_fund_paid': stats['total_community_cents']
        })
    
    # Sort by total events (could be other metrics)
    results.sort(key=lambda x: x['total_events'], reverse=True)
    
    return results[:limit]
