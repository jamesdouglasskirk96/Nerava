# LEGACY: This file has been moved to app/models/extra.py
# Import from new location for backward compatibility
from .models.extra import (
    CreditLedger,
    IncentiveRule,
    UtilityEvent,
    Follow,
    RewardEvent,
    FollowerShare,
    CommunityPeriod,
    Challenge,
    Participation,
    FeatureFlag,
    DualZoneSession,
)

__all__ = [
    "CreditLedger",
    "IncentiveRule",
    "UtilityEvent",
    "Follow",
    "RewardEvent",
    "FollowerShare",
    "CommunityPeriod",
    "Challenge",
    "Participation",
    "FeatureFlag",
    "DualZoneSession",
]
