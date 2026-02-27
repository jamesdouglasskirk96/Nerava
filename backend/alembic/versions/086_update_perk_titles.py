"""Update merchant perk titles: 'Earn X Nova' -> 'EV Rewards'
and update Heights Pizzeria description.

Revision ID: 086_update_perk_titles
Revises: 085_fix_session_user_id
Create Date: 2026-02-27
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect

revision = '086_update_perk_titles'
down_revision = '085_fix_session_user_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'merchant_perks' not in existing_tables:
        return

    # Update all perk titles containing "Earn" and "Nova" to "EV Rewards"
    op.execute(
        "UPDATE merchant_perks SET title = 'EV Rewards' "
        "WHERE title LIKE '%Earn%Nova%' OR title LIKE '%Nova%'"
    )
    print("  Updated perk titles to 'EV Rewards'")

    # Set default title for perks with NULL title
    op.execute(
        "UPDATE merchant_perks SET title = 'EV Rewards' "
        "WHERE title IS NULL"
    )
    print("  Set default title 'EV Rewards' for perks with NULL title")

    # Update Heights Pizzeria description specifically
    if 'merchants' in existing_tables:
        op.execute(
            "UPDATE merchant_perks SET "
            "description = 'Enjoy free Garlic knots ($6 off) with your order while you charge' "
            "WHERE merchant_id IN ("
            "  SELECT id FROM merchants WHERE name LIKE '%Heights Pizzeria%'"
            ")"
        )
        print("  Updated Heights Pizzeria perk description")


def downgrade() -> None:
    pass
