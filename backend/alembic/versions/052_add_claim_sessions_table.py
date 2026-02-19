"""add claim_sessions table

Revision ID: 052_add_claim_sessions_table
Revises: 051_add_favorite_merchants_table
Create Date: 2026-01-23 12:00:00.000000

Adds claim_sessions table for merchant business claim flow
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '052_add_claim_sessions_table'
down_revision = '051_add_favorite_merchants_table'
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
    """Add claim_sessions table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # DateTime with timezone support
    datetime_type = sa.DateTime(timezone=True) if dialect_name != 'sqlite' else sa.DateTime()

    # UUID type - use String(36) for SQLite, UUID for PostgreSQL
    uuid_type = sa.String(36) if dialect_name == 'sqlite' else sa.String()

    # Create claim_sessions table (skip if exists)
    if not _table_exists('claim_sessions', bind):
        op.create_table(
            'claim_sessions',
            sa.Column('id', uuid_type, primary_key=True),
            sa.Column('merchant_id', uuid_type, nullable=False),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('phone', sa.String(20), nullable=False),
            sa.Column('business_name', sa.String(255), nullable=False),
            sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('magic_link_token', sa.String(255), nullable=True),
            sa.Column('magic_link_expires_at', datetime_type, nullable=True),
            sa.Column('created_at', datetime_type, nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', datetime_type, nullable=True, onupdate=sa.func.now()),
            sa.Column('completed_at', datetime_type, nullable=True),
            sa.ForeignKeyConstraint(['merchant_id'], ['domain_merchants.id'], ondelete='CASCADE'),
        )

    # Create indexes (skip if exist)
    if not _index_exists('claim_sessions', 'ix_claim_sessions_merchant_id', bind):
        op.create_index('ix_claim_sessions_merchant_id', 'claim_sessions', ['merchant_id'])
    if not _index_exists('claim_sessions', 'ix_claim_sessions_magic_link_token', bind):
        op.create_index('ix_claim_sessions_magic_link_token', 'claim_sessions', ['magic_link_token'], unique=True)
    if not _index_exists('claim_sessions', 'ix_claim_sessions_email', bind):
        op.create_index('ix_claim_sessions_email', 'claim_sessions', ['email'])
    if not _index_exists('claim_sessions', 'ix_claim_sessions_phone', bind):
        op.create_index('ix_claim_sessions_phone', 'claim_sessions', ['phone'])


def downgrade() -> None:
    """Remove claim_sessions table"""
    op.drop_index('ix_claim_sessions_phone', table_name='claim_sessions')
    op.drop_index('ix_claim_sessions_email', table_name='claim_sessions')
    op.drop_index('ix_claim_sessions_magic_link_token', table_name='claim_sessions')
    op.drop_index('ix_claim_sessions_merchant_id', table_name='claim_sessions')
    op.drop_table('claim_sessions')




