"""add merchants.external_id if missing

Revision ID: 021_add_merchants_external_id_if_missing
Revises: 020_add_vehicle_tables
Create Date: 2025-12-08 14:20:00.000000

This migration ensures merchants.external_id exists even if the table was created
before migration 013 or if the column was somehow missing.

NOTE: If you have an old nerava.db without external_id and migrations fail,
you may need to delete nerava.db and let migrations recreate it from scratch.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "021_add_merchants_external_id_if_missing"
down_revision = "020"  # Matches revision ID from 020_add_vehicle_tables.py
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def upgrade() -> None:
    """Add external_id column to merchants if it doesn't exist"""
    if not _column_exists("merchants", "external_id"):
        op.add_column(
            "merchants",
            sa.Column("external_id", sa.String(), nullable=True)
        )
        # Create index if it doesn't exist
        try:
            op.create_index(
                "ix_merchants_external_id",
                "merchants",
                ["external_id"],
                unique=False,  # Not unique - multiple merchants can share external_id from different sources
            )
        except Exception:
            # Index might already exist, ignore
            pass


def downgrade() -> None:
    """Remove external_id column (only if you really need to rollback)"""
    if _column_exists("merchants", "external_id"):
        try:
            op.drop_index("ix_merchants_external_id", table_name="merchants")
        except Exception:
            pass
        op.drop_column("merchants", "external_id")

