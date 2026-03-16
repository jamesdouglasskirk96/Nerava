"""Add gross_funding_cents and platform_fee_cents to campaigns

Revision ID: 108_add_campaign_platform_fee
Revises: 107_add_charger_cable_telemetry
"""
from alembic import op
import sqlalchemy as sa

revision = "108_add_campaign_platform_fee"
down_revision = "107_add_charger_cable_telemetry"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("campaigns") as batch_op:
        batch_op.add_column(sa.Column("gross_funding_cents", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("platform_fee_cents", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("campaigns") as batch_op:
        batch_op.drop_column("platform_fee_cents")
        batch_op.drop_column("gross_funding_cents")
