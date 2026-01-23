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
)
from .intent import (
    IntentSession,
    PerkUnlock,
)
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
    MerchantIntelForecast,
    UtilityBehaviorSnapshot,
    RewardRoutingRun,
    CityImpactSnapshot,
    MobilityDevice,
    MerchantCreditLedger,
    ChargeVerificationLog,
    WalletInteropPartner,
    CoopPool,
    SdkTenantConfig,
    EnergyRepSnapshot,
    EnergyRepBackfill,
    OffsetBatch,
    FleetOrg,
    IotLink,
    GreenHourDeal,
    TenantModule,
    AiRewardSuggestion,
    FinanceOffer,
    GrowthCampaign,
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
    # Intent models
    "IntentSession",
    "PerkUnlock",
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
    "MerchantIntelForecast",
    "UtilityBehaviorSnapshot",
    "RewardRoutingRun",
    "CityImpactSnapshot",
    "MobilityDevice",
    "MerchantCreditLedger",
    "ChargeVerificationLog",
    "WalletInteropPartner",
    "CoopPool",
    "SdkTenantConfig",
    "EnergyRepSnapshot",
    "EnergyRepBackfill",
    "OffsetBatch",
    "FleetOrg",
    "IotLink",
    "GreenHourDeal",
    "TenantModule",
    "AiRewardSuggestion",
    "FinanceOffer",
    "GrowthCampaign",
    "DualZoneSession",
]

