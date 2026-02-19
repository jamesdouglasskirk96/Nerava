"""Add composite spatial index on chargers

Revision ID: 058_add_chargers_spatial_index
Revises: 057_make_nova_transactions_idempotency_unique
Create Date: 2026-01-27 19:00:00.000000

Adds composite index on (is_public, lat, lng) for spatial query performance
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '058_add_chargers_spatial_index'
down_revision = '057_make_nova_transactions_idempotency_unique'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite spatial index on chargers"""
    op.create_index(
        "ix_chargers_public_lat_lng",
        "chargers",
        ["is_public", "lat", "lng"]
    )


def downgrade() -> None:
    """Remove composite spatial index"""
    op.drop_index("ix_chargers_public_lat_lng", table_name="chargers")
