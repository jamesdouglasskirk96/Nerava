from typing import Dict, Any
from datetime import datetime

def compute(user_id: str) -> Dict[str, Any]:
    """
    Compute user's energy reputation score and tier.
    
    TODO: Implement real energy reputation calculation
    - Analyze charging behavior patterns
    - Calculate sustainability metrics
    - Determine tier based on score
    - Target p95 < 250ms with caching
    """
    
    # Stub implementation - return static score 650 Silver for now
    score = 650
    tier = "Silver"
    
    return {
        "user_id": user_id,
        "score": score,
        "tier": tier,
        "components": {
            "charging_efficiency": 0.87,
            "off_peak_usage": 0.92,
            "renewable_preference": 0.78,
            "community_impact": 0.65
        },
        "last_calculated_at": datetime.utcnow().isoformat()
    }
