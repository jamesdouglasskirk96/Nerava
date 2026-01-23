"""merge production auth v1

Revision ID: 4899c9259e64
Revises: d0dc1d5111a3, 028_production_auth_v1
Create Date: 2025-12-17 15:56:57.953978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4899c9259e64'
down_revision: Union[str, Sequence[str], None] = ('d0dc1d5111a3', '028_production_auth_v1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
