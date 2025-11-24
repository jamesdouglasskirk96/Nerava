"""
Domain Hub Verification Configuration

Per-hub, per-location verification tuning parameters for the Domain Hub pilot.
These values will be calibrated on-site at The Domain.

All radii are in meters.
All times are in seconds.
"""
from typing import Dict

# Hub identifier
HUB_ID = "domain"

# ============================================
# Charger-Specific Verification Radii
# ============================================
# These override default radii for Domain chargers
# Values are in meters
DOMAIN_CHARGER_RADIUS_M: Dict[str, int] = {
    "ch_domain_tesla_001": 75,          # Tesla Supercharger - tighter radius for outdoor chargers
    "ch_domain_chargepoint_001": 75,    # ChargePoint Shopping Center - standard outdoor radius
    "ch_domain_chargepoint_002": 60,    # ChargePoint Parking Garage - tighter radius for indoor/multi-level
}

# Default charger radius if not specified above
DOMAIN_CHARGER_DEFAULT_RADIUS_M = 75

# ============================================
# Merchant-Specific Verification Radii
# ============================================
# These override default radii for Domain merchants
DOMAIN_MERCHANT_RADIUS_M: Dict[str, int] = {
    # Will be populated as merchants are seeded and calibrated
    # Example:
    # "m_domain_starbucks_001": 40,
    # "m_domain_target_001": 50,
}

# Default merchant radius if not specified above
DOMAIN_MERCHANT_DEFAULT_RADIUS_M = 40

# ============================================
# Domain-Specific Dwell Thresholds
# ============================================
# Minimum dwell time required for verification (in seconds)
DOMAIN_DWELL_REQUIRED_S = 90  # 1.5 minutes minimum
DOMAIN_DWELL_OPTIMAL_S = 120  # 2 minutes for optimal score

# ============================================
# Drift Tolerance
# ============================================
# Maximum distance change between pings within 30 seconds
# before applying drift penalty (in meters)
DOMAIN_DRIFT_TOLERANCE_M = 25

# Time window for drift calculation (in seconds)
DOMAIN_DRIFT_WINDOW_S = 30

# ============================================
# Scoring Configuration
# ============================================
# Base score starts at 100
VERIFICATION_BASE_SCORE = 100

# Penalty weights (points deducted per unit)
SCORE_DISTANCE_PENALTY_PER_M = 2  # 2 points per meter beyond radius
SCORE_DWELL_PENALTY_PER_S = 1     # 1 point per second below optimal dwell
SCORE_DRIFT_PENALTY_PER_M = 3     # 3 points per meter of drift beyond tolerance
SCORE_ACCURACY_PENALTY_PER_M = 1  # 1 point per meter of accuracy error above threshold

# Maximum penalties (score cannot go below 0)
MAX_DISTANCE_PENALTY = 50
MAX_DWELL_PENALTY = 30
MAX_DRIFT_PENALTY = 30
MAX_ACCURACY_PENALTY = 20

# ============================================
# Helper Functions
# ============================================

def get_charger_radius(charger_id: str) -> int:
    """Get verification radius for a Domain charger, with fallback to default."""
    return DOMAIN_CHARGER_RADIUS_M.get(charger_id, DOMAIN_CHARGER_DEFAULT_RADIUS_M)


def get_merchant_radius(merchant_id: str) -> int:
    """Get verification radius for a Domain merchant, with fallback to default."""
    return DOMAIN_MERCHANT_RADIUS_M.get(merchant_id, DOMAIN_MERCHANT_DEFAULT_RADIUS_M)


def get_dwell_required() -> int:
    """Get minimum dwell time required for Domain hub verification."""
    return DOMAIN_DWELL_REQUIRED_S


def get_drift_tolerance() -> int:
    """Get drift tolerance for Domain hub verification."""
    return DOMAIN_DRIFT_TOLERANCE_M

