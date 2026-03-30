"""Add charger_availability_snapshots table

Revision ID: 117
Revises: 116
"""
from alembic import op
import sqlalchemy as sa

revision = "117"
down_revision = "116"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "charger_availability_snapshots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("charger_id", sa.String(), nullable=False, index=True),
        sa.Column("tomtom_availability_id", sa.String(), nullable=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("total_ports", sa.Integer(), nullable=True),
        sa.Column("available_ports", sa.Integer(), nullable=True),
        sa.Column("occupied_ports", sa.Integer(), nullable=True),
        sa.Column("out_of_service_ports", sa.Integer(), nullable=True),
        sa.Column("connector_details", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_avail_charger_recorded", "charger_availability_snapshots", ["charger_id", "recorded_at"])


def downgrade():
    op.drop_index("ix_avail_charger_recorded", table_name="charger_availability_snapshots")
    op.drop_table("charger_availability_snapshots")
