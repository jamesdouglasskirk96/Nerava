from typing import Dict, Any, List
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models_extra import MerchantIntelForecast
from ..obs.obs import log_info, log_warn

def cohort_buckets(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze events to create customer cohorts using simple heuristics.
    
    Args:
        events: List of charging/transaction events with timestamps
    
    Returns:
        Dict with cohort analysis
    """
    # Simple heuristics based on hour of day and day of week
    night_owls = sum(1 for event in events 
                    if event.get("hour", 12) >= 22 or event.get("hour", 12) <= 6)
    green_commuters = sum(1 for event in events 
                         if 7 <= event.get("hour", 12) <= 9 or 17 <= event.get("hour", 12) <= 19)
    weekend_fast = sum(1 for event in events 
                      if event.get("day_of_week", 1) >= 6 and event.get("hour", 12) >= 10)
    
    return {
        "night_owls": {"count": night_owls, "avg_spend": 45.20},
        "green_commuters": {"count": green_commuters, "avg_spend": 67.80},
        "weekend_fast": {"count": weekend_fast, "avg_spend": 89.50}
    }

def forecast_footfall(merchant_id: str, horizon_hours: int) -> Dict[str, Any]:
    """
    Generate footfall forecast using deterministic placeholder logic.
    
    Args:
        merchant_id: Merchant identifier
        horizon_hours: Forecast horizon in hours
    
    Returns:
        Dict with forecast data
    """
    # TODO: Replace with proper ML model
    # For now, use deterministic patterns based on merchant_id hash
    base_visits = hash(merchant_id) % 100 + 50  # 50-149 visits
    
    # Time-based patterns
    if horizon_hours <= 24:
        expected_visits = base_visits
        confidence = 0.85
        peak_hours = ["14:00-16:00", "18:00-20:00"]
    else:
        expected_visits = base_visits * 7  # Weekly projection
        confidence = 0.72
        peak_hours = ["Weekend mornings", "Weekday evenings"]
    
    return {
        "expected_visits": expected_visits,
        "confidence": confidence,
        "peak_hours": peak_hours,
        "growth_rate": 0.12
    }

def dynamic_promos(merchant_id: str, grid_load_pct: float) -> List[Dict[str, Any]]:
    """
    Generate dynamic promotions based on grid load and merchant context.
    
    Args:
        merchant_id: Merchant identifier
        grid_load_pct: Current grid load percentage (0-100)
    
    Returns:
        List of promotion suggestions
    """
    promos = []
    
    # Grid load-based promotions
    if grid_load_pct < 70:
        promos.append({
            "id": f"grid_promo_{merchant_id}",
            "name": "Green Hour Bonus",
            "type": "time_based",
            "discount_percent": 20,
            "valid_hours": "14:00-16:00",
            "reason": "Low grid load - encourage off-peak charging"
        })
    
    if grid_load_pct > 90:
        promos.append({
            "id": f"demand_response_{merchant_id}",
            "name": "Peak Avoidance Reward",
            "type": "behavior_change",
            "discount_percent": 15,
            "valid_hours": "17:00-19:00",
            "reason": "High grid load - encourage peak avoidance"
        })
    
    # Merchant-specific promotions
    if "coffee" in merchant_id.lower():
        promos.append({
            "id": f"coffee_promo_{merchant_id}",
            "name": "$2 Coffee Coupon",
            "type": "merchant_specific",
            "discount_percent": 100,
            "max_discount_cents": 200,
            "reason": "Coffee shop partnership promotion"
        })
    
    return promos

def _load_events(merchant_id: str, lookback_days: int = 60) -> List[Dict[str, Any]]:
    """Load events for merchant analysis."""
    # TODO: Replace with actual database query
    # For now, return mock events with deterministic patterns
    events = []
    base_count = hash(merchant_id) % 50 + 20  # 20-69 events
    
    for i in range(base_count):
        hour = (i * 7 + hash(merchant_id)) % 24
        day_of_week = (i * 3 + hash(merchant_id)) % 7
        amount = 30 + (i % 20) * 2.5
        
        events.append({
            "hour": hour,
            "day_of_week": day_of_week,
            "amount": amount,
            "timestamp": datetime.utcnow() - timedelta(days=i % lookback_days)
        })
    
    return events

def _hourly_bucket(events: List[Dict[str, Any]]) -> Dict[int, int]:
    """Bucket events by hour of day."""
    buckets = {h: 0 for h in range(24)}
    for event in events:
        hour = event.get("hour", 12)
        buckets[hour] += 1
    return buckets

def _dow_bucket(events: List[Dict[str, Any]]) -> Dict[int, int]:
    """Bucket events by day of week."""
    buckets = {d: 0 for d in range(7)}
    for event in events:
        dow = event.get("day_of_week", 1)
        buckets[dow] += 1
    return buckets

def get_overview(merchant_id: str, grid_load_pct: float = 75.0, db: Session = None) -> Dict[str, Any]:
    """
    Get merchant intelligence overview with v1 logic implementation.
    
    Args:
        merchant_id: Merchant identifier
        grid_load_pct: Optional grid load percentage for dynamic promos
        db: Database session for persistence
    
    Returns:
        Dict with merchant intelligence data
    """
    start_time = datetime.utcnow()
    log_info(f"Computing merchant intel for {merchant_id}")
    
    # Load events for analysis
    events = _load_events(merchant_id, lookback_days=60)
    log_info(f"Loaded {len(events)} events for analysis")
    
    # Generate cohorts using v1 logic
    cohorts_data = cohort_buckets(events)
    cohorts = [
        {
            "name": "Night Owls",
            "size": cohorts_data["night_owls"]["count"],
            "avg_monthly_spend": cohorts_data["night_owls"]["avg_spend"],
            "retention_rate": 0.87
        },
        {
            "name": "Green Commuters", 
            "size": cohorts_data["green_commuters"]["count"],
            "avg_monthly_spend": cohorts_data["green_commuters"]["avg_spend"],
            "retention_rate": 0.92
        },
        {
            "name": "Weekend Fast",
            "size": cohorts_data["weekend_fast"]["count"],
            "avg_monthly_spend": cohorts_data["weekend_fast"]["avg_spend"],
            "retention_rate": 0.78
        }
    ]
    
    # Generate forecasts using v1 logic
    forecast_24h = forecast_footfall(merchant_id, 24)
    forecast_7d = forecast_footfall(merchant_id, 168)
    
    forecasts = {
        "next_24h": {
            "expected_visits": forecast_24h["expected_visits"],
            "confidence": forecast_24h["confidence"],
            "peak_hours": forecast_24h["peak_hours"]
        },
        "next_7d": {
            "expected_revenue_cents": forecast_7d["expected_visits"] * 500,  # $5 avg per visit
            "confidence": forecast_7d["confidence"],
            "growth_rate": forecast_7d["growth_rate"]
        }
    }
    
    # Generate dynamic promotions using v1 logic
    dynamic_promos_list = dynamic_promos(merchant_id, grid_load_pct)
    
    promos = {
        "active": [
            {
                "id": "promo_001",
                "name": "Off-Peak Bonus",
                "discount_percent": 15,
                "usage_count": 234,
                "conversion_rate": 0.23
            }
        ],
        "recommended": dynamic_promos_list
    }
    
    result = {
        "merchant_id": merchant_id,
        "cohorts": cohorts,
        "forecasts": forecasts,
        "promos": promos,
        "last_updated": datetime.utcnow().isoformat()
    }
    
    # Persist forecast if database available
    if db:
        try:
            forecast = MerchantIntelForecast(
                merchant_id=merchant_id,
                version="v1",
                inputs={"lookback_days": 60, "grid_load_pct": grid_load_pct},
                cohorts=cohorts,
                forecasts=forecasts,
                promos=promos
            )
            db.add(forecast)
            db.commit()
            log_info(f"Persisted merchant intel forecast for {merchant_id}")
        except Exception as e:
            log_warn(f"Failed to persist forecast: {e}")
            db.rollback()
    
    # Log metrics
    compute_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    log_info(f"Merchant intel compute time: {compute_time:.2f}ms")
    
    return result
