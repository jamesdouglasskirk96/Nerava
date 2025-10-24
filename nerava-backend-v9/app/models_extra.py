from datetime import datetime, time
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from .db import Base

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
