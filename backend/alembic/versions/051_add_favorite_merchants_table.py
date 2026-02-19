"""add favorite merchants table

Revision ID: 051_add_favorite_merchants_table
Revises: 050_add_outbox_retry_fields
Create Date: 2025-01-27 15:00:00.000000

Adds favorite_merchants table for user favorites functionality
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '051_add_favorite_merchants_table'
down_revision = '050_add_outbox_retry_fields'
branch_labels = None
depends_on = None


def _table_exists(table_name: str, bind) -> bool:
    """Check if a table exists"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str, bind) -> bool:
    """Check if an index exists on a table"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    """Add favorite_merchants table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # DateTime with timezone support
    datetime_type = sa.DateTime(timezone=True) if dialect_name != 'sqlite' else sa.DateTime()

    # Create favorite_merchants table (skip if exists)
    if not _table_exists('favorite_merchants', bind):
        op.create_table(
            'favorite_merchants',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('merchant_id', sa.String(), nullable=False),
            sa.Column('created_at', datetime_type, nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # Create indexes (skip if exist)
    if not _index_exists('favorite_merchants', 'idx_favorite_merchant_unique', bind):
        op.create_index('idx_favorite_merchant_unique', 'favorite_merchants', ['user_id', 'merchant_id'], unique=True)
    if not _index_exists('favorite_merchants', 'idx_favorite_merchant_user', bind):
        op.create_index('idx_favorite_merchant_user', 'favorite_merchants', ['user_id'])
    if not _index_exists('favorite_merchants', 'idx_favorite_merchant_merchant', bind):
        op.create_index('idx_favorite_merchant_merchant', 'favorite_merchants', ['merchant_id'])


def downgrade() -> None:
    """Remove favorite_merchants table"""
    op.drop_index('idx_favorite_merchant_merchant', table_name='favorite_merchants')
    op.drop_index('idx_favorite_merchant_user', table_name='favorite_merchants')
    op.drop_index('idx_favorite_merchant_unique', table_name='favorite_merchants')
    op.drop_table('favorite_merchants')






