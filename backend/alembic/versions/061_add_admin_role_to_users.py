"""Add admin_role to users table

Revision ID: 061_add_admin_role_to_users
Revises: 060_add_consent_fields
Create Date: 2026-01-28 00:00:00.000000

Adds admin_role column to users table for RBAC
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '061_add_admin_role_to_users'
down_revision = '060_add_consent_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add admin_role column to users table"""
    op.add_column('users', sa.Column('admin_role', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove admin_role column from users table"""
    op.drop_column('users', 'admin_role')
