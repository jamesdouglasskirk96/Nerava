"""Add wallet pass token and activity timestamps to driver_wallets

Revision ID: 023_add_wallet_pass_fields
Revises: 022_add_square_and_merchant_redemptions
Create Date: 2025-01-24 12:00:00.000000

This migration adds:
- wallet_pass_token: unique opaque token for Apple Wallet pass barcode
- wallet_activity_updated_at: timestamp bumped on any earn/spend
- wallet_pass_last_generated_at: timestamp set when pkpass created/refreshed

Backfill logic:
- wallet_pass_token: random token (secrets.token_urlsafe) for existing wallets
- wallet_activity_updated_at: NOW() if wallet has prior activity, else NULL
- wallet_pass_last_generated_at: NULL (no passes generated yet)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
import secrets


# revision identifiers, used by Alembic.
revision = "023_add_wallet_pass_fields"
down_revision = "022_add_square_and_merchant_redemptions"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    """Check if a table exists"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        columns = insp.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception:
        return False


def _has_index(table_name: str, index_name: str) -> bool:
    """Check if an index exists"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        indexes = insp.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)
    except Exception:
        return False


def upgrade() -> None:
    """Add wallet pass fields to driver_wallets table"""
    
    if not _has_table('driver_wallets'):
        # Table doesn't exist yet - skip migration (will be created by model)
        return
    
    # 1. Add wallet_pass_token column (nullable initially for backfill)
    if not _has_column('driver_wallets', 'wallet_pass_token'):
        op.add_column('driver_wallets', sa.Column('wallet_pass_token', sa.String(), nullable=True))
    
    # 2. Add wallet_activity_updated_at column
    if not _has_column('driver_wallets', 'wallet_activity_updated_at'):
        op.add_column('driver_wallets', sa.Column('wallet_activity_updated_at', sa.DateTime(), nullable=True))
    
    # 3. Add wallet_pass_last_generated_at column
    if not _has_column('driver_wallets', 'wallet_pass_last_generated_at'):
        op.add_column('driver_wallets', sa.Column('wallet_pass_last_generated_at', sa.DateTime(), nullable=True))
    
    # 4. Backfill wallet_pass_token for existing wallets
    # Generate random tokens for all existing wallets
    conn = op.get_bind()
    wallets = conn.execute(sa.text("SELECT user_id FROM driver_wallets WHERE wallet_pass_token IS NULL")).fetchall()
    
    for (user_id,) in wallets:
        # Generate random opaque token (24 bytes = 32 chars in base64)
        token = secrets.token_urlsafe(24)
        # Ensure uniqueness by checking if token already exists
        existing = conn.execute(
            sa.text("SELECT user_id FROM driver_wallets WHERE wallet_pass_token = :token"),
            {"token": token}
        ).fetchone()
        if existing:
            # If collision (unlikely), generate again
            token = secrets.token_urlsafe(24)
        conn.execute(
            sa.text("UPDATE driver_wallets SET wallet_pass_token = :token WHERE user_id = :user_id"),
            {"token": token, "user_id": user_id}
        )
    
    # 5. Backfill wallet_activity_updated_at
    # Set to NOW() if wallet has ANY prior activity (NovaTransaction OR MerchantRedemption)
    # Check if nova_transactions table exists
    if _has_table('nova_transactions'):
        conn.execute(sa.text("""
            UPDATE driver_wallets
            SET wallet_activity_updated_at = CURRENT_TIMESTAMP
            WHERE wallet_activity_updated_at IS NULL
            AND user_id IN (
                SELECT DISTINCT driver_user_id FROM nova_transactions WHERE driver_user_id IS NOT NULL
            )
        """))
    
    # Check if merchant_redemptions table exists
    if _has_table('merchant_redemptions'):
        conn.execute(sa.text("""
            UPDATE driver_wallets
            SET wallet_activity_updated_at = CURRENT_TIMESTAMP
            WHERE wallet_activity_updated_at IS NULL
            AND user_id IN (
                SELECT DISTINCT driver_user_id FROM merchant_redemptions WHERE driver_user_id IS NOT NULL
            )
        """))
    
    # 6. Add unique index on wallet_pass_token
    if not _has_index('driver_wallets', 'ix_driver_wallets_wallet_pass_token'):
        op.create_index('ix_driver_wallets_wallet_pass_token', 'driver_wallets', ['wallet_pass_token'], unique=True)
    
    # 7. Make wallet_pass_token NOT NULL after backfill
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    # For SQLite, we'll leave it nullable but ensure all rows have tokens
    # For other databases, we could make it NOT NULL, but for compatibility, keep nullable
    # The application logic will ensure tokens are created when needed


def downgrade() -> None:
    """Remove wallet pass fields from driver_wallets table"""
    
    if not _has_table('driver_wallets'):
        return
    
    # Remove index
    if _has_index('driver_wallets', 'ix_driver_wallets_wallet_pass_token'):
        op.drop_index('ix_driver_wallets_wallet_pass_token', table_name='driver_wallets')
    
    # Remove columns
    if _has_column('driver_wallets', 'wallet_pass_last_generated_at'):
        op.drop_column('driver_wallets', 'wallet_pass_last_generated_at')
    if _has_column('driver_wallets', 'wallet_activity_updated_at'):
        op.drop_column('driver_wallets', 'wallet_activity_updated_at')
    if _has_column('driver_wallets', 'wallet_pass_token'):
        op.drop_column('driver_wallets', 'wallet_pass_token')
