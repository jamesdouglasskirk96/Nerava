"""
Franchise exclusion list for merchant filtering.
Identifies known national franchise chains to exclude from merchant analysis.
"""

# Comprehensive list of franchise keywords to exclude
FRANCHISE_KEYWORDS = [
    # Fast Food Chains
    "Starbucks",
    "McDonald's",
    "Burger King",
    "Taco Bell",
    "Subway",
    "Chick-fil-A",
    "Dunkin'",
    "Dunkin Donuts",
    "Wendy's",
    "KFC",
    "Pizza Hut",
    "Domino's",
    "Papa John's",
    "Little Caesars",
    "Arby's",
    "Sonic",
    "Dairy Queen",
    "Carl's Jr.",
    "Hardee's",
    "Jack in the Box",
    "Five Guys",
    "In-N-Out",
    "Chipotle",
    "Qdoba",
    "Moe's Southwest Grill",
    "Panera Bread",
    "Jimmy John's",
    "Panda Express",
    "Popeyes",
    "Wingstop",
    "Zaxby's",
    "Raising Cane's",
    "Culver's",
    "Whataburger",
    "Steak 'n Shake",
    "Denny's",
    "IHOP",
    "Waffle House",
    "Cracker Barrel",
    "Olive Garden",
    "Applebee's",
    "Red Lobster",
    "Outback Steakhouse",
    "Chili's",
    "Texas Roadhouse",
    "Buffalo Wild Wings",
    
    # Retail Chains
    "Target",
    "Walmart",
    "Costco",
    "Sam's Club",
    "BJ's Wholesale",
    "Home Depot",
    "Lowe's",
    "Best Buy",
    "Bed Bath & Beyond",
    "Barnes & Noble",
    "Staples",
    "Office Depot",
    "OfficeMax",
    "PetSmart",
    "Petco",
    "Dick's Sporting Goods",
    "Academy Sports",
    "Dillard's",
    "Macy's",
    "Nordstrom",
    "JCPenney",
    "Sears",
    "Kohl's",
    "Ross",
    "T.J. Maxx",
    "Marshalls",
    "HomeGoods",
    "Burlington",
    "Big Lots",
    "Dollar General",
    "Family Dollar",
    "Dollar Tree",
    "Five Below",
    
    # Pharmacy/Convenience
    "CVS",
    "Walgreens",
    "Rite Aid",
    "7-Eleven",
    "Circle K",
    "RaceTrac",
    "Buc-ee's",
    "Love's Travel Stops",
    "Pilot",
    "Flying J",
    
    # Grocery Chains
    "Kroger",
    "H-E-B",
    "Whole Foods",
    "Trader Joe's",
    "Sprouts",
    "Aldi",
    "Lidl",
    "Safeway",
    "Albertsons",
    "Tom Thumb",
    "Randalls",
    "Central Market",
    
    # Coffee Chains
    "Coffee Bean",
    "Peet's Coffee",
    "Dutch Bros",
    "Caribou Coffee",
    
    # Fitness Chains
    "Planet Fitness",
    "24 Hour Fitness",
    "LA Fitness",
    "Gold's Gym",
    "Anytime Fitness",
    "Crunch Fitness",
    "Equinox",
    "Orangetheory",
    "Pure Barre",
    "CrossFit",
    "YMCA",
    "YWCA",
    
    # Gas Stations (usually franchise-heavy)
    "Shell",
    "Exxon",
    "Mobil",
    "Chevron",
    "BP",
    "Valero",
    "Phillips 66",
    "Citgo",
    "Speedway",
    
    # Banks (exclude from merchant analysis)
    "Bank of America",
    "Chase",
    "Wells Fargo",
    "Citibank",
    "US Bank",
    "PNC",
    "Capital One",
    "TD Bank",
    "Regions",
    "BB&T",
    
    # Hotels (franchise-heavy)
    "Holiday Inn",
    "Marriott",
    "Hilton",
    "Hyatt",
    "Sheraton",
    "Westin",
    "DoubleTree",
    "Embassy Suites",
    "Courtyard",
    "Hampton Inn",
    "Comfort Inn",
    "Best Western",
    "La Quinta",
    "Days Inn",
    "Motel 6",
    "Super 8",
    
    # Auto Services (franchise-heavy)
    "Jiffy Lube",
    "Midas",
    "Firestone",
    "Goodyear",
    "Pep Boys",
    "NTB",
    "Tire Kingdom",
    
    # Other Chains
    "FedEx",
    "UPS Store",
    "Mail Boxes Etc",
    "PostNet",
    "GNC",
    "Vitamin Shoppe",
    "GameStop",
    "RadioShack",
    "AT&T Store",
    "Verizon",
    "T-Mobile",
    "Sprint",
]


def is_franchise(merchant_name: str, place_details: dict = None) -> bool:
    """
    Check if a merchant is a franchise/chain based on name and place details.
    
    Args:
        merchant_name: Name of the merchant
        place_details: Optional Google Places details dict
        
    Returns:
        True if merchant appears to be a franchise, False otherwise
    """
    if not merchant_name:
        return False
    
    name_lower = merchant_name.lower()
    
    # Check against franchise keywords
    for keyword in FRANCHISE_KEYWORDS:
        if keyword.lower() in name_lower:
            return True
    
    # Additional heuristics using place details if available
    if place_details:
        # Check for chain indicators in place details
        # Note: Google Places API may have chain indicators we can check
        pass
    
    return False


def filter_franchises(merchants: list) -> list:
    """
    Filter out franchise merchants from a list.
    
    Args:
        merchants: List of merchant dicts with 'name' field
        
    Returns:
        Filtered list with franchises removed
    """
    return [
        merchant for merchant in merchants
        if not is_franchise(merchant.get('name', ''), merchant.get('place_details'))
    ]






