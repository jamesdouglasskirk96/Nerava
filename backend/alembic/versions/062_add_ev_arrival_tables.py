"""Add EV Arrival tables: arrival_sessions, merchant_notification_config,
merchant_pos_credentials, billing_events, and user/merchant vehicle/ordering fields.

Revision ID: 062
Revises: 061
Create Date: 2026-02-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "062"
down_revision = "061_add_admin_role_to_users"
branch_labels = None
depends_on = None


def _table_exists(table_name: str, bind) -> bool:
    """Check if a table exists"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str, bind) -> bool:
    """Check if a column exists in a table"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def _index_exists(table_name: str, index_name: str, bind) -> bool:
    """Check if an index exists on a table"""
    from sqlalchemy import inspect
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    # -- arrival_sessions (skip if exists) --
    if not _table_exists("arrival_sessions", bind):
        op.create_table(
            "arrival_sessions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("driver_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("merchant_id", sa.String, sa.ForeignKey("merchants.id"), nullable=False),
            sa.Column("charger_id", sa.String, sa.ForeignKey("chargers.id"), nullable=True),
            sa.Column("arrival_type", sa.String(20), nullable=False),
            sa.Column("order_number", sa.String(100), nullable=True),
            sa.Column("order_source", sa.String(20), nullable=True),
            sa.Column("order_total_cents", sa.Integer, nullable=True),
            sa.Column("order_status", sa.String(20), nullable=True),
            sa.Column("driver_estimate_cents", sa.Integer, nullable=True),
            sa.Column("merchant_reported_total_cents", sa.Integer, nullable=True),
            sa.Column("total_source", sa.String(20), nullable=True),
            sa.Column("vehicle_color", sa.String(30), nullable=True),
            sa.Column("vehicle_model", sa.String(60), nullable=True),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending_order"),
            sa.Column("merchant_reply_code", sa.String(4), nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("order_bound_at", sa.DateTime, nullable=True),
            sa.Column("geofence_entered_at", sa.DateTime, nullable=True),
            sa.Column("merchant_notified_at", sa.DateTime, nullable=True),
            sa.Column("merchant_confirmed_at", sa.DateTime, nullable=True),
            sa.Column("completed_at", sa.DateTime, nullable=True),
            sa.Column("expires_at", sa.DateTime, nullable=False),
            sa.Column("arrival_lat", sa.Float, nullable=True),
            sa.Column("arrival_lng", sa.Float, nullable=True),
            sa.Column("arrival_accuracy_m", sa.Float, nullable=True),
            sa.Column("platform_fee_bps", sa.Integer, nullable=False, server_default="500"),
            sa.Column("billable_amount_cents", sa.Integer, nullable=True),
            sa.Column("billing_status", sa.String(20), server_default="pending"),
            sa.Column("feedback_rating", sa.String(10), nullable=True),
            sa.Column("feedback_reason", sa.String(50), nullable=True),
            sa.Column("feedback_comment", sa.String(200), nullable=True),
            sa.Column("idempotency_key", sa.String(100), unique=True, nullable=True),
        )
    if not _index_exists("arrival_sessions", "idx_arrival_driver_active", bind):
        op.create_index("idx_arrival_driver_active", "arrival_sessions", ["driver_id", "status"])
    if not _index_exists("arrival_sessions", "idx_arrival_merchant_status", bind):
        op.create_index("idx_arrival_merchant_status", "arrival_sessions", ["merchant_id", "status"])
    if not _index_exists("arrival_sessions", "idx_arrival_billing", bind):
        op.create_index("idx_arrival_billing", "arrival_sessions", ["billing_status"])
    if not _index_exists("arrival_sessions", "idx_arrival_created", bind):
        op.create_index("idx_arrival_created", "arrival_sessions", ["created_at"])
    if not _index_exists("arrival_sessions", "idx_arrival_reply_code", bind):
        op.create_index("idx_arrival_reply_code", "arrival_sessions", ["merchant_reply_code"])

    # Partial unique index: one active session per driver (PostgreSQL only)
    if dialect_name == 'postgresql':
        op.execute(sa.text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_arrival_one_active_per_driver
            ON arrival_sessions (driver_id)
            WHERE status IN ('pending_order', 'awaiting_arrival', 'arrived', 'merchant_notified')
        """))

    # -- merchant_notification_config (skip if exists) --
    if not _table_exists("merchant_notification_config", bind):
        op.create_table(
            "merchant_notification_config",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("merchant_id", sa.String, sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("notify_sms", sa.Boolean, server_default="1", nullable=False),
            sa.Column("notify_email", sa.Boolean, server_default="0", nullable=False),
            sa.Column("sms_phone", sa.String(20), nullable=True),
            sa.Column("email_address", sa.String(255), nullable=True),
            sa.Column("pos_integration", sa.String(20), server_default="none", nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # -- merchant_pos_credentials (skip if exists) --
    if not _table_exists("merchant_pos_credentials", bind):
        op.create_table(
            "merchant_pos_credentials",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("merchant_id", sa.String, sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("pos_type", sa.String(20), nullable=False),
            sa.Column("restaurant_guid", sa.String(100), nullable=True),
            sa.Column("access_token_encrypted", sa.Text, nullable=True),
            sa.Column("refresh_token_encrypted", sa.Text, nullable=True),
            sa.Column("token_expires_at", sa.DateTime, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # -- billing_events (skip if exists) --
    if not _table_exists("billing_events", bind):
        op.create_table(
            "billing_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("arrival_session_id", sa.String(36), sa.ForeignKey("arrival_sessions.id"), nullable=False),
            sa.Column("merchant_id", sa.String, sa.ForeignKey("merchants.id"), nullable=False),
            sa.Column("order_total_cents", sa.Integer, nullable=False),
            sa.Column("fee_bps", sa.Integer, nullable=False),
            sa.Column("billable_cents", sa.Integer, nullable=False),
            sa.Column("total_source", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), server_default="pending", nullable=False),
            sa.Column("invoice_id", sa.String(100), nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column("invoiced_at", sa.DateTime, nullable=True),
            sa.Column("paid_at", sa.DateTime, nullable=True),
        )
    if not _index_exists("billing_events", "idx_billing_merchant_status", bind):
        op.create_index("idx_billing_merchant_status", "billing_events", ["merchant_id", "status"])
    if not _index_exists("billing_events", "idx_billing_pending", bind):
        op.create_index("idx_billing_pending", "billing_events", ["status"])

    # -- Add vehicle fields to users (skip if exist) --
    if not _column_exists("users", "vehicle_color", bind):
        op.add_column("users", sa.Column("vehicle_color", sa.String(30), nullable=True))
    if not _column_exists("users", "vehicle_model", bind):
        op.add_column("users", sa.Column("vehicle_model", sa.String(60), nullable=True))
    if not _column_exists("users", "vehicle_set_at", bind):
        op.add_column("users", sa.Column("vehicle_set_at", sa.DateTime, nullable=True))

    # -- Add ordering fields to merchants (skip if exist) --
    if not _column_exists("merchants", "ordering_url", bind):
        op.add_column("merchants", sa.Column("ordering_url", sa.String(500), nullable=True))
    if not _column_exists("merchants", "ordering_app_scheme", bind):
        op.add_column("merchants", sa.Column("ordering_app_scheme", sa.String(100), nullable=True))
    if not _column_exists("merchants", "ordering_instructions", bind):
        op.add_column("merchants", sa.Column("ordering_instructions", sa.Text, nullable=True))


def downgrade() -> None:
    # Drop partial unique index if it exists (PostgreSQL only)
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    if dialect_name == 'postgresql':
        try:
            op.execute(sa.text("DROP INDEX IF EXISTS idx_arrival_one_active_per_driver"))
        except Exception:
            pass  # Index may not exist
    
    op.drop_column("merchants", "ordering_instructions")
    op.drop_column("merchants", "ordering_app_scheme")
    op.drop_column("merchants", "ordering_url")
    op.drop_column("users", "vehicle_set_at")
    op.drop_column("users", "vehicle_model")
    op.drop_column("users", "vehicle_color")
    op.drop_table("billing_events")
    op.drop_table("merchant_pos_credentials")
    op.drop_table("merchant_notification_config")
    op.drop_table("arrival_sessions")
