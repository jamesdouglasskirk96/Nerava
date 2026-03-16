"""add merchant rewards and join requests

Revision ID: 109_merchant_rewards
Revises: 108
Create Date: 2026-03-13
"""
from alembic import op
import sqlalchemy as sa

revision = "109_merchant_rewards"
down_revision = "108_add_campaign_platform_fee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Merchant Join Requests (demand capture)
    op.create_table(
        "merchant_join_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("driver_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("merchant_id", sa.String, nullable=True, index=True),
        sa.Column("place_id", sa.String, nullable=True, index=True),
        sa.Column("merchant_name", sa.String, nullable=False),
        sa.Column("charger_id", sa.String, nullable=True),
        sa.Column("interest_tags", sa.JSON, nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_join_req_driver_merchant",
        "merchant_join_requests",
        ["driver_user_id", "place_id"],
        unique=True,
    )

    # 2. Reward Claims
    op.create_table(
        "reward_claims",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("driver_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("campaign_id", sa.String(36), nullable=True, index=True),
        sa.Column("merchant_id", sa.String, nullable=True, index=True),
        sa.Column("place_id", sa.String, nullable=True),
        sa.Column("merchant_name", sa.String, nullable=True),
        sa.Column("session_event_id", sa.String(36), nullable=True),
        sa.Column("charger_id", sa.String, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="claimed"),
        sa.Column("reward_cents", sa.Integer, nullable=True),
        sa.Column("reward_description", sa.String, nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("receipt_submission_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_reward_claim_driver_status",
        "reward_claims",
        ["driver_user_id", "status"],
    )

    # 3. Receipt Submissions
    op.create_table(
        "receipt_submissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("driver_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("reward_claim_id", sa.String(36), sa.ForeignKey("reward_claims.id"), nullable=False, index=True),
        sa.Column("campaign_id", sa.String(36), nullable=True),
        sa.Column("merchant_id", sa.String, nullable=True),
        sa.Column("place_id", sa.String, nullable=True),
        sa.Column("image_url", sa.Text, nullable=False),
        sa.Column("image_key", sa.String, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("ocr_provider", sa.String(50), nullable=True),
        sa.Column("ocr_raw_response", sa.JSON, nullable=True),
        sa.Column("ocr_merchant_name", sa.String, nullable=True),
        sa.Column("ocr_total_cents", sa.Integer, nullable=True),
        sa.Column("ocr_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ocr_confidence", sa.Float, nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("approved_reward_cents", sa.Integer, nullable=True),
        sa.Column("reviewed_by", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("receipt_submissions")
    op.drop_table("reward_claims")
    op.drop_index("ix_join_req_driver_merchant", table_name="merchant_join_requests")
    op.drop_table("merchant_join_requests")
