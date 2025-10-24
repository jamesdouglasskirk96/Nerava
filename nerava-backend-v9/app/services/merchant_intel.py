from typing import Dict, Any, List
import uuid
from datetime import datetime, timedelta

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

def get_overview(merchant_id: str, grid_load_pct: float = 75.0) -> Dict[str, Any]:
    """
    Get merchant intelligence overview with cohorts, forecasts, and promos.
    
    Args:
        merchant_id: Merchant identifier
        grid_load_pct: Optional grid load percentage for dynamic promos
    
    Returns:
        Dict with merchant intelligence data
    """
    # Mock events for cohort analysis
    mock_events = [
        {"hour": 22, "day_of_week": 1, "amount": 45.20},
        {"hour": 8, "day_of_week": 2, "amount": 67.80},
        {"hour": 14, "day_of_week": 6, "amount": 89.50},
        {"hour": 19, "day_of_week": 3, "amount": 34.20},
        {"hour": 23, "day_of_week": 5, "amount": 56.70}
    ]
    
    # Generate cohorts
    cohorts_data = cohort_buckets(mock_events)
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
    
    # Generate forecasts
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
    
    # Generate dynamic promotions
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
    
    return {
        "merchant_id": merchant_id,
        "cohorts": cohorts,
        "forecasts": forecasts,
        "promos": promos,
        "last_updated": datetime.utcnow().isoformat()
    }
