"""
Domain Charge Party MVP Models

These models are separate from the existing "While You Charge" models
to support the Domain-specific charge party event system with merchants,
drivers, Nova transactions, and Stripe integration.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from .db import Base

try:
    from sqlalchemy import JSON  # for non-sqlite engines
except Exception:
    JSON = SQLITE_JSON  # fallback for sqlite


class Zone(Base):
    """Geographic zone (e.g., domain_austin, south_lamar_austin)"""
    __tablename__ = "zones"
    
    slug = Column(String, primary_key=True)  # e.g., "domain_austin"
    name = Column(String, nullable=False)  # e.g., "The Domain, Austin"
    
    # Geographic bounds (for validation)
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    radius_m = Column(Integer, nullable=False, default=1000)  # meters
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)


class EnergyEvent(Base):
    """Charge party event (e.g., domain_jan_2025)"""
    __tablename__ = "energy_events"
    
    id = Column(String, primary_key=True)  # UUID as string
    slug = Column(String, unique=True, nullable=False, index=True)  # e.g., "domain_jan_2025"
    zone_slug = Column(String, ForeignKey("zones.slug"), nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g., "Domain Charge Party - January 2025"
    
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=True)  # None for ongoing events
    status = Column(String, nullable=False, default="draft", index=True)  # draft, active, closed
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    zone = relationship("Zone", foreign_keys=[zone_slug])
    charging_sessions = relationship("DomainChargingSession", back_populates="energy_event")
    
    __table_args__ = (
        Index('ix_energy_events_zone_status', 'zone_slug', 'status'),
    )


class DomainMerchant(Base):
    """Domain Charge Party merchant - separate from While You Charge merchants"""
    __tablename__ = "domain_merchants"
    
    id = Column(String, primary_key=True)  # UUID as string
    name = Column(String, nullable=False)
    google_place_id = Column(String, nullable=True)
    
    # Address
    addr_line1 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True, default="US")
    
    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    
    # Contact
    public_phone = Column(String, nullable=True)
    
    # Ownership
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Status
    status = Column(String, nullable=False, default="pending")  # pending, active, flagged, suspended
    
    # Nova balance (in smallest unit, e.g., cents or points)
    nova_balance = Column(Integer, nullable=False, default=0)
    
    # Zone (data-scoped, not path-scoped)
    zone_slug = Column(String, nullable=False, index=True)  # e.g., "domain_austin" (no FK for flexibility)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_user_id])
    transactions = relationship("NovaTransaction", back_populates="merchant")
    stripe_payments = relationship("StripePayment", back_populates="merchant")
    
    __table_args__ = (
        Index('ix_domain_merchants_zone_status', 'zone_slug', 'status'),
        Index('ix_domain_merchants_location', 'lat', 'lng'),
    )


class DriverWallet(Base):
    """Driver wallet - Nova balance and energy reputation"""
    __tablename__ = "driver_wallets"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    nova_balance = Column(Integer, nullable=False, default=0)  # in smallest unit
    energy_reputation_score = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    transactions = relationship("NovaTransaction", back_populates="driver")


class NovaTransaction(Base):
    """Nova transaction ledger - tracks all Nova movements"""
    __tablename__ = "nova_transactions"
    
    id = Column(String, primary_key=True)  # UUID as string
    type = Column(String, nullable=False)  # driver_earn, driver_redeem, merchant_topup, admin_grant
    
    # Parties involved
    driver_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    merchant_id = Column(String, ForeignKey("domain_merchants.id"), nullable=True, index=True)
    
    # Amount (always positive; type indicates direction)
    amount = Column(Integer, nullable=False)
    
    # References
    stripe_payment_id = Column(String, ForeignKey("stripe_payments.id"), nullable=True)
    session_id = Column(String, ForeignKey("domain_charging_sessions.id"), nullable=True)
    event_id = Column(String, ForeignKey("energy_events.id"), nullable=True, index=True)  # Optional event reference
    
    # Metadata (Python attribute is 'transaction_meta' to avoid SQLAlchemy reserved word 'metadata')
    # Database column name remains 'metadata' for backward compatibility
    transaction_meta = Column("metadata", JSON, nullable=True)  # Flexible JSON for additional context
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    driver = relationship("User", foreign_keys=[driver_user_id])
    merchant = relationship("DomainMerchant", foreign_keys=[merchant_id])
    stripe_payment = relationship("StripePayment", foreign_keys=[stripe_payment_id])
    charging_session = relationship("DomainChargingSession", foreign_keys=[session_id])
    energy_event = relationship("EnergyEvent", foreign_keys=[event_id])
    
    __table_args__ = (
        Index('ix_nova_transactions_type_created', 'type', 'created_at'),
    )


class DomainChargingSession(Base):
    """Domain Charge Party charging session"""
    __tablename__ = "domain_charging_sessions"
    
    id = Column(String, primary_key=True)  # UUID as string
    driver_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    charger_provider = Column(String, nullable=False, default="manual")  # tesla, manual, demo, etc.
    
    # Timing
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Charging details
    kwh_estimate = Column(Float, nullable=True)
    
    # Verification
    verified = Column(Boolean, nullable=False, default=False, index=True)
    verification_source = Column(String, nullable=True)  # tesla_api, manual_code, admin, demo
    
    # Event tracking (data-scoped, not path-scoped)
    event_id = Column(String, ForeignKey("energy_events.id"), nullable=True, index=True)  # Optional event reference
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    driver = relationship("User", foreign_keys=[driver_user_id])
    transactions = relationship("NovaTransaction", back_populates="charging_session")
    energy_event = relationship("EnergyEvent", back_populates="charging_sessions")


class StripePayment(Base):
    """Stripe payment records for merchant Nova purchases"""
    __tablename__ = "stripe_payments"
    
    id = Column(String, primary_key=True)  # UUID as string
    stripe_session_id = Column(String, nullable=False, unique=True)
    stripe_payment_intent_id = Column(String, nullable=True, index=True)
    
    merchant_id = Column(String, ForeignKey("domain_merchants.id"), nullable=True, index=True)
    
    amount_usd = Column(Integer, nullable=False)  # in cents
    nova_issued = Column(Integer, nullable=False)  # Nova amount
    
    status = Column(String, nullable=False, default="pending", index=True)  # pending, paid, failed
    
    stripe_event_id = Column(String, nullable=True, unique=True)  # for idempotency
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    merchant = relationship("DomainMerchant", foreign_keys=[merchant_id])
    transactions = relationship("NovaTransaction", back_populates="stripe_payment")
