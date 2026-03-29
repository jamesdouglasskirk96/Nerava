"""Add POS ordering columns to merchants table

Revision ID: 114
Revises: 113
"""
from alembic import op
import sqlalchemy as sa

revision = "114"
down_revision = "113"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("merchants", sa.Column("ordering_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("merchants", sa.Column("pos_type", sa.String(20), nullable=True))
    op.add_column("merchants", sa.Column("discount_injection_method", sa.String(20), nullable=True))
    op.add_column("merchants", sa.Column("discount_param_key", sa.String(100), nullable=True))
    op.add_column("merchants", sa.Column("phone_field_selector", sa.String(200), nullable=True))
    op.add_column("merchants", sa.Column("confirmation_url_pattern", sa.String(500), nullable=True))
    op.add_column("merchants", sa.Column("nerava_offer", sa.String(200), nullable=True))
    op.add_column("merchants", sa.Column("nerava_discount_code", sa.String(100), nullable=True))


def downgrade():
    op.drop_column("merchants", "nerava_discount_code")
    op.drop_column("merchants", "nerava_offer")
    op.drop_column("merchants", "confirmation_url_pattern")
    op.drop_column("merchants", "phone_field_selector")
    op.drop_column("merchants", "discount_param_key")
    op.drop_column("merchants", "discount_injection_method")
    op.drop_column("merchants", "pos_type")
    op.drop_column("merchants", "ordering_enabled")
