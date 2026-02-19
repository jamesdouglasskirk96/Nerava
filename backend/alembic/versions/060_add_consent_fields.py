"""Add ip_address and privacy_policy_version to user_consents

Revision ID: 060_add_consent_fields
Revises: 059_add_user_consents_table
Create Date: 2026-01-27 21:00:00.000000

Adds ip_address and privacy_policy_version fields to user_consents table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '060_add_consent_fields'
down_revision = '059_add_user_consents_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ip_address and privacy_policy_version columns"""
    op.add_column('user_consents', sa.Column('ip_address', sa.String(), nullable=True))
    op.add_column('user_consents', sa.Column('privacy_policy_version', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove ip_address and privacy_policy_version columns"""
    op.drop_column('user_consents', 'privacy_policy_version')
    op.drop_column('user_consents', 'ip_address')
