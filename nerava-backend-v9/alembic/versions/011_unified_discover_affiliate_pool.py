"""unified discover + affiliate + pool + events v2"""
from alembic import op
import sqlalchemy as sa


revision = "011_unified_discover_affiliate_pool"
down_revision = "010_merchant_keys"
branch_labels = None
depends_on = None


def _add_col_if_missing(table: str, col: sa.Column) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table)]
    if col.name not in cols:
        op.add_column(table, col)


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    # merchants extensions
    if not _has_table("merchants"):
        op.create_table(
            "merchants",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(255)),
            sa.Column("category", sa.String(64)),
            sa.Column("lat", sa.Float),
            sa.Column("lng", sa.Float),
            sa.Column("created_at", sa.DateTime),
        )
    _add_col_if_missing("merchants", sa.Column("pos_provider", sa.String(32)))
    _add_col_if_missing("merchants", sa.Column("pos_account_id", sa.String(128)))
    _add_col_if_missing("merchants", sa.Column("pos_location_ids", sa.Text))
    _add_col_if_missing("merchants", sa.Column("affiliate_partner", sa.String(32)))
    _add_col_if_missing("merchants", sa.Column("affiliate_merchant_ref", sa.String(128)))
    _add_col_if_missing("merchants", sa.Column("radius_m", sa.Integer, server_default="500"))
    _add_col_if_missing("merchants", sa.Column("green_hour_commit_pct", sa.Float))
    _add_col_if_missing("merchants", sa.Column("status", sa.String(32), server_default="active"))

    # offers catalog (per-merchant)
    if not _has_table("offers_catalog"):
        op.create_table(
            "offers_catalog",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("merchant_id", sa.Integer, sa.ForeignKey("merchants.id")),
            sa.Column("offer_ref", sa.String(128)),
            sa.Column("type", sa.String(16)),
            sa.Column("value", sa.Integer),
            sa.Column("window_start", sa.Time),
            sa.Column("window_end", sa.Time),
            sa.Column("source", sa.String(32)),
            sa.Column("tracking_template", sa.Text),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # events v2
    if not _has_table("events2"):
        op.create_table(
            "events2",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("host_type", sa.String(16)),
            sa.Column("host_id", sa.Integer),
            sa.Column("title", sa.String(255)),
            sa.Column("description", sa.Text),
            sa.Column("category", sa.String(64)),
            sa.Column("city", sa.String(128)),
            sa.Column("lat", sa.Float),
            sa.Column("lng", sa.Float),
            sa.Column("radius_m", sa.Integer, server_default="120"),
            sa.Column("starts_at", sa.DateTime),
            sa.Column("ends_at", sa.DateTime),
            sa.Column("green_window_start", sa.Time),
            sa.Column("green_window_end", sa.Time),
            sa.Column("join_fee_cents", sa.Integer, server_default="0"),
            sa.Column("pool_commit_pct", sa.Float),
            sa.Column("capacity", sa.Integer),
            sa.Column("verification_mode", sa.String(16), server_default="geo"),
            sa.Column("min_dwell_sec", sa.Integer, server_default="0"),
            sa.Column("status", sa.String(16), server_default="scheduled"),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("idx_events2_city_time", "events2", ["city", "starts_at"])
        op.create_index("idx_events2_geo", "events2", ["lat", "lng"])

    if not _has_table("event_attendance2"):
        op.create_table(
            "event_attendance2",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("event_id", sa.Integer, sa.ForeignKey("events2.id")),
            sa.Column("user_id", sa.Integer),
            sa.Column("state", sa.String(16), server_default="joined"),
            sa.Column("joined_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("verified_at", sa.DateTime),
        )
        op.create_unique_constraint("ux_event_attendee2", "event_attendance2", ["event_id", "user_id"])

    if not _has_table("verifications2"):
        op.create_table(
            "verifications2",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("user_id", sa.Integer),
            sa.Column("event_id", sa.Integer),
            sa.Column("mode", sa.String(16)),
            sa.Column("started_at", sa.DateTime),
            sa.Column("completed_at", sa.DateTime),
            sa.Column("lat", sa.Float),
            sa.Column("lng", sa.Float),
            sa.Column("status", sa.String(16), server_default="pending"),
            sa.Column("meta_json", sa.Text),
        )
        op.create_index("idx_verif2_user_time", "verifications2", ["user_id", "started_at"])

    # transactions (affiliate/POS/event fee)
    if not _has_table("transactions"):
        op.create_table(
            "transactions",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer),
            sa.Column("merchant_id", sa.Integer),
            sa.Column("event_id", sa.Integer),
            sa.Column("source", sa.String(16)),
            sa.Column("amount_cents", sa.Integer),
            sa.Column("status", sa.String(16), server_default="initiated"),
            sa.Column("meta_json", sa.Text),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("idx_txn_user_time", "transactions", ["user_id", "created_at"])

    # rewards2
    if not _has_table("rewards2"):
        op.create_table(
            "rewards2",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer),
            sa.Column("type", sa.String(24)),
            sa.Column("amount_cents", sa.Integer),
            sa.Column("earn_date", sa.Date),
            sa.Column("available_at", sa.DateTime),
            sa.Column("ref_txn_id", sa.Integer),
            sa.Column("ref_event_id", sa.Integer),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("idx_rewards2_user_avail", "rewards2", ["user_id", "available_at"])

    if not _has_table("pool_ledger2"):
        op.create_table(
            "pool_ledger2",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("city", sa.String(128)),
            sa.Column("source", sa.String(24)),
            sa.Column("amount_cents", sa.Integer),
            sa.Column("related_event_id", sa.Integer),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        )


def downgrade() -> None:
    # no destructive downgrade
    pass


