"""Add partner fields to session_events, incentive_grants, and campaigns

Extends existing tables with partner-related columns for the External Incentive API.
All columns are nullable with defaults — zero risk to existing data.

Revision ID: 105_add_partner_fields
Revises: 104_add_partners_and_api_keys
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

revision = "105_add_partner_fields"
down_revision = "104_add_partners_and_api_keys"
branch_labels = None
depends_on = None


def _has_column(inspector, table, column):
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)

    # --- session_events ---
    if not _has_column(inspector, "session_events", "partner_id"):
        op.add_column("session_events", sa.Column("partner_id", sa.String(36), nullable=True))
        # SQLite does not support ALTER TABLE ADD CONSTRAINT for foreign keys.
        # The FK is defined in the ORM model and enforced on PostgreSQL (production).
        try:
            op.create_foreign_key(
                "fk_session_events_partner_id", "session_events",
                "partners", ["partner_id"], ["id"],
            )
        except (NotImplementedError, Exception):
            pass  # SQLite — FK enforced at ORM level

    if not _has_column(inspector, "session_events", "partner_driver_id"):
        op.add_column("session_events", sa.Column("partner_driver_id", sa.String(200), nullable=True))

    # Composite index for partner session queries
    try:
        op.create_index("ix_session_events_partner_start", "session_events", ["partner_id", "session_start"])
    except Exception:
        pass  # Index may already exist

    # --- incentive_grants ---
    if not _has_column(inspector, "incentive_grants", "reward_destination"):
        op.add_column(
            "incentive_grants",
            sa.Column("reward_destination", sa.String(30), nullable=False, server_default="nerava_wallet"),
        )

    # --- campaigns ---
    if not _has_column(inspector, "campaigns", "allow_partner_sessions"):
        op.add_column(
            "campaigns",
            sa.Column("allow_partner_sessions", sa.Boolean, nullable=False, server_default="1"),
        )

    if not _has_column(inspector, "campaigns", "rule_partner_ids"):
        op.add_column("campaigns", sa.Column("rule_partner_ids", sa.JSON, nullable=True))

    if not _has_column(inspector, "campaigns", "rule_min_trust_tier"):
        op.add_column("campaigns", sa.Column("rule_min_trust_tier", sa.Integer, nullable=True))


def downgrade():
    op.drop_column("campaigns", "rule_min_trust_tier")
    op.drop_column("campaigns", "rule_partner_ids")
    op.drop_column("campaigns", "allow_partner_sessions")
    op.drop_column("incentive_grants", "reward_destination")
    op.drop_index("ix_session_events_partner_start", "session_events")
    op.drop_column("session_events", "partner_driver_id")
    op.drop_column("session_events", "partner_id")
