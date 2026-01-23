"""Add verify fields to sessions table

Revision ID: 006
Revises: 005
Create Date: 2025-01-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to sessions table for verify flow
    try:
        op.add_column('sessions', sa.Column('status', sa.String(50), nullable=True, server_default='started'))
        op.add_column('sessions', sa.Column('lat', sa.Float(), nullable=True))
        op.add_column('sessions', sa.Column('lng', sa.Float(), nullable=True))
        op.add_column('sessions', sa.Column('accuracy_m', sa.Float(), nullable=True))
        op.add_column('sessions', sa.Column('verified_at', sa.DateTime(), nullable=True))
        op.add_column('sessions', sa.Column('charger_id', sa.String(200), nullable=True))
        op.add_column('sessions', sa.Column('started_at', sa.DateTime(), nullable=True))
        # Add index for status lookups
        op.create_index('idx_sessions_status', 'sessions', ['status'])
    except Exception:
        # Columns might already exist
        pass


def downgrade():
    try:
        op.drop_index('idx_sessions_status', 'sessions')
        op.drop_column('sessions', 'started_at')
        op.drop_column('sessions', 'charger_id')
        op.drop_column('sessions', 'verified_at')
        op.drop_column('sessions', 'accuracy_m')
        op.drop_column('sessions', 'lng')
        op.drop_column('sessions', 'lat')
        op.drop_column('sessions', 'status')
    except Exception:
        pass

