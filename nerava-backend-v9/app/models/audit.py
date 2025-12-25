"""
Admin Audit Log Model

Tracks all wallet mutations and admin actions for audit purposes.
P1-1: Admin audit log for all wallet mutations + admin actions.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, ForeignKey
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from ..db import Base

try:
    from sqlalchemy import JSON  # for non-sqlite engines
except Exception:
    JSON = SQLITE_JSON  # fallback for sqlite


class AdminAuditLog(Base):
    """Admin audit log for tracking all wallet mutations and admin actions"""
    __tablename__ = "admin_audit_logs"
    
    id = Column(String, primary_key=True)  # UUID as string
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # "wallet_credit", "wallet_debit", "admin_adjust", etc.
    target_type = Column(String, nullable=False)  # "wallet", "merchant_balance", "user", etc.
    target_id = Column(String, nullable=False, index=True)
    before_json = Column(JSON, nullable=True)  # State before mutation
    after_json = Column(JSON, nullable=True)  # State after mutation
    metadata_json = Column(JSON, nullable=True)  # Additional metadata (filtered to exclude secrets)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('ix_admin_audit_logs_actor_created', 'actor_id', 'created_at'),
        Index('ix_admin_audit_logs_target_created', 'target_type', 'target_id', 'created_at'),
        Index('ix_admin_audit_logs_action_created', 'action', 'created_at'),
    )

