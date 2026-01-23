"""Add cap and time window fields to merchant exclusives

Revision ID: 050_exclusive_caps
Revises: 049_add_merchant_details_fields
Create Date: 2025-01-27 14:00:00.000000

Adds daily_cap, start_time, end_time, days_of_week, and staff_notes fields to merchant_perks table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '050_exclusive_caps'
down_revision = '049_add_merchant_details_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Add cap and time window fields to merchant_perks table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Check which columns already exist
    from sqlalchemy import inspect
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('merchant_perks')]
    
    # Only add columns that don't exist
    if 'daily_cap' not in existing_columns:
        op.add_column('merchant_perks', sa.Column('daily_cap', sa.Integer(), nullable=True))
    if 'start_time' not in existing_columns:
        op.add_column('merchant_perks', sa.Column('start_time', sa.Time(), nullable=True))
    if 'end_time' not in existing_columns:
        op.add_column('merchant_perks', sa.Column('end_time', sa.Time(), nullable=True))
    if 'days_of_week' not in existing_columns:
        op.add_column('merchant_perks', sa.Column('days_of_week', sa.String(20), nullable=True))  # "1,2,3,4,5" for Mon-Fri
    if 'staff_notes' not in existing_columns:
        op.add_column('merchant_perks', sa.Column('staff_notes', sa.Text(), nullable=True))


def downgrade():
    """Remove cap and time window fields from merchant_perks table"""
    op.drop_column('merchant_perks', 'staff_notes')
    op.drop_column('merchant_perks', 'days_of_week')
    op.drop_column('merchant_perks', 'end_time')
    op.drop_column('merchant_perks', 'start_time')
    op.drop_column('merchant_perks', 'daily_cap')

