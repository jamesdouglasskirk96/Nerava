"""add primary merchant override

Revision ID: 049_add_primary_merchant_override
Revises: 048_add_exclusive_sessions
Create Date: 2025-01-27 14:00:00.000000

Adds primary merchant override fields to merchants and charger_merchants tables
for Google Places enrichment and charger-specific merchant prioritization
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '049_add_primary_merchant_override'
down_revision = '048_add_exclusive_sessions'
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str, inspector) -> bool:
    """Check if a column exists in a table"""
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def _index_exists(table_name: str, index_name: str, inspector) -> bool:
    """Check if an index exists on a table"""
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    """Add primary merchant override fields"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    inspector = sa.inspect(bind)
    
    # DateTime with timezone support
    datetime_type = sa.DateTime(timezone=True) if dialect_name != 'sqlite' else sa.DateTime()
    
    # JSON type handling
    json_type = sa.JSON() if dialect_name != 'sqlite' else sqlite.JSON()
    
    # Add columns to merchants table (check if they exist first)
    if not _column_exists('merchants', 'place_id', inspector):
        op.add_column('merchants', sa.Column('place_id', sa.String(), nullable=True))
    if not _column_exists('merchants', 'primary_photo_url', inspector):
        op.add_column('merchants', sa.Column('primary_photo_url', sa.String(), nullable=True))
    if not _column_exists('merchants', 'photo_urls', inspector):
        op.add_column('merchants', sa.Column('photo_urls', json_type, nullable=True))
    if not _column_exists('merchants', 'user_rating_count', inspector):
        op.add_column('merchants', sa.Column('user_rating_count', sa.Integer(), nullable=True))
    if not _column_exists('merchants', 'business_status', inspector):
        op.add_column('merchants', sa.Column('business_status', sa.String(), nullable=True))
    if not _column_exists('merchants', 'open_now', inspector):
        op.add_column('merchants', sa.Column('open_now', sa.Boolean(), nullable=True))
    if not _column_exists('merchants', 'hours_json', inspector):
        op.add_column('merchants', sa.Column('hours_json', json_type, nullable=True))
    if not _column_exists('merchants', 'google_places_updated_at', inspector):
        op.add_column('merchants', sa.Column('google_places_updated_at', datetime_type, nullable=True))
    if not _column_exists('merchants', 'last_status_check', inspector):
        op.add_column('merchants', sa.Column('last_status_check', datetime_type, nullable=True))
    
    # Add columns to charger_merchants table (check if they exist first)
    if not _column_exists('charger_merchants', 'is_primary', inspector):
        op.add_column('charger_merchants', sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='0'))
    if not _column_exists('charger_merchants', 'override_mode', inspector):
        op.add_column('charger_merchants', sa.Column('override_mode', sa.String(), nullable=True))
    if not _column_exists('charger_merchants', 'suppress_others', inspector):
        op.add_column('charger_merchants', sa.Column('suppress_others', sa.Boolean(), nullable=False, server_default='0'))
    if not _column_exists('charger_merchants', 'exclusive_title', inspector):
        op.add_column('charger_merchants', sa.Column('exclusive_title', sa.String(), nullable=True))
    if not _column_exists('charger_merchants', 'exclusive_description', inspector):
        op.add_column('charger_merchants', sa.Column('exclusive_description', sa.Text(), nullable=True))
    
    # Create indexes (check if they exist first)
    if not _index_exists('merchants', 'ix_merchants_place_id', inspector):
        op.create_index('ix_merchants_place_id', 'merchants', ['place_id'], unique=True)
    if not _index_exists('charger_merchants', 'ix_charger_merchants_is_primary', inspector):
        op.create_index('ix_charger_merchants_is_primary', 'charger_merchants', ['is_primary'])
    if not _index_exists('charger_merchants', 'idx_charger_merchant_primary', inspector):
        op.create_index('idx_charger_merchant_primary', 'charger_merchants', ['charger_id', 'is_primary'])


def downgrade() -> None:
    """Remove primary merchant override fields"""
    op.drop_index('idx_charger_merchant_primary', table_name='charger_merchants')
    op.drop_index('ix_charger_merchants_is_primary', table_name='charger_merchants')
    op.drop_index('ix_merchants_place_id', table_name='merchants')
    
    op.drop_column('charger_merchants', 'exclusive_description')
    op.drop_column('charger_merchants', 'exclusive_title')
    op.drop_column('charger_merchants', 'suppress_others')
    op.drop_column('charger_merchants', 'override_mode')
    op.drop_column('charger_merchants', 'is_primary')
    
    op.drop_column('merchants', 'last_status_check')
    op.drop_column('merchants', 'google_places_updated_at')
    op.drop_column('merchants', 'hours_json')
    op.drop_column('merchants', 'open_now')
    op.drop_column('merchants', 'business_status')
    op.drop_column('merchants', 'user_rating_count')
    op.drop_column('merchants', 'photo_urls')
    op.drop_column('merchants', 'primary_photo_url')
    op.drop_column('merchants', 'place_id')


