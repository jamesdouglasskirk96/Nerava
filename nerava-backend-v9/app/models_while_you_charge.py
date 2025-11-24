"""
Models for "While You Charge" feature
- Chargers (EV charging stations)
- Merchants (places near chargers)
- ChargerMerchants (junction table with walk times)
- MerchantPerks (active rewards/offers)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from .db import Base

try:
    from sqlalchemy import JSON
except Exception:
    JSON = SQLITE_JSON


class Charger(Base):
    """EV charging station"""
    __tablename__ = "chargers"
    
    id = Column(String, primary_key=True)  # e.g., "ch_123" or external ID
    external_id = Column(String, unique=True, index=True, nullable=True)  # NREL/OCM ID
    name = Column(String, nullable=False)
    network_name = Column(String, nullable=True)  # "Tesla", "ChargePoint", etc.
    lat = Column(Float, nullable=False, index=True)
    lng = Column(Float, nullable=False, index=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    
    # Charger details
    connector_types = Column(JSON, default=list)  # ["CCS", "CHAdeMO", "Tesla"]
    power_kw = Column(Float, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    access_code = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="available", nullable=False)  # available, in_use, broken, unknown
    last_verified_at = Column(DateTime, nullable=True)
    
    # Metadata
    logo_url = Column(String, nullable=True)  # Network logo URL
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    merchants = relationship("ChargerMerchant", back_populates="charger", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_chargers_location', 'lat', 'lng'),
    )


class Merchant(Base):
    """Merchant/place near chargers"""
    __tablename__ = "merchants"
    
    id = Column(String, primary_key=True)  # e.g., "m_1"
    external_id = Column(String, unique=True, index=True, nullable=True)  # Google Places ID
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=True, index=True)  # "coffee", "restaurant", "grocery_or_supermarket", "gym"
    
    lat = Column(Float, nullable=False, index=True)
    lng = Column(Float, nullable=False, index=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    
    # Merchant details
    logo_url = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    price_level = Column(Integer, nullable=True)  # 1-4 (Google Places)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Google Places types (array)
    place_types = Column(JSON, default=list)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    charger_links = relationship("ChargerMerchant", back_populates="merchant", cascade="all, delete-orphan")
    perks = relationship("MerchantPerk", back_populates="merchant", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_merchants_location', 'lat', 'lng'),
    )


class ChargerMerchant(Base):
    """Junction table: which merchants are near which chargers, with walk times"""
    __tablename__ = "charger_merchants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    charger_id = Column(String, ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Distance and travel time
    distance_m = Column(Float, nullable=False)  # Straight-line distance in meters
    walk_duration_s = Column(Integer, nullable=False)  # Walking time in seconds (from Distance Matrix)
    walk_distance_m = Column(Float, nullable=True)  # Actual walking distance (may differ from straight-line)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    charger = relationship("Charger", back_populates="merchants")
    merchant = relationship("Merchant", back_populates="charger_links")
    
    __table_args__ = (
        Index('idx_charger_merchant_unique', 'charger_id', 'merchant_id', unique=True),
    )


class MerchantPerk(Base):
    """Active perks/rewards for merchants"""
    __tablename__ = "merchant_perks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Perk details
    title = Column(String, nullable=False)  # "Earn 12 Nova"
    description = Column(Text, nullable=True)
    nova_reward = Column(Integer, nullable=False)  # Nova amount (cents or points)
    
    # Time window (optional - if null, always active)
    window_start = Column(String, nullable=True)  # "14:00" (HH:MM format)
    window_end = Column(String, nullable=True)  # "18:00"
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="perks")

