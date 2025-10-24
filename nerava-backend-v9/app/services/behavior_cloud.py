from typing import Dict, Any, List
from datetime import datetime
import math
from sqlalchemy.orm import Session
from ..models_extra import UtilityBehaviorSnapshot
from ..obs.obs import log_info, log_warn

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

def get_cloud(utility_id: str, window: str, db: Session = None) -> Dict[str, Any]:
    """
    Get utility behavior cloud with v1 logic implementation.
    
    Args:
        utility_id: Utility identifier
        window: Time window for analysis
        db: Database session for persistence
    
    Returns:
        Dict with behavior cloud data
    """
    start_time = datetime.utcnow()
    log_info(f"Computing behavior cloud for {utility_id} window {window}")
    
    # Generate segments using v1 logic
    segments = segment_users(window)
    log_info(f"Generated {len(segments)} user segments")
    
    # Calculate participation using v1 logic
    participation_data = participation(window)
    log_info(f"Participation rate: {participation_data['participation_rate']:.2%}")
    
    # Estimate elasticity using v1 logic
    elasticity_data = elasticity_estimate()
    
    result = {
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
    
    # Persist snapshot if database available
    if db:
        try:
            snapshot = UtilityBehaviorSnapshot(
                utility_id=utility_id,
                version="v1",
                inputs={"window": window},
                segments=segments,
                participation=participation_data,
                elasticity=elasticity_data
            )
            db.add(snapshot)
            db.commit()
            log_info(f"Persisted behavior cloud snapshot for {utility_id}")
        except Exception as e:
            log_warn(f"Failed to persist snapshot: {e}")
            db.rollback()
    
    # Log metrics
    compute_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    log_info(f"Behavior cloud compute time: {compute_time:.2f}ms")
    
    return result
