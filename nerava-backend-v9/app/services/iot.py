from typing import Dict, Any
from datetime import datetime

def link_device(provider: str, device_id: str, user_id: str) -> Dict[str, Any]:
    """
    Link a smart home/IoT device.
    
    TODO: Implement real IoT device linking logic
    - Validate device compatibility
    - Set up data integration
    - Configure privacy settings
    - Target p95 < 250ms
    """
    
    # Stub implementation
    return {
        "provider": provider,
        "device_id": device_id,
        "user_id": user_id,
        "status": "linked",
        "linked_at": datetime.utcnow().isoformat()
    }
