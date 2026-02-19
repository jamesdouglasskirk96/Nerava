"""Add intent fields to exclusive_sessions table

Revision ID: 054
Revises: 053_add_verified_visits
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '054'
down_revision = '053_add_verified_visits'
branch_labels = None
depends_on = None


def upgrade():
    """Add intent columns to exclusive_sessions table"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Check if columns already exist (for idempotency)
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('exclusive_sessions')]
    
    # Add intent column (works for both SQLite and PostgreSQL)
    if 'intent' not in columns:
        op.add_column('exclusive_sessions', sa.Column('intent', sa.String(50), nullable=True))
    
    # Add intent_metadata column - use JSONB for PostgreSQL, JSON/Text for SQLite
    if 'intent_metadata' not in columns:
        if dialect_name == 'postgresql':
            op.add_column('exclusive_sessions', sa.Column('intent_metadata', JSONB, nullable=True))
        else:
            # SQLite doesn't support JSONB, use JSON or Text
            op.add_column('exclusive_sessions', sa.Column('intent_metadata', sa.JSON, nullable=True))


def downgrade():
    op.drop_column('exclusive_sessions', 'intent_metadata')
    op.drop_column('exclusive_sessions', 'intent')
