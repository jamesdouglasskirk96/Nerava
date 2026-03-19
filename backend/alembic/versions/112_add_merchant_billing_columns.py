"""Add billing columns to domain_merchants

Revision ID: 112
Revises: 111
"""
from alembic import op
import sqlalchemy as sa

revision = "112"
down_revision = "111"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("domain_merchants", sa.Column("stripe_customer_id", sa.String(), nullable=True))
    op.add_column("domain_merchants", sa.Column("billing_type", sa.String(), nullable=False, server_default="free"))
    op.add_column("domain_merchants", sa.Column("card_last4", sa.String(4), nullable=True))
    op.add_column("domain_merchants", sa.Column("card_brand", sa.String(20), nullable=True))
    op.create_index("ix_domain_merchants_stripe_customer", "domain_merchants", ["stripe_customer_id"])


def downgrade():
    op.drop_index("ix_domain_merchants_stripe_customer", table_name="domain_merchants")
    op.drop_column("domain_merchants", "card_brand")
    op.drop_column("domain_merchants", "card_last4")
    op.drop_column("domain_merchants", "billing_type")
    op.drop_column("domain_merchants", "stripe_customer_id")
