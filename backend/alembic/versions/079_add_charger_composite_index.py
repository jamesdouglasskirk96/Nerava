"""Add charger composite index for spatial queries

Revision ID: 079_charger_composite_index
Revises: None (standalone)
Create Date: 2026-02-25
"""
from alembic import op

# revision identifiers
revision = '079_charger_composite_index'
down_revision = '078_tesla_oauth_states'
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.create_index('idx_chargers_public_location', 'chargers', ['is_public', 'lat', 'lng'])
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index('idx_chargers_public_location', table_name='chargers')
