"""Add Apple/Google wallet pass system tables and backfills

Revision ID: 024_add_wallet_pass_system
Revises: 023_add_wallet_pass_fields
Create Date: 2025-02-01 00:00:00.000000

This migration adds:
- apple_pass_registrations table for Apple Wallet PassKit device registrations
- google_wallet_links table for Google Wallet links per driver wallet
- apple_authentication_token field on driver_wallets (encrypted-at-rest)

It also ensures:
- wallet_pass_token is backfilled using secrets.token_urlsafe for any missing rows
- wallet_activity_updated_at is backfilled when prior wallet activity exists
"""
from alembic import op
import sqlalchemy as sa
import secrets


# revision identifiers, used by Alembic.
revision = "024_add_wallet_pass_system"
down_revision = "023_add_wallet_pass_fields"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    """Check if a table exists."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        columns = insp.get_columns(table_name)
        return any(col["name"] == column_name for col in columns)
    except Exception:
        return False


def _has_index(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        indexes = insp.get_indexes(table_name)
        return any(idx["name"] == index_name for idx in indexes)
    except Exception:
        return False


def upgrade() -> None:
    """Create wallet pass system tables and backfill wallet fields."""

    # 1. Add apple_authentication_token to driver_wallets (encrypted-at-rest)
    if _has_table("driver_wallets") and not _has_column("driver_wallets", "apple_authentication_token"):
        op.add_column(
            "driver_wallets",
            sa.Column("apple_authentication_token", sa.Text(), nullable=True),
        )

    # 2. Create apple_pass_registrations table
    if not _has_table("apple_pass_registrations"):
        op.create_table(
            "apple_pass_registrations",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("driver_wallet_id", sa.Integer(), sa.ForeignKey("driver_wallets.user_id"), nullable=False),
            sa.Column("device_library_identifier", sa.String(), nullable=False),
            sa.Column("push_token", sa.String(), nullable=True),
            sa.Column("pass_type_identifier", sa.String(), nullable=False),
            sa.Column("serial_number", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        )

        # Indexes for fast lookup by device, wallet, and serial
        op.create_index(
            "ix_apple_pass_registrations_driver_wallet_id",
            "apple_pass_registrations",
            ["driver_wallet_id"],
        )
        op.create_index(
            "ix_apple_pass_registrations_device_library_identifier",
            "apple_pass_registrations",
            ["device_library_identifier"],
        )
        op.create_index(
            "ix_apple_pass_registrations_serial_number",
            "apple_pass_registrations",
            ["serial_number"],
        )
        op.create_index(
            "ix_apple_pass_registrations_driver_serial",
            "apple_pass_registrations",
            ["driver_wallet_id", "serial_number"],
        )
        op.create_index(
            "ix_apple_pass_registrations_is_active",
            "apple_pass_registrations",
            ["is_active"],
        )

    # 3. Create google_wallet_links table
    if not _has_table("google_wallet_links"):
        op.create_table(
            "google_wallet_links",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("driver_wallet_id", sa.Integer(), sa.ForeignKey("driver_wallets.user_id"), nullable=False),
            sa.Column("issuer_id", sa.String(), nullable=False),
            sa.Column("class_id", sa.String(), nullable=False),
            sa.Column("object_id", sa.String(), nullable=False),
            sa.Column("state", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column(
                "last_updated_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )

        # Indexes for fast lookup by wallet, object, and state
        op.create_index(
            "ix_google_wallet_links_driver_wallet_id",
            "google_wallet_links",
            ["driver_wallet_id"],
        )
        op.create_index(
            "ix_google_wallet_links_object_id",
            "google_wallet_links",
            ["object_id"],
        )
        op.create_index(
            "ix_google_wallet_links_state",
            "google_wallet_links",
            ["state"],
        )
        op.create_index(
            "ix_google_wallet_links_driver_state",
            "google_wallet_links",
            ["driver_wallet_id", "state"],
        )

    # 4. Backfill wallet_pass_token for any existing driver_wallets missing a token
    if _has_table("driver_wallets") and _has_column("driver_wallets", "wallet_pass_token"):
        conn = op.get_bind()
        wallets = conn.execute(
            sa.text("SELECT user_id FROM driver_wallets WHERE wallet_pass_token IS NULL")
        ).fetchall()

        for (user_id,) in wallets:
            # Generate random opaque token (24 bytes -> ~32 chars URL-safe base64)
            token = secrets.token_urlsafe(24)

            # Ensure uniqueness by checking for collisions (extremely unlikely)
            existing = conn.execute(
                sa.text("SELECT user_id FROM driver_wallets WHERE wallet_pass_token = :token"),
                {"token": token},
            ).fetchone()
            if existing:
                token = secrets.token_urlsafe(24)

            conn.execute(
                sa.text(
                    "UPDATE driver_wallets "
                    "SET wallet_pass_token = :token "
                    "WHERE user_id = :user_id"
                ),
                {"token": token, "user_id": user_id},
            )

    # 5. Backfill wallet_activity_updated_at based on historical activity
    if _has_table("driver_wallets") and _has_column("driver_wallets", "wallet_activity_updated_at"):
        conn = op.get_bind()

        # From nova_transactions
        if _has_table("nova_transactions"):
            conn.execute(
                sa.text(
                    """
                    UPDATE driver_wallets
                    SET wallet_activity_updated_at = CURRENT_TIMESTAMP
                    WHERE wallet_activity_updated_at IS NULL
                    AND user_id IN (
                        SELECT DISTINCT driver_user_id
                        FROM nova_transactions
                        WHERE driver_user_id IS NOT NULL
                    )
                    """
                )
            )

        # From merchant_redemptions
        if _has_table("merchant_redemptions"):
            conn.execute(
                sa.text(
                    """
                    UPDATE driver_wallets
                    SET wallet_activity_updated_at = CURRENT_TIMESTAMP
                    WHERE wallet_activity_updated_at IS NULL
                    AND user_id IN (
                        SELECT DISTINCT driver_user_id
                        FROM merchant_redemptions
                        WHERE driver_user_id IS NOT NULL
                    )
                    """
                )
            )


def downgrade() -> None:
    """Drop wallet pass system tables and fields."""

    # Drop google_wallet_links
    if _has_table("google_wallet_links"):
        op.drop_index("ix_google_wallet_links_driver_state", table_name="google_wallet_links")
        op.drop_index("ix_google_wallet_links_state", table_name="google_wallet_links")
        op.drop_index("ix_google_wallet_links_object_id", table_name="google_wallet_links")
        op.drop_index("ix_google_wallet_links_driver_wallet_id", table_name="google_wallet_links")
        op.drop_table("google_wallet_links")

    # Drop apple_pass_registrations
    if _has_table("apple_pass_registrations"):
        op.drop_index("ix_apple_pass_registrations_is_active", table_name="apple_pass_registrations")
        op.drop_index(
            "ix_apple_pass_registrations_driver_serial",
            table_name="apple_pass_registrations",
        )
        op.drop_index(
            "ix_apple_pass_registrations_serial_number",
            table_name="apple_pass_registrations",
        )
        op.drop_index(
            "ix_apple_pass_registrations_device_library_identifier",
            table_name="apple_pass_registrations",
        )
        op.drop_index(
            "ix_apple_pass_registrations_driver_wallet_id",
            table_name="apple_pass_registrations",
        )
        op.drop_table("apple_pass_registrations")

    # Remove apple_authentication_token column from driver_wallets
    if _has_table("driver_wallets") and _has_column("driver_wallets", "apple_authentication_token"):
        op.drop_column("driver_wallets", "apple_authentication_token")










