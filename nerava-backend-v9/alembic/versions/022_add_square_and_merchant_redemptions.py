"""Add Square fields, QR fields, merchant redemptions, and OAuth state table

Revision ID: 022_add_square_and_merchant_redemptions
Revises: 021_add_merchants_external_id_if_missing
Create Date: 2025-01-24 00:00:00.000000

This migration adds:
- Square integration fields to domain_merchants (square_merchant_id, square_location_id, square_access_token, square_connected_at)
- QR token fields to domain_merchants (qr_token, qr_created_at, qr_last_used_at)
- Perk configuration fields (avg_order_value_cents, recommended_perk_cents, custom_perk_cents, perk_label)
- merchant_redemptions table for tracking Nova redemptions
- square_oauth_states table for OAuth CSRF protection
- zone_slug field (renamed from domain_zone for consistency)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = "022_add_square_and_merchant_redemptions"
down_revision = "021_add_merchants_external_id_if_missing"
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
    """Add Square fields, QR fields, merchant redemptions table, and OAuth state table"""
    
    # 1. Add Square fields to domain_merchants (all nullable for backward compatibility)
    if _has_table('domain_merchants'):
        if not _has_column('domain_merchants', 'square_merchant_id'):
            op.add_column('domain_merchants', sa.Column('square_merchant_id', sa.String(), nullable=True))
        if not _has_column('domain_merchants', 'square_location_id'):
            op.add_column('domain_merchants', sa.Column('square_location_id', sa.String(), nullable=True))
        if not _has_column('domain_merchants', 'square_access_token'):
            op.add_column('domain_merchants', sa.Column('square_access_token', sa.Text(), nullable=True))
        if not _has_column('domain_merchants', 'square_connected_at'):
            op.add_column('domain_merchants', sa.Column('square_connected_at', sa.DateTime(), nullable=True))
        
        # Add indexes for Square fields
        if not _has_index('domain_merchants', 'ix_domain_merchants_square_merchant_id'):
            op.create_index('ix_domain_merchants_square_merchant_id', 'domain_merchants', ['square_merchant_id'])
        
        # 2. Add QR fields to domain_merchants
        if not _has_column('domain_merchants', 'qr_token'):
            op.add_column('domain_merchants', sa.Column('qr_token', sa.String(), nullable=True))
        if not _has_column('domain_merchants', 'qr_created_at'):
            op.add_column('domain_merchants', sa.Column('qr_created_at', sa.DateTime(), nullable=True))
        if not _has_column('domain_merchants', 'qr_last_used_at'):
            op.add_column('domain_merchants', sa.Column('qr_last_used_at', sa.DateTime(), nullable=True))
        
        # Add index for QR token
        if not _has_index('domain_merchants', 'ix_domain_merchants_qr_token'):
            op.create_index('ix_domain_merchants_qr_token', 'domain_merchants', ['qr_token'], unique=True)
        
        # 3. Add perk configuration fields
        if not _has_column('domain_merchants', 'avg_order_value_cents'):
            op.add_column('domain_merchants', sa.Column('avg_order_value_cents', sa.Integer(), nullable=True))
        if not _has_column('domain_merchants', 'recommended_perk_cents'):
            op.add_column('domain_merchants', sa.Column('recommended_perk_cents', sa.Integer(), nullable=True))
        if not _has_column('domain_merchants', 'custom_perk_cents'):
            op.add_column('domain_merchants', sa.Column('custom_perk_cents', sa.Integer(), nullable=True))
        if not _has_column('domain_merchants', 'perk_label'):
            op.add_column('domain_merchants', sa.Column('perk_label', sa.String(), nullable=True))
        
        # 4. Add zone_slug field (if domain_zone exists, migrate data)
        if not _has_column('domain_merchants', 'zone_slug'):
            op.add_column('domain_merchants', sa.Column('zone_slug', sa.String(), nullable=True))
            # Migrate data from domain_zone if it exists
            if _has_column('domain_merchants', 'domain_zone'):
                op.execute("UPDATE domain_merchants SET zone_slug = domain_zone WHERE zone_slug IS NULL")
            # Set default for any remaining NULLs
            op.execute("UPDATE domain_merchants SET zone_slug = 'national' WHERE zone_slug IS NULL")
            # Make it NOT NULL after migration
            op.alter_column('domain_merchants', 'zone_slug', nullable=False, server_default='national')
    
    # 5. Create merchant_redemptions table
    if not _has_table('merchant_redemptions'):
        op.create_table(
            'merchant_redemptions',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('merchant_id', sa.String(), sa.ForeignKey('domain_merchants.id'), nullable=False),
            sa.Column('driver_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('qr_token', sa.String(), nullable=True),
            sa.Column('order_total_cents', sa.Integer(), nullable=False),
            sa.Column('discount_cents', sa.Integer(), nullable=False),
            sa.Column('nova_spent_cents', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        
        # Indexes for merchant_redemptions
        op.create_index('ix_merchant_redemptions_merchant_id', 'merchant_redemptions', ['merchant_id'])
        op.create_index('ix_merchant_redemptions_driver_user_id', 'merchant_redemptions', ['driver_user_id'])
        op.create_index('ix_merchant_redemptions_qr_token', 'merchant_redemptions', ['qr_token'])
        op.create_index('ix_merchant_redemptions_merchant_created', 'merchant_redemptions', ['merchant_id', 'created_at'])
        op.create_index('ix_merchant_redemptions_driver_created', 'merchant_redemptions', ['driver_user_id', 'created_at'])
    
    # 6. Create square_oauth_states table
    if not _has_table('square_oauth_states'):
        op.create_table(
            'square_oauth_states',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('state', sa.String(), nullable=False, unique=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('used', sa.Boolean(), nullable=False, server_default='0'),
        )
        
        # Indexes for square_oauth_states
        op.create_index('ix_square_oauth_states_state', 'square_oauth_states', ['state'])
        op.create_index('ix_square_oauth_states_expires_at', 'square_oauth_states', ['expires_at'])
        op.create_index('ix_square_oauth_states_used', 'square_oauth_states', ['used'])


def downgrade() -> None:
    """Remove Square fields, QR fields, merchant redemptions table, and OAuth state table"""
    
    # Drop square_oauth_states table
    if _has_table('square_oauth_states'):
        op.drop_table('square_oauth_states')
    
    # Drop merchant_redemptions table
    if _has_table('merchant_redemptions'):
        op.drop_table('merchant_redemptions')
    
    # Remove columns from domain_merchants
    if _has_table('domain_merchants'):
        # Remove indexes first
        if _has_index('domain_merchants', 'ix_domain_merchants_qr_token'):
            op.drop_index('ix_domain_merchants_qr_token', table_name='domain_merchants')
        if _has_index('domain_merchants', 'ix_domain_merchants_square_merchant_id'):
            op.drop_index('ix_domain_merchants_square_merchant_id', table_name='domain_merchants')
        
        # Remove columns
        if _has_column('domain_merchants', 'zone_slug'):
            op.drop_column('domain_merchants', 'zone_slug')
        if _has_column('domain_merchants', 'perk_label'):
            op.drop_column('domain_merchants', 'perk_label')
        if _has_column('domain_merchants', 'custom_perk_cents'):
            op.drop_column('domain_merchants', 'custom_perk_cents')
        if _has_column('domain_merchants', 'recommended_perk_cents'):
            op.drop_column('domain_merchants', 'recommended_perk_cents')
        if _has_column('domain_merchants', 'avg_order_value_cents'):
            op.drop_column('domain_merchants', 'avg_order_value_cents')
        if _has_column('domain_merchants', 'qr_last_used_at'):
            op.drop_column('domain_merchants', 'qr_last_used_at')
        if _has_column('domain_merchants', 'qr_created_at'):
            op.drop_column('domain_merchants', 'qr_created_at')
        if _has_column('domain_merchants', 'qr_token'):
            op.drop_column('domain_merchants', 'qr_token')
        if _has_column('domain_merchants', 'square_connected_at'):
            op.drop_column('domain_merchants', 'square_connected_at')
        if _has_column('domain_merchants', 'square_access_token'):
            op.drop_column('domain_merchants', 'square_access_token')
        if _has_column('domain_merchants', 'square_location_id'):
            op.drop_column('domain_merchants', 'square_location_id')
        if _has_column('domain_merchants', 'square_merchant_id'):
            op.drop_column('domain_merchants', 'square_merchant_id')

