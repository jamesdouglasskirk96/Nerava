"""add merchant category and nearest charger fields

Revision ID: 037_add_merchant_category_and_nearest_charger
Revises: 036_payments_state_machine
Create Date: 2025-01-24 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "037_add_merchant_category_and_nearest_charger"
down_revision = "036_payments_state_machine"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str, inspector) -> bool:
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table = "merchants"

    if table not in inspector.get_table_names():
        return

    # Add primary_category column
    if not _column_exists(table, "primary_category", inspector):
        op.add_column(
            table,
            sa.Column("primary_category", sa.String(32), nullable=True)
        )

    # Add nearest_charger_id column
    if not _column_exists(table, "nearest_charger_id", inspector):
        op.add_column(
            table,
            sa.Column("nearest_charger_id", sa.String(64), nullable=True)
        )

    # Add nearest_charger_distance_m column
    if not _column_exists(table, "nearest_charger_distance_m", inspector):
        op.add_column(
            table,
            sa.Column("nearest_charger_distance_m", sa.Integer(), nullable=True)
        )

    # Create indexes
    indexes = [idx["name"] for idx in inspector.get_indexes(table)]
    
    if "ix_merchants_primary_category" not in indexes:
        op.create_index(
            "ix_merchants_primary_category",
            table,
            ["primary_category"]
        )
    
    if "ix_merchants_nearest_charger_distance" not in indexes:
        op.create_index(
            "ix_merchants_nearest_charger_distance",
            table,
            ["nearest_charger_distance_m"]
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table = "merchants"

    if table not in inspector.get_table_names():
        return

    indexes = [idx["name"] for idx in inspector.get_indexes(table)]
    columns = [col["name"] for col in inspector.get_columns(table)]

    # Drop indexes
    if "ix_merchants_nearest_charger_distance" in indexes:
        op.drop_index("ix_merchants_nearest_charger_distance", table)
    
    if "ix_merchants_primary_category" in indexes:
        op.drop_index("ix_merchants_primary_category", table)

    # Drop columns
    if "nearest_charger_distance_m" in columns:
        op.drop_column(table, "nearest_charger_distance_m")
    
    if "nearest_charger_id" in columns:
        op.drop_column(table, "nearest_charger_id")
    
    if "primary_category" in columns:
        op.drop_column(table, "primary_category")








