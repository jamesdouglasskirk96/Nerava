"""Add user_consents table

Revision ID: 059_add_user_consents_table
Revises: 058_add_chargers_spatial_index
Create Date: 2026-01-27 20:00:00.000000

Adds user_consents table for GDPR compliance consent tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '059_add_user_consents_table'
down_revision = '058_add_chargers_spatial_index'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user_consents table with unique constraint"""
    op.create_table(
        'user_consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('consent_type', sa.String(length=50), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on user_id
    op.create_index(
        'ix_user_consents_user_id',
        'user_consents',
        ['user_id']
    )
    
    # Create unique index on (user_id, consent_type)
    op.create_index(
        'ix_user_consents_user_type',
        'user_consents',
        ['user_id', 'consent_type'],
        unique=True
    )


def downgrade() -> None:
    """Remove user_consents table"""
    op.drop_index('ix_user_consents_user_type', table_name='user_consents')
    op.drop_index('ix_user_consents_user_id', table_name='user_consents')
    op.drop_table('user_consents')
