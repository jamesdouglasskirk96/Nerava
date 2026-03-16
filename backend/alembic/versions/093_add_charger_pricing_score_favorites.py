"""Add charger pricing, nerava_score, and favorite_chargers table

Revision ID: 093_add_charger_pricing_score_favorites
Revises: 092_add_telemetry_enabled_to_tesla_connections
Create Date: 2026-03-02

Adds pricing_per_kwh, pricing_source, and nerava_score columns to chargers.
Creates favorite_chargers table for charger bookmarks.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '093_add_charger_pricing_score_favorites'
down_revision = '092_add_telemetry_enabled_to_tesla_connections'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add pricing and score columns to chargers
    with op.batch_alter_table('chargers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pricing_per_kwh', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('pricing_source', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('nerava_score', sa.Float(), nullable=True))

    # Create favorite_chargers table
    op.create_table(
        'favorite_chargers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('charger_id', sa.String(), sa.ForeignKey('chargers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_favorite_charger_user', 'favorite_chargers', ['user_id'])
    op.create_index('idx_favorite_charger_charger', 'favorite_chargers', ['charger_id'])
    op.create_index('idx_favorite_charger_unique', 'favorite_chargers', ['user_id', 'charger_id'], unique=True)


def downgrade() -> None:
    op.drop_table('favorite_chargers')

    with op.batch_alter_table('chargers', schema=None) as batch_op:
        batch_op.drop_column('nerava_score')
        batch_op.drop_column('pricing_source')
        batch_op.drop_column('pricing_per_kwh')
