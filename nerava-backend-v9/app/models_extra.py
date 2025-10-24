from datetime import datetime, time
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from .db import Base

# Import demo models
from .models_demo import DemoState, DemoSeedLog, ApiKey

try:
    from sqlalchemy import JSON
except Exception:
    JSON = SQLITE_JSON

# --- existing: User & UserPreferences live here already ---

class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    id = Column(Integer, primary_key=True)
    user_ref = Column(String, index=True, nullable=False)  # email or "USER_ID" string (compat)
    cents = Column(Integer, nullable=False)                # +earn / -spend
    reason = Column(String, default="ADJUST")              # OFF_PEAK_AWARD / REDEEM / ADJUST
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class IncentiveRule(Base):
    __tablename__ = "incentive_rules"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True)         # "OFF_PEAK_BASE"
    active = Column(Boolean, default=True)
    params = Column(JSON, default=dict)                    # {"cents":25,"window":["22:00","06:00"]}

class UtilityEvent(Base):
    __tablename__ = "utility_events"
    id = Column(Integer, primary_key=True)
    provider = Column(String, index=True)                  # "austin_energy"
    kind = Column(String)                                   # "DR_EVENT","RATE_WINDOW"
    window = Column(JSON, default=dict)                     # {"start":"...","end":"..."}
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# --- Social / Community Pool ---

class Follow(Base):
    __tablename__ = "follows"
    id = Column(Integer, primary_key=True)
    follower_id = Column(String, index=True, nullable=False)
    followee_id = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class RewardEvent(Base):
    __tablename__ = "reward_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    source = Column(String, index=True, nullable=False)  # "CHARGE","REFERRAL","MERCHANT","BONUS"
    gross_cents = Column(Integer, nullable=False)
    community_cents = Column(Integer, nullable=False)
    net_cents = Column(Integer, nullable=False)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FollowerShare(Base):
    __tablename__ = "follower_shares"
    id = Column(Integer, primary_key=True)
    reward_event_id = Column(Integer, ForeignKey("reward_events.id"), index=True, nullable=False)
    payee_user_id = Column(String, index=True, nullable=False)
    cents = Column(Integer, nullable=False)
    settled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class CommunityPeriod(Base):
    __tablename__ = "community_periods"
    id = Column(Integer, primary_key=True)
    period_key = Column(String, unique=True, index=True)  # e.g., "2025-10"
    total_gross_cents = Column(Integer, default=0)
    total_community_cents = Column(Integer, default=0)
    total_distributed_cents = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# --- Group Challenges ---

class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    scope = Column(String, nullable=False)  # 'city' or 'global'
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    goal_kwh = Column(Integer, nullable=False)  # Total kWh goal
    sponsor_merchant_id = Column(String, index=True)  # Optional sponsor
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Participation(Base):
    __tablename__ = "participations"
    id = Column(Integer, primary_key=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    kwh = Column(Integer, default=0)  # User's contribution
    points = Column(Integer, default=0)  # Points earned
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# ===== 20 Feature Scaffold Models =====

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    key = Column(String, primary_key=True)
    enabled = Column(Boolean, default=False)
    env = Column(String, default="prod")  # prod/staging/dev

# 1 Merchant Intel
class MerchantIntelForecast(Base):
    __tablename__ = "merchant_intel_forecasts"
    id = Column(Integer, primary_key=True)
    merchant_id = Column(String, index=True, nullable=False)
    horizon_hours = Column(Integer, default=24)
    payload = Column(JSON, default=dict)
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)

# 2 Behavior Cloud
class UtilityBehaviorSnapshot(Base):
    __tablename__ = "utility_behavior_snapshots"
    id = Column(Integer, primary_key=True)
    utility_id = Column(String, index=True, nullable=False)
    window = Column(String, default="24h")
    segments = Column(JSON, default=dict)
    elasticity = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# 3 Autonomous Reward Routing
class RewardRoutingRun(Base):
    __tablename__ = "reward_routing_runs"
    id = Column(Integer, primary_key=True)
    run_id = Column(String, unique=True, nullable=False)
    status = Column(String, default="scheduled")  # scheduled|running|done|failed
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# 4 City Marketplace
class CityImpactSnapshot(Base):
    __tablename__ = "city_impact_snapshots"
    id = Column(Integer, primary_key=True)
    city_slug = Column(String, index=True, nullable=False)
    mwh_saved = Column(Integer, default=0)  # Using Integer for SQLite compatibility
    rewards_paid_cents = Column(Integer, default=0)
    leaderboard = Column(JSON, default=list)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)

# 5 Multi-Modal
class MobilityDevice(Base):
    __tablename__ = "mobility_devices"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, unique=True, nullable=False)
    mode = Column(String, nullable=False)  # scooter|ebike|av
    user_id = Column(String, index=True)
    registered_at = Column(DateTime, default=datetime.utcnow)

# 6 Merchant Credits
class MerchantCreditLedger(Base):
    __tablename__ = "merchant_credit_ledger"
    id = Column(Integer, primary_key=True)
    merchant_id = Column(String, index=True, nullable=False)
    delta_credits = Column(Integer, nullable=False)
    price_cents = Column(Integer, default=0)
    reason = Column(String, default="purchase")  # purchase|spend|refund
    created_at = Column(DateTime, default=datetime.utcnow)

