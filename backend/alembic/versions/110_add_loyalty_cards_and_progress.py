"""add loyalty cards and progress

Revision ID: 110_loyalty
Revises: 109_merchant_rewards
Create Date: 2026-03-15
"""
from alembic import op
import sqlalchemy as sa

revision = "110_loyalty"
down_revision = "109_merchant_rewards"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "loyalty_cards",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("merchant_id", sa.String, sa.ForeignKey("domain_merchants.id"), nullable=False, index=True),
        sa.Column("place_id", sa.String, nullable=True, index=True),
        sa.Column("program_name", sa.String, nullable=False),
        sa.Column("visits_required", sa.Integer, nullable=False),
        sa.Column("reward_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reward_description", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=True),
    )

    op.create_table(
        "loyalty_progress",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("driver_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("loyalty_card_id", sa.String(36), sa.ForeignKey("loyalty_cards.id"), nullable=False, index=True),
        sa.Column("merchant_id", sa.String, nullable=False, index=True),
        sa.Column("visit_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_visit_at", sa.DateTime, nullable=True),
        sa.Column("reward_unlocked", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("reward_unlocked_at", sa.DateTime, nullable=True),
        sa.Column("reward_claimed", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("reward_claimed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("driver_user_id", "loyalty_card_id", name="uq_loyalty_progress_driver_card"),
    )


def downgrade():
    op.drop_table("loyalty_progress")
    op.drop_table("loyalty_cards")
