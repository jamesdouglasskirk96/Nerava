"""verify dwell engine columns on sessions"""
from alembic import op
import sqlalchemy as sa


revision = "012_verify_dwell_engine"
down_revision = "011_unified_discover_affiliate_pool"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _add_col_if_missing(table: str, col: sa.Column) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table)]
    if col.name not in cols:
        op.add_column(table, col)


def upgrade() -> None:
    if not _has_table("sessions"):
        # Minimal sessions table if missing (dev SQLite safety)
        op.create_table(
            "sessions",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer),
            sa.Column("started_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("status", sa.String(16), server_default="pending"),
        )

    # New/extended columns for dwell engine
    _add_col_if_missing("sessions", sa.Column("target_type", sa.String(16)))
    _add_col_if_missing("sessions", sa.Column("target_id", sa.String(64)))
    _add_col_if_missing("sessions", sa.Column("target_name", sa.String(255)))
    _add_col_if_missing("sessions", sa.Column("radius_m", sa.Integer, server_default="120"))
    _add_col_if_missing("sessions", sa.Column("started_lat", sa.Float))
    _add_col_if_missing("sessions", sa.Column("started_lng", sa.Float))
    _add_col_if_missing("sessions", sa.Column("last_lat", sa.Float))
    _add_col_if_missing("sessions", sa.Column("last_lng", sa.Float))
    _add_col_if_missing("sessions", sa.Column("last_accuracy_m", sa.Float))
    _add_col_if_missing("sessions", sa.Column("dwell_seconds", sa.Integer, server_default="0"))
    _add_col_if_missing("sessions", sa.Column("min_accuracy_m", sa.Integer, server_default="100"))
    _add_col_if_missing("sessions", sa.Column("dwell_required_s", sa.Integer, server_default="60"))
    _add_col_if_missing("sessions", sa.Column("ping_count", sa.Integer, server_default="0"))
    _add_col_if_missing("sessions", sa.Column("ua", sa.Text))
    _add_col_if_missing("sessions", sa.Column("status", sa.String(16), server_default="pending"))

    # Partial indexes for Postgres
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        try:
            op.create_index("idx_sessions_user_started", "sessions", ["user_id", "started_at"])
        except Exception:
            pass
        try:
            op.create_index("idx_sessions_status", "sessions", ["status"])
        except Exception:
            pass
        try:
            op.create_index("idx_sessions_target", "sessions", ["target_type", "target_id"])
        except Exception:
            pass


def downgrade() -> None:
    # Non-destructive downgrade
    pass


