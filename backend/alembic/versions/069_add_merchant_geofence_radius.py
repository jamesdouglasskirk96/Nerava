"""Add geofence radius to merchants

Revision ID: 069
Revises: 068
Create Date: 2026-02-09

Adds geofence_radius_m column to merchants table for configurable arrival detection radius.
"""
from alembic import op
import sqlalchemy as sa

revision = '069'
down_revision = '068'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('merchants', sa.Column('geofence_radius_m', sa.Integer(), server_default='150', nullable=True))


def downgrade():
    op.drop_column('merchants', 'geofence_radius_m')
