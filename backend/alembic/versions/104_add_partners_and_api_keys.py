"""Add partners and partner_api_keys tables

Creates the partner entity and API key tables for the External Incentive API.
Partners can submit charging sessions via API and receive incentive evaluations.

Revision ID: 104_add_partners_and_api_keys
Revises: 103_make_campaigns_sponsor_id_nullable
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

revision = "104_add_partners_and_api_keys"
down_revision = "103_make_campaigns_sponsor_id_nullable"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    existing_tables = inspector.get_table_names()

    if "partners" not in existing_tables:
        op.create_table(
            "partners",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("slug", sa.String(100), nullable=False),
            sa.Column("partner_type", sa.String(50), nullable=False),
            sa.Column("trust_tier", sa.Integer, nullable=False, server_default="3"),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("contact_name", sa.String(200), nullable=True),
            sa.Column("contact_email", sa.String(200), nullable=True),
            sa.Column("webhook_url", sa.String(500), nullable=True),
            sa.Column("webhook_secret", sa.String(200), nullable=True),
            sa.Column("webhook_enabled", sa.Boolean, nullable=False, server_default="0"),
            sa.Column("rate_limit_rpm", sa.Integer, nullable=False, server_default="60"),
            sa.Column("default_verification_method", sa.String(50), nullable=False, server_default="partner_app_signal"),
            sa.Column("quality_score_modifier", sa.Integer, nullable=False, server_default="0"),
            sa.Column("metadata_json", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False),
        )
        try:
            op.create_index("ix_partners_slug", "partners", ["slug"], unique=True)
        except Exception:
            pass
        try:
            op.create_index("ix_partners_status", "partners", ["status"])
        except Exception:
            pass

    if "partner_api_keys" not in existing_tables:
        op.create_table(
            "partner_api_keys",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("partner_id", sa.String(36), sa.ForeignKey("partners.id"), nullable=False),
            sa.Column("key_prefix", sa.String(12), nullable=False),
            sa.Column("key_hash", sa.String(128), nullable=False),
            sa.Column("name", sa.String(100), nullable=True),
            sa.Column("scopes", sa.JSON, nullable=False),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
            sa.Column("last_used_at", sa.DateTime, nullable=True),
            sa.Column("expires_at", sa.DateTime, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
        try:
            op.create_index("ix_partner_api_keys_partner_id", "partner_api_keys", ["partner_id"])
        except Exception:
            pass
        try:
            op.create_index("ix_partner_api_keys_prefix", "partner_api_keys", ["key_prefix"])
        except Exception:
            pass
        try:
            op.create_index("ix_partner_api_keys_hash", "partner_api_keys", ["key_hash"], unique=True)
        except Exception:
            pass
        try:
            op.create_index("ix_partner_api_keys_partner_active", "partner_api_keys", ["partner_id", "is_active"])
        except Exception:
            pass


def downgrade():
    op.drop_table("partner_api_keys")
    op.drop_table("partners")
