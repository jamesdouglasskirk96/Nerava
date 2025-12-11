from datetime import datetime, time
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from ..db import Base

try:
    from sqlalchemy import JSON  # for non-sqlite engines
except Exception:
    JSON = SQLITE_JSON  # fallback for sqlite

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    preferences = relationship("UserPreferences", uselist=False, back_populates="user", cascade="all, delete")
    
    # Domain Charge Party MVP fields
    display_name = Column(String, nullable=True)
    role_flags = Column(String, nullable=True, default="driver")  # comma-separated: "driver,merchant_admin,admin"
    auth_provider = Column(String, nullable=False, default="local")  # local, google, apple
    oauth_sub = Column(String, nullable=True)  # OAuth subject ID
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    food_tags = Column(JSON, default=list, nullable=False)          # ["coffee","tacos"]
    max_detour_minutes = Column(Integer, default=10, nullable=False)
    preferred_networks = Column(JSON, default=list, nullable=False) # ["Tesla","ChargePoint"]
    typical_start = Column(Time, default=time(18, 0), nullable=False)
    typical_end = Column(Time, default=time(22, 0), nullable=False)
    home_zip = Column(String, nullable=True)
    user = relationship("User", back_populates="preferences")


