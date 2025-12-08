"""Create users table if missing

Revision ID: d0dc1d5111a3
Revises: 020
Create Date: 2025-12-08 01:22:52.129525

This migration creates the core users and user_preferences tables if they don't exist.
These tables are required for authentication and were never created by a previous migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = 'd0dc1d5111a3'
down_revision: Union[str, Sequence[str], None] = '020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    """Check if a table exists"""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    """Create users and user_preferences tables if they don't exist"""
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    # Use JSON for Postgres, TEXT for SQLite (SQLite doesn't have native JSON)
    json_type = sa.JSON() if not is_sqlite else sa.Text()
    
    # 1. Create users table
    if not _has_table('users'):
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('email', sa.String(), nullable=False, unique=True),
            sa.Column('password_hash', sa.String(), nullable=True),  # nullable for magic-link users
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('display_name', sa.String(), nullable=True),
            sa.Column('role_flags', sa.String(), nullable=True, server_default='driver'),
            sa.Column('auth_provider', sa.String(), nullable=False, server_default='local'),
            sa.Column('oauth_sub', sa.String(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
        # Create index on email (unique constraint already creates an index, but explicit is clearer)
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # 2. Create user_preferences table (depends on users)
    if not _has_table('user_preferences'):
        op.create_table(
            'user_preferences',
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False),
            sa.Column('food_tags', json_type, nullable=False, server_default='[]'),
            sa.Column('max_detour_minutes', sa.Integer(), nullable=False, server_default='10'),
            sa.Column('preferred_networks', json_type, nullable=False, server_default='[]'),
            sa.Column('typical_start', sa.Time(), nullable=False, server_default=sa.text("'18:00:00'")),
            sa.Column('typical_end', sa.Time(), nullable=False, server_default=sa.text("'22:00:00'")),
            sa.Column('home_zip', sa.String(), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema - conservative: don't drop users table automatically"""
    # Be conservative: don't drop the users table on downgrade
    # If you need to drop it, do it manually
    pass
