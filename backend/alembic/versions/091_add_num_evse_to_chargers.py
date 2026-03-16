"""Add num_evse column to chargers and backfill from network heuristics

Revision ID: 091_add_num_evse_to_chargers
Revises: 090_add_wallet_nova_reputation_columns
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = '091_add_num_evse_to_chargers'
down_revision = '090_add_wallet_nova_reputation_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Add num_evse column
    with op.batch_alter_table('chargers') as batch_op:
        batch_op.add_column(sa.Column('num_evse', sa.Integer(), nullable=True))

    # Backfill based on network_name heuristics
    chargers = sa.table('chargers',
        sa.column('id', sa.String),
        sa.column('network_name', sa.String),
        sa.column('name', sa.String),
        sa.column('num_evse', sa.Integer),
    )

    # Tesla Superchargers typically have 8-20 stalls
    op.execute(
        chargers.update()
        .where(chargers.c.network_name == 'Tesla')
        .where(chargers.c.num_evse.is_(None))
        .values(num_evse=12)
    )

    # Tesla Destination chargers typically have 2-4 stalls
    op.execute(
        chargers.update()
        .where(chargers.c.network_name == 'Tesla Destination')
        .where(chargers.c.num_evse.is_(None))
        .values(num_evse=2)
    )

    # ChargePoint stations vary widely, default to 2
    op.execute(
        chargers.update()
        .where(chargers.c.network_name.like('%ChargePoint%'))
        .where(chargers.c.num_evse.is_(None))
        .values(num_evse=2)
    )

    # Other networks default to 4
    op.execute(
        chargers.update()
        .where(chargers.c.num_evse.is_(None))
        .values(num_evse=4)
    )


def downgrade():
    with op.batch_alter_table('chargers') as batch_op:
        batch_op.drop_column('num_evse')
