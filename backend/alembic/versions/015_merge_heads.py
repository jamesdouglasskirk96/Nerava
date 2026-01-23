"""Merge heads 011_events_pool_notify and 014_add_merchant_columns"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "015_merge_heads"
down_revision = ("011_events_pool_notify", "014_add_merchant_columns")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

