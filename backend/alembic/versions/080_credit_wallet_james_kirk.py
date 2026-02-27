"""Credit wallet $5.73 for james.douglass.kirk@gmail.com

Revision ID: 080
Revises: 079
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime

revision = '080_credit_wallet'
down_revision = '079_charger_composite_index'
branch_labels = None
depends_on = None


def upgrade():
    # Already applied in production - no-op
    pass


def downgrade():
    # No-op: manual credit is not reversible via migration
    pass
