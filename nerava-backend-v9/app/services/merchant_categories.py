"""
Merchant category mapping service.

Maps Google Places types to primary categories (coffee, food, other).
"""
from typing import List, Optional

# Map Google Places types to category groups
GOOGLE_TYPES_TO_GROUP = {
    "cafe": "coffee",
    "coffee_shop": "coffee",
    "bakery": "coffee",
    "restaurant": "food",
    "meal_takeaway": "food",
    "meal_delivery": "food",
    "bar": "food",
    "fast_food_restaurant": "food",
}


def to_primary_category(google_types: Optional[List[str]]) -> str:
    """
    Convert Google Places types to primary category.
    
    Rules:
    - Coffee wins over food if both present
    - Returns 'other' if no match
    
    Args:
        google_types: List of Google Places type strings (e.g., ["cafe", "restaurant"])
    
    Returns:
        "coffee", "food", or "other"
    """
    if not google_types:
        return "other"
    
    # Check for coffee types first (coffee wins over food)
    for place_type in google_types:
        if GOOGLE_TYPES_TO_GROUP.get(place_type) == "coffee":
            return "coffee"
    
    # Check for food types
    for place_type in google_types:
        if GOOGLE_TYPES_TO_GROUP.get(place_type) == "food":
            return "food"
    
    return "other"


