"""Add sponsor campaign tables (campaigns, impressions, driver limits)

Revision ID: 116
Revises: 115
"""
from alembic import op
import sqlalchemy as sa

try:
    from sqlalchemy import JSON
except Exception:
    from sqlalchemy.dialects.sqlite import JSON

revision = "116"
down_revision = "115"
branch_labels = None
depends_on = None


def upgrade():
    # Use String for UUID columns to support both SQLite and PostgreSQL
    op.create_table(
        "sponsor_campaigns",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("sponsor_name", sa.String(), nullable=False),
        sa.Column("sponsor_category", sa.String(20), nullable=True),
        sa.Column("message_title", sa.String(50), nullable=False),
        sa.Column("message_body", sa.String(100), nullable=False),
        sa.Column("cta_label", sa.String(30), nullable=True),
        sa.Column("cta_url", sa.String(500), nullable=True),
        sa.Column("target_clusters", JSON(), nullable=True),
        sa.Column("target_vehicle_types", JSON(), nullable=True),
        sa.Column("target_min_session_minutes", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("budget_total", sa.Float(), nullable=False),
        sa.Column("budget_remaining", sa.Float(), nullable=False),
        sa.Column("cost_per_impression", sa.Float(), nullable=False),
        sa.Column("impressions_served", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("trigger_type", sa.String(20), nullable=False, server_default="session_start"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_sponsor_campaign_status", "sponsor_campaigns", ["status"])
    op.create_index("idx_sponsor_campaign_trigger", "sponsor_campaigns", ["trigger_type"])

    op.create_table(
        "sponsor_impressions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("campaign_id", sa.String(), nullable=False, index=True),
        sa.Column("driver_id_hash", sa.String(), nullable=False),
        sa.Column("cluster_id", sa.String(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=False),
        sa.Column("clicked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_impression_campaign", "sponsor_impressions", ["campaign_id", "delivered_at"])
    op.create_index("idx_impression_driver", "sponsor_impressions", ["driver_id_hash", "delivered_at"])

    op.create_table(
        "sponsor_driver_limits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("driver_id_hash", sa.String(), nullable=False, index=True),
        sa.Column("week_start", sa.String(10), nullable=False),
        sa.Column("impression_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("idx_driver_limit_week", "sponsor_driver_limits",
                     ["driver_id_hash", "week_start"], unique=True)


def downgrade():
    op.drop_table("sponsor_driver_limits")
    op.drop_table("sponsor_impressions")
    op.drop_table("sponsor_campaigns")
