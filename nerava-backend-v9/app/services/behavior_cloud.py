from typing import Dict, Any, List
from datetime import datetime
import math

def segment_users(window: str) -> List[Dict[str, Any]]:
    """
    Segment users based on charging behavior patterns.
    
    Args:
        window: Time window for analysis (e.g., "24h", "7d")
    
    Returns:
        List of user segments with counts and characteristics
    """
    # Deterministic segmentation based on window
    base_size = 1000 if window == "24h" else 5000
    
    segments = [
        {
            "name": "Night Owls",
            "size": int(base_size * 0.25),
            "avg_shift_kwh": 15.2,
            "elasticity": -0.45,
            "characteristics": ["late_night_charging", "high_flexibility"]
        },
        {
            "name": "Green Commuters", 
            "size": int(base_size * 0.35),
            "avg_shift_kwh": 8.7,
            "elasticity": -0.67,
            "characteristics": ["rush_hour_avoidance", "price_sensitive"]
        },
        {
            "name": "Weekend Fast",
            "size": int(base_size * 0.20),
            "avg_shift_kwh": 22.1,
            "elasticity": -0.89,
            "characteristics": ["weekend_charging", "high_volume"]
        },
        {
            "name": "Flexible Chargers",
            "size": int(base_size * 0.20),
            "avg_shift_kwh": 18.2,
            "elasticity": -0.78,
            "characteristics": ["time_flexible", "incentive_responsive"]
        }
    ]
    
    return segments

def participation(window: str) -> Dict[str, Any]:
    """
    Calculate participation metrics by hour using deterministic curve.
    
    Args:
        window: Time window for analysis
    
    Returns:
        Dict with participation data
    """
    # Generate participation curve (higher during off-peak hours)
    participation_by_hour = {}
    total_users = 5000 if window == "7d" else 1000
    
    for hour in range(24):
        # Higher participation during off-peak hours (22-6, 10-14)
        if 22 <= hour or hour <= 6 or 10 <= hour <= 14:
            participation_rate = 0.8 + 0.2 * math.sin(hour * math.pi / 12)
        else:
            participation_rate = 0.3 + 0.1 * math.sin(hour * math.pi / 12)
        
        participation_by_hour[hour] = {
            "participation_rate": max(0.1, min(1.0, participation_rate)),
            "active_users": int(total_users * participation_rate)
        }
    
    # Calculate aggregate metrics
    active_participants = sum(data["active_users"] for data in participation_by_hour.values())
    avg_participation_rate = active_participants / (total_users * 24)
    avg_shift_kwh = 12.1 + (hash(window) % 5)  # Add some variation
    
    return {
        "total_users": total_users,
        "active_participants": active_participants,
        "participation_rate": avg_participation_rate,
        "avg_shift_kwh": avg_shift_kwh,
        "by_hour": participation_by_hour
    }

def elasticity_estimate() -> Dict[str, Any]:
    """
    Estimate demand elasticity using deterministic price points.
    
    Returns:
        Dict with elasticity estimates
    """
    # Price points and expected responsiveness
    price_points = [
        {"price_cents_kwh": 5, "expected_lift": 0.15},
        {"price_cents_kwh": 10, "expected_lift": 0.35},
        {"price_cents_kwh": 20, "expected_lift": 0.65}
    ]
    
    # Calculate elasticity coefficients
    price_elasticity = -0.45  # Negative: higher prices reduce demand
    time_elasticity = -0.23   # Negative: peak hours reduce demand
    incentive_elasticity = 0.78  # Positive: incentives increase participation
    
    return {
        "price_points": price_points,
        "price_elasticity": price_elasticity,
        "time_elasticity": time_elasticity,
        "incentive_elasticity": incentive_elasticity,
        "confidence": 0.82
    }

def get_cloud(utility_id: str, window: str) -> Dict[str, Any]:
    """
    Get utility behavior cloud with segments, participation, and elasticity data.
    
    Args:
        utility_id: Utility identifier
        window: Time window for analysis
    
    Returns:
        Dict with behavior cloud data
    """
    # Generate segments
    segments = segment_users(window)
    
    # Calculate participation
    participation_data = participation(window)
    
    # Estimate elasticity
    elasticity_data = elasticity_estimate()
    
    return {
        "utility_id": utility_id,
        "window": window,
        "segments": segments,
        "participation": {
            "total_users": participation_data["total_users"],
            "active_participants": participation_data["active_participants"],
            "participation_rate": participation_data["participation_rate"],
            "avg_shift_kwh": participation_data["avg_shift_kwh"]
        },
        "elasticity": {
            "price_elasticity": elasticity_data["price_elasticity"],
            "time_elasticity": elasticity_data["time_elasticity"],
            "incentive_elasticity": elasticity_data["incentive_elasticity"],
            "confidence": elasticity_data["confidence"]
        },
        "generated_at": datetime.utcnow().isoformat()
    }
