"""Add charging demo fields to driver_wallets

Revision ID: 025_add_charging_demo_fields
Revises: 024_add_wallet_pass_system
Create Date: 2025-02-01 12:00:00.000000

This migration adds demo-only charging detection fields:
- charging_detected (bool, default false)
- charging_detected_at (datetime, nullable)

These fields are for sandbox/demo flows only and do not affect production behavior.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "025_add_charging_demo_fields"
down_revision = "024_add_wallet_pass_system"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        columns = insp.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception:
        return False


def upgrade() -> None:
    """Add charging demo fields to driver_wallets table."""
    
    if not _has_table('driver_wallets'):
        # Table doesn't exist yet - skip migration (will be created by model)
        return
    
    # Add charging_detected column (bool, default false)
    if not _has_column('driver_wallets', 'charging_detected'):
        op.add_column('driver_wallets', sa.Column('charging_detected', sa.Boolean(), nullable=False, server_default='0'))
    
    # Add charging_detected_at column (nullable datetime)
    if not _has_column('driver_wallets', 'charging_detected_at'):
        op.add_column('driver_wallets', sa.Column('charging_detected_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove charging demo fields from driver_wallets table."""
    
    if not _has_table('driver_wallets'):
        return
    
    # Remove columns
    if _has_column('driver_wallets', 'charging_detected_at'):
        op.drop_column('driver_wallets', 'charging_detected_at')
    if _has_column('driver_wallets', 'charging_detected'):
        op.drop_column('driver_wallets', 'charging_detected')

