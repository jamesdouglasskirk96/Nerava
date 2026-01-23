"""add missing merchant columns

Revision ID: 014_add_merchant_columns
Revises: 013_while_you_charge_tables
Create Date: 2025-02-03 11:11:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "014_add_merchant_columns"
down_revision = "013_while_you_charge_tables"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str, inspector) -> bool:
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table = "merchants"

    column_defs = [
        ("city", sa.String(), {"nullable": True}),
        ("state", sa.String(), {"nullable": True}),
        ("zip_code", sa.String(), {"nullable": True}),
        ("logo_url", sa.String(), {"nullable": True}),
        ("photo_url", sa.String(), {"nullable": True}),
        ("rating", sa.Float(), {"nullable": True}),
        ("price_level", sa.Integer(), {"nullable": True}),
        ("phone", sa.String(), {"nullable": True}),
        ("website", sa.String(), {"nullable": True}),
        ("place_types", sa.JSON(), {"nullable": True}),
        (
            "updated_at",
            sa.DateTime(),
            {"nullable": False, "server_default": sa.text("CURRENT_TIMESTAMP")},
        ),
    ]

    for name, column_type, kwargs in column_defs:
        if not _column_exists(table, name, inspector):
            op.add_column(table, sa.Column(name, column_type, **kwargs))


def downgrade() -> None:
    columns = [
        "updated_at",
        "place_types",
        "website",
        "phone",
        "price_level",
        "rating",
        "photo_url",
        "logo_url",
        "zip_code",
        "state",
        "city",
    ]
    for column in columns:
        op.drop_column("merchants", column)

