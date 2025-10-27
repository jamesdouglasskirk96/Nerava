# server/src/models.py
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    handle = Column(String, index=True)
    avatar_url = Column(String, nullable=True)
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)

class Reputation(Base):
    __tablename__ = "user_reputation"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    score = Column(Integer, default=0)
    tier = Column(String, default="Bronze")
    updated_at = Column(DateTime, default=datetime.utcnow)

class FollowEarning(Base):
    __tablename__ = "follow_earnings_monthly"
    month_yyyymm = Column(Integer, primary_key=True)
    receiver_user_id = Column(String, primary_key=True)
    payer_user_id = Column(String, primary_key=True)
    amount_cents = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChargeIntent(Base):
    __tablename__ = "charge_intents"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    station_id = Column(String)
    station_name = Column(String)
    merchant = Column(String, nullable=True)
    address = Column(String, nullable=True)
    window_text = Column(String, nullable=True)   # e.g. "2–4pm"
    distance_text = Column(String, nullable=True) # e.g. "3 min walk"
    status = Column(String, default="pending")    # pending|started|notified|done
    created_at = Column(DateTime, default=datetime.utcnow)

class WalletEvent(Base):
    __tablename__ = "wallet_events"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # 'credit' or 'debit'
    source = Column(String, nullable=False)  # e.g., 'merchant_reward', 'payment', 'green_hour'
    amount_cents = Column(Integer, nullable=False)
    meta = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "user_settings"
    user_id = Column(String, primary_key=True)
    green_alerts = Column(Boolean, default=True)
    perk_alerts = Column(Boolean, default=True)
    vehicle = Column(JSON, nullable=True)
