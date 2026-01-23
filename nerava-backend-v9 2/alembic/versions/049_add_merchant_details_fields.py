"""Add merchant details fields

Revision ID: 049_add_merchant_details_fields
Revises: 048_add_exclusive_sessions
Create Date: 2025-01-27 13:00:00.000000

Adds description, user_rating_count, photo_urls, opening_hours, and place_id fields to merchants table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '049_add_merchant_details_fields'
down_revision = '048_add_exclusive_sessions'
branch_labels = None
depends_on = None


def upgrade():
    """Add merchant details fields to merchants table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # JSON type handling (SQLite uses TEXT, PostgreSQL uses JSON)
    json_type = postgresql.JSON() if dialect_name != 'sqlite' else sa.Text()
    
    # Check which columns already exist
    from sqlalchemy import inspect, text
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('merchants')]
    
    # Only add columns that don't exist
    if 'description' not in existing_columns:
        op.add_column('merchants', sa.Column('description', sa.Text(), nullable=True))
    if 'user_rating_count' not in existing_columns:
        op.add_column('merchants', sa.Column('user_rating_count', sa.Integer(), nullable=True))
    if 'photo_urls' not in existing_columns:
        op.add_column('merchants', sa.Column('photo_urls', json_type, nullable=True))
    if 'opening_hours' not in existing_columns:
        op.add_column('merchants', sa.Column('opening_hours', json_type, nullable=True))
    if 'place_id' not in existing_columns:
        op.add_column('merchants', sa.Column('place_id', sa.String(), nullable=True))
    
    # Add index on place_id if it doesn't exist
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('merchants')]
    if 'ix_merchants_place_id' not in existing_indexes:
        op.create_index('ix_merchants_place_id', 'merchants', ['place_id'], unique=False)


def downgrade():
    """Remove merchant details fields from merchants table"""
    op.drop_index('ix_merchants_place_id', table_name='merchants')
    op.drop_column('merchants', 'place_id')
    op.drop_column('merchants', 'opening_hours')
    op.drop_column('merchants', 'photo_urls')
    op.drop_column('merchants', 'user_rating_count')
    op.drop_column('merchants', 'description')

