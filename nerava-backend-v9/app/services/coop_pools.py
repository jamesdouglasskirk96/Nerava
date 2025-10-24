from typing import Dict, Any
import uuid
from datetime import datetime

def create_pool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a merchant-utility cooperation pool.
    
    TODO: Implement real coop pool creation logic
    - Validate utility and merchant relationships
    - Set up shared incentive structures
    - Configure pool parameters
    - Target p95 < 250ms
    """
    
    # Stub implementation
    pool_id = f"pool_{uuid.uuid4().hex[:8]}"
    
    return {
        "pool_id": pool_id,
        "utility_id": payload["utility_id"],
        "merchants": payload["merchants"],
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
