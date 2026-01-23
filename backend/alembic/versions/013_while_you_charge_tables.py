"""while you charge tables: chargers, merchants, charger_merchants, merchant_perks"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = "013_while_you_charge_tables"
down_revision = "012_verify_dwell_engine"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    # Chargers table
    if not _has_table("chargers"):
        op.create_table(
            "chargers",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("external_id", sa.String(), unique=True, nullable=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("network_name", sa.String(), nullable=True),
            sa.Column("lat", sa.Float(), nullable=False),
            sa.Column("lng", sa.Float(), nullable=False),
            sa.Column("address", sa.String(), nullable=True),
            sa.Column("city", sa.String(), nullable=True),
            sa.Column("state", sa.String(), nullable=True),
            sa.Column("zip_code", sa.String(), nullable=True),
            sa.Column("connector_types", sa.JSON() if hasattr(sa, 'JSON') else sa.Text(), default=list),
            sa.Column("power_kw", sa.Float(), nullable=True),
            sa.Column("is_public", sa.Boolean(), default=True, nullable=False),
            sa.Column("access_code", sa.String(), nullable=True),
            sa.Column("status", sa.String(), default="available", nullable=False),
            sa.Column("last_verified_at", sa.DateTime(), nullable=True),
            sa.Column("logo_url", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        )
        op.create_index("ix_chargers_external_id", "chargers", ["external_id"], unique=True)
        op.create_index("ix_chargers_lat", "chargers", ["lat"])
        op.create_index("ix_chargers_lng", "chargers", ["lng"])
        op.create_index("ix_chargers_city", "chargers", ["city"])
        op.create_index("idx_chargers_location", "chargers", ["lat", "lng"])

    # Merchants table
    if not _has_table("merchants"):
        op.create_table(
            "merchants",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("external_id", sa.String(), unique=True, nullable=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=True),
            sa.Column("lat", sa.Float(), nullable=False),
            sa.Column("lng", sa.Float(), nullable=False),
            sa.Column("address", sa.String(), nullable=True),
            sa.Column("city", sa.String(), nullable=True),
            sa.Column("state", sa.String(), nullable=True),
            sa.Column("zip_code", sa.String(), nullable=True),
            sa.Column("logo_url", sa.String(), nullable=True),
            sa.Column("photo_url", sa.String(), nullable=True),
            sa.Column("rating", sa.Float(), nullable=True),
            sa.Column("price_level", sa.Integer(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("website", sa.String(), nullable=True),
            sa.Column("place_types", sa.JSON() if hasattr(sa, 'JSON') else sa.Text(), default=list),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        )
        op.create_index("ix_merchants_external_id", "merchants", ["external_id"], unique=True)
        op.create_index("ix_merchants_name", "merchants", ["name"])
        op.create_index("ix_merchants_category", "merchants", ["category"])
        op.create_index("ix_merchants_lat", "merchants", ["lat"])
        op.create_index("ix_merchants_lng", "merchants", ["lng"])
        op.create_index("ix_merchants_city", "merchants", ["city"])
        op.create_index("idx_merchants_location", "merchants", ["lat", "lng"])

    # ChargerMerchants junction table
    if not _has_table("charger_merchants"):
        op.create_table(
            "charger_merchants",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("charger_id", sa.String(), sa.ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("merchant_id", sa.String(), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("distance_m", sa.Float(), nullable=False),
            sa.Column("walk_duration_s", sa.Integer(), nullable=False),
            sa.Column("walk_distance_m", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        )
        op.create_index("ix_charger_merchants_charger_id", "charger_merchants", ["charger_id"])
        op.create_index("ix_charger_merchants_merchant_id", "charger_merchants", ["merchant_id"])
        op.create_index("idx_charger_merchant_unique", "charger_merchants", ["charger_id", "merchant_id"], unique=True)

    # MerchantPerks table
    if not _has_table("merchant_perks"):
        op.create_table(
            "merchant_perks",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("merchant_id", sa.String(), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("nova_reward", sa.Integer(), nullable=False),
            sa.Column("window_start", sa.String(), nullable=True),
            sa.Column("window_end", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_merchant_perks_merchant_id", "merchant_perks", ["merchant_id"])
        op.create_index("ix_merchant_perks_is_active", "merchant_perks", ["is_active"])


def downgrade() -> None:
    op.drop_table("merchant_perks")
    op.drop_table("charger_merchants")
    op.drop_table("merchants")
    op.drop_table("chargers")

