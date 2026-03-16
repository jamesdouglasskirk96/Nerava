"""Make campaigns.sponsor_id nullable

The campaigns table was originally created by metadata.create_all() which
included a sponsor_id NOT NULL column. This column is not in the current
Campaign model (sponsor info is stored as inline columns like sponsor_name).
Make it nullable so inserts don't fail.

Revision ID: 103_make_campaigns_sponsor_id_nullable
Revises: 102_add_ad_impressions
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

revision = "103_make_campaigns_sponsor_id_nullable"
down_revision = "102_add_ad_impressions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)

    if "campaigns" not in inspector.get_table_names():
        return

    columns = {c["name"]: c for c in inspector.get_columns("campaigns")}
    if "sponsor_id" in columns:
        op.alter_column("campaigns", "sponsor_id", nullable=True)


def downgrade() -> None:
    pass
