"""Add charger intelligence tables (availability, cluster scores, history)

Revision ID: 115
Revises: 114
"""
from alembic import op
import sqlalchemy as sa

try:
    from sqlalchemy import JSON
except Exception:
    from sqlalchemy.dialects.sqlite import JSON

revision = "115"
down_revision = "114"
branch_labels = None
depends_on = None


def upgrade():
    # charger_availability
    op.create_table(
        "charger_availability",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("charger_id", sa.String(), nullable=False, index=True),
        sa.Column("tomtom_id", sa.String(), nullable=True, index=True),
        sa.Column("availability_status", sa.String(20), nullable=True),
        sa.Column("available_ports", sa.Integer(), nullable=True),
        sa.Column("total_ports", sa.Integer(), nullable=True),
        sa.Column("last_availability_update", sa.DateTime(), nullable=True),
        sa.Column("nevi_funded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("nevi_station_id", sa.String(), nullable=True, index=True),
        sa.Column("real_time_status", JSON(), nullable=True),
        sa.Column("last_nevi_update", sa.DateTime(), nullable=True),
        sa.Column("pricing_raw_text", sa.Text(), nullable=True),
        sa.Column("pricing_per_kwh", sa.Float(), nullable=True),
        sa.Column("session_fee", sa.Float(), nullable=True),
        sa.Column("pricing_model", sa.String(20), nullable=True),
        sa.Column("pricing_last_updated", sa.DateTime(), nullable=True),
        sa.Column("ocm_usage_cost", sa.Text(), nullable=True),
        sa.Column("ocm_usage_cost_parsed", sa.Float(), nullable=True),
        sa.Column("ocm_last_updated", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # cluster_scores
    op.create_table(
        "cluster_scores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cluster_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("charger_ids", JSON(), nullable=False),
        sa.Column("centroid_lat", sa.Float(), nullable=False),
        sa.Column("centroid_lng", sa.Float(), nullable=False),
        sa.Column("total_ports", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_weekly_occupancy_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("peak_hour_start", sa.Integer(), nullable=True),
        sa.Column("peak_hour_end", sa.Integer(), nullable=True),
        sa.Column("peak_day_of_week", sa.Integer(), nullable=True),
        sa.Column("nearby_nerava_merchants", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pricing_tier", sa.String(10), nullable=True),
        sa.Column("tier_score", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_scored", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_cluster_score_tier", "cluster_scores", ["tier_score"])
    op.create_index("idx_cluster_score_location", "cluster_scores", ["centroid_lat", "centroid_lng"])

    # charger_availability_history
    op.create_table(
        "charger_availability_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cluster_id", sa.String(), nullable=False, index=True),
        sa.Column("date", sa.String(10), nullable=False),
        sa.Column("peak_occupancy_pct", sa.Float(), nullable=True),
        sa.Column("avg_occupancy_pct", sa.Float(), nullable=True),
        sa.Column("out_of_service_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_sessions_observed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_avail_history_cluster_date", "charger_availability_history",
                     ["cluster_id", "date"], unique=True)


def downgrade():
    op.drop_table("charger_availability_history")
    op.drop_table("cluster_scores")
    op.drop_table("charger_availability")
