"""
Models package - organized by domain
"""
# Re-export all models for backward compatibility
from .user import User, UserPreferences
from .refresh_token import RefreshToken
from .otp_challenge import OTPChallenge
from .notification_prefs import UserNotificationPrefs
from .domain import (
    Zone,
    EnergyEvent,
    DomainMerchant,
    DriverWallet,
    NovaTransaction,
    DomainChargingSession,
    StripePayment,
    ApplePassRegistration,
    GoogleWalletLink,
)
from .vehicle import (
    VehicleAccount,
    VehicleToken,
    VehicleTelemetry,
)
from .while_you_charge import (
    Charger,
    Merchant,
    ChargerMerchant,
    MerchantPerk,
    MerchantBalance,
    MerchantBalanceLedger,
    MerchantOfferCode,
    FavoriteMerchant,
    ChargerCluster,
    AmenityVote,
)
from .intent import (
    IntentSession,
    PerkUnlock,
)
from .charge_intent import ChargeIntent
from .user_reputation import UserReputation
from .exclusive_session import (
    ExclusiveSession,
    ExclusiveSessionStatus,
)
from .vehicle_onboarding import (
    VehicleOnboarding,
)
from .merchant_cache import (
    MerchantCache,
)
from .wallet_pass_state import (
    WalletPassState,
)
from .wallet_pass import (
    WalletPassActivation,
    WalletPassStateEnum,
)
from .merchant_account import (
    MerchantAccount,
    MerchantLocationClaim,
    MerchantPlacementRule,
    MerchantPaymentMethod,
)
from .claim_session import ClaimSession
from .verified_visit import VerifiedVisit
from .user_consent import UserConsent
from .arrival_session import ArrivalSession
from .car_pin import CarPin
from .merchant_notification_config import MerchantNotificationConfig
from .merchant_pos_credentials import MerchantPOSCredentials
from .billing_event import BillingEvent
from .queued_order import QueuedOrder, QueuedOrderStatus
from .virtual_key import VirtualKey
from .tesla_connection import TeslaConnection, EVVerificationCode
from .device_token import DeviceToken
from .campaign import Campaign
from .session_event import SessionEvent, IncentiveGrant
from .driver_wallet import Payout, WalletLedger
from .extra import (
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
    # User models
    "User",
    "UserPreferences",
    "RefreshToken",
    "OTPChallenge",
    "UserNotificationPrefs",
    # Domain models
    "Zone",
    "EnergyEvent",
    "DomainMerchant",
    "DriverWallet",
    "NovaTransaction",
    "DomainChargingSession",
    "StripePayment",
    "ApplePassRegistration",
    "GoogleWalletLink",
    # Vehicle models
    "VehicleAccount",
    "VehicleToken",
    "VehicleTelemetry",
    # While You Charge models
    "Charger",
    "Merchant",
    "ChargerMerchant",
    "MerchantPerk",
    "MerchantBalance",
    "MerchantBalanceLedger",
    "MerchantOfferCode",
    "FavoriteMerchant",
    "ChargerCluster",
    "AmenityVote",
    # Intent models
    "IntentSession",
    "PerkUnlock",
    "ChargeIntent",
    "UserReputation",
    # Exclusive session models
    "ExclusiveSession",
    "ExclusiveSessionStatus",
    # Vehicle onboarding models
    "VehicleOnboarding",
    # Merchant cache models
    "MerchantCache",
    # Wallet pass state models
    "WalletPassState",
    "WalletPassActivation",
    "WalletPassStateEnum",
    # Merchant account models
    "MerchantAccount",
    "MerchantLocationClaim",
    "MerchantPlacementRule",
    "MerchantPaymentMethod",
    # Claim session models
    "ClaimSession",
    # Verified visit models
    "VerifiedVisit",
    # User consent models
    "UserConsent",
    # EV Arrival models
    "ArrivalSession",
    "CarPin",
    "MerchantNotificationConfig",
    "MerchantPOSCredentials",
    "BillingEvent",
    "QueuedOrder",
    "QueuedOrderStatus",
    # Virtual Key models
    "VirtualKey",
    # Device token models
    "DeviceToken",
    # Campaign / Incentive models
    "Campaign",
    "SessionEvent",
    "IncentiveGrant",
    # Extra models
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

