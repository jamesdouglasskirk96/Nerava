"""Add merchant_rewards table

Revision ID: 026_add_merchant_rewards
Revises: 025_add_charging_demo_fields
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '026_add_merchant_rewards'
down_revision = '025_add_charging_demo_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create merchant_rewards table
    op.create_table(
        'merchant_rewards',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('nova_amount', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['domain_merchants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_merchant_rewards_merchant_id', 'merchant_rewards', ['merchant_id'])
    op.create_index('ix_merchant_rewards_is_active', 'merchant_rewards', ['is_active'])
    op.create_index('ix_merchant_rewards_merchant_active', 'merchant_rewards', ['merchant_id', 'is_active'])
    
    # Add reward_id column to merchant_redemptions (if table exists)
    try:
        op.add_column('merchant_redemptions', sa.Column('reward_id', sa.String(), nullable=True))
        op.create_foreign_key('fk_merchant_redemptions_reward', 'merchant_redemptions', 'merchant_rewards', ['reward_id'], ['id'])
        op.create_index('ix_merchant_redemptions_reward_id', 'merchant_redemptions', ['reward_id'])
    except Exception:
        # Table might not exist yet, or column already exists - skip
        pass


def downgrade():
    # Remove reward_id column from merchant_redemptions (if exists)
    try:
        op.drop_index('ix_merchant_redemptions_reward_id', table_name='merchant_redemptions')
        op.drop_constraint('fk_merchant_redemptions_reward', 'merchant_redemptions', type_='foreignkey')
        op.drop_column('merchant_redemptions', 'reward_id')
    except Exception:
        # Column might not exist - skip
        pass
    
    # Drop indexes
    op.drop_index('ix_merchant_rewards_merchant_active', table_name='merchant_rewards')
    op.drop_index('ix_merchant_rewards_is_active', table_name='merchant_rewards')
    op.drop_index('ix_merchant_rewards_merchant_id', table_name='merchant_rewards')
    
    # Drop table
    op.drop_table('merchant_rewards')

