from typing import Dict, Any, Literal
import uuid
from datetime import datetime

def register_device(user_id: str, mode: Literal["scooter", "ebike", "av"]) -> Dict[str, Any]:
    """
    Register a multi-modal mobility device.
    
    TODO: Implement real device registration logic
    - Validate device compatibility
    - Store device metadata
    - Set up tracking integration
    - Target p95 < 250ms
    """
    
    # Stub implementation
    device_id = f"{mode}_{uuid.uuid4().hex[:8]}"
    
    return {
        "device_id": device_id,
        "mode": mode,
        "status": "registered",
        "user_id": user_id,
        "registered_at": datetime.utcnow().isoformat()
    }
