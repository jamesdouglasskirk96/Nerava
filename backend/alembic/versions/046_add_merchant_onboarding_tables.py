"""add merchant onboarding tables

Revision ID: 046_add_merchant_onboarding_tables
Revises: 045_add_intent_models
Create Date: 2025-02-01 13:00:00.000000

Adds merchant onboarding models: MerchantAccount, MerchantLocationClaim, MerchantPlacementRule, MerchantPaymentMethod
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '046_add_merchant_onboarding_tables'
down_revision = '045_add_intent_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create merchant onboarding tables"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # UUID type handling
    uuid_type = sa.String(36) if dialect_name == 'sqlite' else sa.UUID()
    
    # MerchantAccount table
    op.create_table(
        'merchant_accounts',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('owner_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_merchant_accounts_owner_user_id', 'merchant_accounts', ['owner_user_id'])
    op.create_index('idx_merchant_accounts_owner', 'merchant_accounts', ['owner_user_id'])
    
    # MerchantLocationClaim table
    op.create_table(
        'merchant_location_claims',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('merchant_account_id', uuid_type, nullable=False),
        sa.Column('place_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='CLAIMED'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_account_id'], ['merchant_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_account_id', 'place_id', name='uq_merchant_location_claim')
    )
    
    op.create_index('ix_merchant_location_claims_merchant_account_id', 'merchant_location_claims', ['merchant_account_id'])
    op.create_index('ix_merchant_location_claims_place_id', 'merchant_location_claims', ['place_id'])
    op.create_index('ix_merchant_location_claims_status', 'merchant_location_claims', ['status'])
    op.create_index('idx_merchant_location_claims_account', 'merchant_location_claims', ['merchant_account_id'])
    op.create_index('idx_merchant_location_claims_place', 'merchant_location_claims', ['place_id'])
    
    # MerchantPlacementRule table
    op.create_table(
        'merchant_placement_rules',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('place_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('daily_cap_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('boost_weight', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('perks_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('place_id')
    )
    
    op.create_index('ix_merchant_placement_rules_place_id', 'merchant_placement_rules', ['place_id'])
    op.create_index('ix_merchant_placement_rules_status', 'merchant_placement_rules', ['status'])
    op.create_index('ix_merchant_placement_rules_updated_at', 'merchant_placement_rules', ['updated_at'])
    op.create_index('idx_merchant_placement_rules_status', 'merchant_placement_rules', ['status', 'updated_at'])
    op.create_index('idx_merchant_placement_rules_place', 'merchant_placement_rules', ['place_id'])
    
    # MerchantPaymentMethod table
    op.create_table(
        'merchant_payment_methods',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('merchant_account_id', uuid_type, nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=False),
        sa.Column('stripe_payment_method_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_account_id'], ['merchant_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_merchant_payment_methods_merchant_account_id', 'merchant_payment_methods', ['merchant_account_id'])
    op.create_index('ix_merchant_payment_methods_stripe_customer_id', 'merchant_payment_methods', ['stripe_customer_id'])
    op.create_index('ix_merchant_payment_methods_status', 'merchant_payment_methods', ['status'])
    op.create_index('idx_merchant_payment_methods_account', 'merchant_payment_methods', ['merchant_account_id'])
    op.create_index('idx_merchant_payment_methods_customer', 'merchant_payment_methods', ['stripe_customer_id'])


def downgrade() -> None:
    """Drop merchant onboarding tables"""
    # Drop indexes first
    op.drop_index('idx_merchant_payment_methods_customer', table_name='merchant_payment_methods')
    op.drop_index('idx_merchant_payment_methods_account', table_name='merchant_payment_methods')
    op.drop_index('ix_merchant_payment_methods_status', table_name='merchant_payment_methods')
    op.drop_index('ix_merchant_payment_methods_stripe_customer_id', table_name='merchant_payment_methods')
    op.drop_index('ix_merchant_payment_methods_merchant_account_id', table_name='merchant_payment_methods')
    op.drop_table('merchant_payment_methods')
    
    op.drop_index('idx_merchant_placement_rules_place', table_name='merchant_placement_rules')
    op.drop_index('idx_merchant_placement_rules_status', table_name='merchant_placement_rules')
    op.drop_index('ix_merchant_placement_rules_updated_at', table_name='merchant_placement_rules')
    op.drop_index('ix_merchant_placement_rules_status', table_name='merchant_placement_rules')
    op.drop_index('ix_merchant_placement_rules_place_id', table_name='merchant_placement_rules')
    op.drop_table('merchant_placement_rules')
    
    op.drop_index('idx_merchant_location_claims_place', table_name='merchant_location_claims')
    op.drop_index('idx_merchant_location_claims_account', table_name='merchant_location_claims')
    op.drop_index('ix_merchant_location_claims_status', table_name='merchant_location_claims')
    op.drop_index('ix_merchant_location_claims_place_id', table_name='merchant_location_claims')
    op.drop_index('ix_merchant_location_claims_merchant_account_id', table_name='merchant_location_claims')
    op.drop_table('merchant_location_claims')
    
    op.drop_index('idx_merchant_accounts_owner', table_name='merchant_accounts')
    op.drop_index('ix_merchant_accounts_owner_user_id', table_name='merchant_accounts')
    op.drop_table('merchant_accounts')



