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
