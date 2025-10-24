from typing import Dict, Any

def green_hour_deals(lat: float, lng: float) -> Dict[str, Any]:
    """
    Get contextual commerce deals for green hours.
    
    TODO: Implement real green hour deals logic
    - Query nearby merchants
    - Calculate green hour windows
    - Apply location-based filtering
    - Target p95 < 250ms with caching
    """
    
    # Stub implementation
    return {
        "window": {
            "start": "14:00",
            "end": "16:00",
            "timezone": "UTC-8"
        },
        "deals": [
            {
                "merchant_id": "merchant_001",
                "name": "Green Coffee Co",
                "discount_percent": 15,
                "green_hour_bonus": 5,
                "distance_m": 250
            },
            {
                "merchant_id": "merchant_002", 
                "name": "Eco Market",
                "discount_percent": 20,
                "green_hour_bonus": 10,
                "distance_m": 180
            }
        ]
    }
