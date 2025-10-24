"""
Demo mode models for investor-friendly demo system.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, UniqueConstraint
from datetime import datetime
from .db import Base

class DemoState(Base):
    __tablename__ = "demo_state"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)       # grid_state, merchant_shift, rep_profile, city
    value = Column(String, nullable=False)                   # "peak"/"offpeak", "A_dominates"/"balanced", "high"/"low", "austin"
    updated_at = Column(DateTime, default=datetime.utcnow)

class DemoSeedLog(Base):
    __tablename__ = "demo_seed_log"
    id = Column(Integer, primary_key=True)
    run_id = Column(String, unique=True, nullable=False)
    summary = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    scopes = Column(JSON, default=list)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
