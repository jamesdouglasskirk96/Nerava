"""
Geographic bounds for Texas metro areas and intercity corridors.
Used for charger discovery with location bias.
"""

# Texas Metro Area Bounds (center coordinates + radius in meters)
TEXAS_METRO_BOUNDS = {
    "dallas": {
        "name": "Dallas-Fort Worth",
        "lat": 32.7767,
        "lng": -96.7970,
        "radius_km": 50,  # Large metro area
        "city": "Dallas",
        "state": "TX"
    },
    "austin": {
        "name": "Austin Metro",
        "lat": 30.2672,
        "lng": -97.7431,
        "radius_km": 30,
        "city": "Austin",
        "state": "TX"
    },
    "san_antonio": {
        "name": "San Antonio Metro",
        "lat": 29.4241,
        "lng": -98.4936,
        "radius_km": 30,
        "city": "San Antonio",
        "state": "TX"
    },
    "houston": {
        "name": "Houston Metro",
        "lat": 29.7604,
        "lng": -95.3698,
        "radius_km": 50,  # Large metro area
        "city": "Houston",
        "state": "TX"
    },
}

# Intercity Corridor Points (strategic points along major highways)
# I-35: Dallas → Austin → San Antonio → Laredo
# I-10: Houston → San Antonio → El Paso
# I-45: Dallas → Houston

INTERCITY_CORRIDORS = {
    "i35": [
        {
            "name": "I-35 - Waco",
            "lat": 31.5493,
            "lng": -97.1467,
            "radius_km": 15,
            "city": "Waco",
            "state": "TX"
        },
        {
            "name": "I-35 - Temple",
            "lat": 31.0982,
            "lng": -97.3428,
            "radius_km": 15,
            "city": "Temple",
            "state": "TX"
        },
        {
            "name": "I-35 - Georgetown",
            "lat": 30.6333,
            "lng": -97.6778,
            "radius_km": 15,
            "city": "Georgetown",
            "state": "TX"
        },
        {
            "name": "I-35 - New Braunfels",
            "lat": 29.7030,
            "lng": -98.1245,
            "radius_km": 15,
            "city": "New Braunfels",
            "state": "TX"
        },
        {
            "name": "I-35 - San Marcos",
            "lat": 29.8833,
            "lng": -97.9414,
            "radius_km": 15,
            "city": "San Marcos",
            "state": "TX"
        },
    ],
    "i10": [
        {
            "name": "I-10 - Katy",
            "lat": 29.7858,
            "lng": -95.8244,
            "radius_km": 15,
            "city": "Katy",
            "state": "TX"
        },
        {
            "name": "I-10 - Sealy",
            "lat": 29.7808,
            "lng": -96.1580,
            "radius_km": 15,
            "city": "Sealy",
            "state": "TX"
        },
        {
            "name": "I-10 - Columbus",
            "lat": 29.7066,
            "lng": -96.5394,
            "radius_km": 15,
            "city": "Columbus",
            "state": "TX"
        },
        {
            "name": "I-10 - Seguin",
            "lat": 29.5688,
            "lng": -97.9647,
            "radius_km": 15,
            "city": "Seguin",
            "state": "TX"
        },
    ],
    "i45": [
        {
            "name": "I-45 - Corsicana",
            "lat": 32.0954,
            "lng": -96.4686,
            "radius_km": 15,
            "city": "Corsicana",
            "state": "TX"
        },
        {
            "name": "I-45 - Madisonville",
            "lat": 30.9499,
            "lng": -95.9116,
            "radius_km": 15,
            "city": "Madisonville",
            "state": "TX"
        },
        {
            "name": "I-45 - Huntsville",
            "lat": 30.7235,
            "lng": -95.5508,
            "radius_km": 15,
            "city": "Huntsville",
            "state": "TX"
        },
        {
            "name": "I-45 - The Woodlands",
            "lat": 30.1654,
            "lng": -95.4613,
            "radius_km": 15,
            "city": "The Woodlands",
            "state": "TX"
        },
    ],
}


def get_all_search_locations():
    """
    Get all search locations (metros + intercity corridors) for charger discovery.
    
    Returns:
        List of location dicts with lat, lng, radius_km, city, state
    """
    locations = []
    
    # Add metro areas
    for metro_key, metro_data in TEXAS_METRO_BOUNDS.items():
        locations.append(metro_data)
    
    # Add intercity corridor points
    for corridor_key, corridor_points in INTERCITY_CORRIDORS.items():
        locations.extend(corridor_points)
    
    return locations


def get_metro_bounds(metro_name: str):
    """
    Get bounds for a specific metro area.
    
    Args:
        metro_name: One of "dallas", "austin", "san_antonio", "houston"
        
    Returns:
        Dict with lat, lng, radius_km, city, state
    """
    return TEXAS_METRO_BOUNDS.get(metro_name.lower())

