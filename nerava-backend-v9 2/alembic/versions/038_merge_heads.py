"""merge heads

Revision ID: 038_merge_heads
Revises: 037_add_merchant_category_and_nearest_charger, 4899c9259e64
Create Date: 2025-01-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '038_merge_heads'
down_revision: Union[str, Sequence[str], None] = ('037_add_merchant_category_and_nearest_charger', '4899c9259e64')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads - no schema changes."""
    pass


def downgrade() -> None:
    """Downgrade - no schema changes."""
    pass
