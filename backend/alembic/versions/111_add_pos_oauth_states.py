"""Add pos_oauth_states table for Toast/POS OAuth CSRF protection.

Revision ID: 111
Revises: 110
"""
from alembic import op
import sqlalchemy as sa

revision = "111"
down_revision = "110"


def upgrade():
    op.create_table(
        "pos_oauth_states",
        sa.Column("state", sa.String(64), primary_key=True),
        sa.Column("data_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
    )
    op.create_index("idx_pos_oauth_states_expires", "pos_oauth_states", ["expires_at"])


def downgrade():
    op.drop_index("idx_pos_oauth_states_expires")
    op.drop_table("pos_oauth_states")