# 7 Verify API
class ChargeVerificationLog(Base):
    __tablename__ = "charge_verification_logs"
    id = Column(Integer, primary_key=True)
    request_id = Column(String, unique=True, nullable=False)
    external_app = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# 8 Wallet Interop
class WalletInteropPartner(Base):
    __tablename__ = "wallet_interop_partners"
    id = Column(Integer, primary_key=True)
    partner = Column(String, index=True, nullable=False)  # apple_pay|visa|bank_x
    config = Column(JSON, default=dict)
    enabled = Column(Boolean, default=False)

# 9 Co-Ops
class CoopPool(Base):
    __tablename__ = "coop_pools"
    id = Column(Integer, primary_key=True)
    pool_id = Column(String, unique=True, nullable=False)
    utility_id = Column(String, index=True, nullable=False)
    merchants = Column(JSON, default=list)
    status = Column(String, default="active")

# 10 SDK
class SdkTenantConfig(Base):
    __tablename__ = "sdk_tenant_configs"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, unique=True, nullable=False)
    modules = Column(JSON, default=list)
    branding = Column(JSON, default=dict)

# 11 Energy Rep
class EnergyRepSnapshot(Base):
    __tablename__ = "energy_rep_snapshots"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    score = Column(Integer, nullable=False)
    components = Column(JSON, default=dict)
    tier = Column(String, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)

class EnergyRepBackfill(Base):
    __tablename__ = "energy_rep_backfills"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    score = Column(Integer, nullable=False)
    components = Column(JSON, default=dict)
    tier = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 12 Carbon Offsets
class OffsetBatch(Base):
    __tablename__ = "offset_batches"
    id = Column(Integer, primary_key=True)
    batch_id = Column(String, unique=True, nullable=False)
    tons_co2e = Column(Integer, default=0)  # Using Integer for SQLite compatibility
    credits_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# 13 Fleet
class FleetOrg(Base):
    __tablename__ = "fleet_orgs"
    id = Column(Integer, primary_key=True)
    org_id = Column(String, unique=True, nullable=False)
    settings = Column(JSON, default=dict)

# 14 IoT
class IotLink(Base):
    __tablename__ = "iot_links"
    id = Column(Integer, primary_key=True)
    provider = Column(String, index=True, nullable=False)
    device_id = Column(String, nullable=False)
    user_id = Column(String, index=True)
    status = Column(String, default="linked")
    linked_at = Column(DateTime, default=datetime.utcnow)

# 15 Contextual Commerce
class GreenHourDeal(Base):
    __tablename__ = "green_hour_deals"
    id = Column(Integer, primary_key=True)
    merchant_id = Column(String, index=True, nullable=False)
    window = Column(JSON, default=dict)  # start/end UTC
    terms = Column(JSON, default=dict)
    geo = Column(JSON, default=dict)

# 16 Events
class EnergyEvent(Base):
    __tablename__ = "energy_events"
    id = Column(Integer, primary_key=True)
    event_id = Column(String, unique=True, nullable=False)
    host_id = Column(String, index=True, nullable=False)
    schedule = Column(JSON, default=dict)
    boost_rate = Column(Integer, default=0)  # Using Integer for SQLite compatibility

# 17 Utility Platform Tenants
class TenantModule(Base):
    __tablename__ = "tenant_modules"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True, nullable=False)
    module_key = Column(String, nullable=False)
    config = Column(JSON, default=dict)

# 18 AI Reward Suggestions
class AiRewardSuggestion(Base):
    __tablename__ = "ai_reward_suggestions"
    id = Column(Integer, primary_key=True)
    region = Column(String, index=True)
    hour_utc = Column(Integer)
    incentive_cents = Column(Integer)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

# 19 Finance Offers
class FinanceOffer(Base):
    __tablename__ = "finance_offers"
    id = Column(Integer, primary_key=True)
    partner = Column(String, index=True)
    apr_delta_bps = Column(Integer, default=0)
    terms_url = Column(String)
    eligibility = Column(JSON, default=dict)

# 20 AI Growth Campaigns
class GrowthCampaign(Base):
    __tablename__ = "growth_campaigns"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String, unique=True, nullable=False)
    variants = Column(JSON, default=list)
    status = Column(String, default="draft")

# Dual-Radius Verification Model
class DualZoneSession(Base):
    __tablename__ = "dual_zone_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    charger_id = Column(String, index=True, nullable=False)
    merchant_id = Column(String, index=True, nullable=False)

    # timestamps
    started_at = Column(DateTime, default=datetime.utcnow, index=True)   # app-side start
    charger_entered_at = Column(DateTime, nullable=True)
    merchant_entered_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # parameters
    charger_radius_m = Column(Integer, default=40)   # R1
    merchant_radius_m = Column(Integer, default=100) # R2
    dwell_threshold_s = Column(Integer, default=300) # 5 min

    # computed
    dwell_seconds = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending|verified|expired
    meta = Column(JSON, default=dict)

Index("ix_dual_zone_user_active", DualZoneSession.user_id, DualZoneSession.status)
