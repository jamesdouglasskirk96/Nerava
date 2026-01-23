"""Domain Charge Party MVP - Core tables

Revision ID: 018
Revises: 017
Create Date: 2025-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = insp.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        indexes = insp.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)
    except Exception:
        return False


def upgrade() -> None:
    # 1. Extend users table with Domain Charge Party fields
    if _has_table('users'):
        if not _has_column('users', 'display_name'):
            op.add_column('users', sa.Column('display_name', sa.String(), nullable=True))
        if not _has_column('users', 'role_flags'):
            op.add_column('users', sa.Column('role_flags', sa.String(), nullable=True, server_default='driver'))
        if not _has_column('users', 'auth_provider'):
            op.add_column('users', sa.Column('auth_provider', sa.String(), nullable=False, server_default='local'))
        if not _has_column('users', 'oauth_sub'):
            op.add_column('users', sa.Column('oauth_sub', sa.String(), nullable=True))
        if not _has_column('users', 'updated_at'):
            op.add_column('users', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True))
    
    # 2. Create domain_merchants table (separate from merchants in while_you_charge)
    if not _has_table('domain_merchants'):
        op.create_table(
            'domain_merchants',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('google_place_id', sa.String(), nullable=True),
            sa.Column('addr_line1', sa.String(), nullable=True),
            sa.Column('city', sa.String(), nullable=True),
            sa.Column('state', sa.String(), nullable=True),
            sa.Column('postal_code', sa.String(), nullable=True),
            sa.Column('country', sa.String(), nullable=True, server_default='US'),
            sa.Column('lat', sa.Float(), nullable=False),
            sa.Column('lng', sa.Float(), nullable=False),
            sa.Column('public_phone', sa.String(), nullable=True),
            sa.Column('owner_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('status', sa.String(), nullable=False, server_default='pending'),
            sa.Column('nova_balance', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('domain_zone', sa.String(), nullable=False, server_default='domain_austin'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        )
        
        # Indexes for domain_merchants
        op.create_index('ix_domain_merchants_owner_user_id', 'domain_merchants', ['owner_user_id'])
        op.create_index('ix_domain_merchants_domain_zone_status', 'domain_merchants', ['domain_zone', 'status'])
        op.create_index('ix_domain_merchants_location', 'domain_merchants', ['lat', 'lng'])
    
    # 3. Create driver_wallets table
    if not _has_table('driver_wallets'):
        op.create_table(
            'driver_wallets',
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
            sa.Column('nova_balance', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('energy_reputation_score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        )
    
    # 4. Create nova_transactions table
    if not _has_table('nova_transactions'):
        op.create_table(
            'nova_transactions',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('type', sa.String(), nullable=False),  # driver_earn, driver_redeem, merchant_topup, admin_grant
            sa.Column('driver_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('merchant_id', sa.String(), sa.ForeignKey('domain_merchants.id'), nullable=True),
            sa.Column('amount', sa.Integer(), nullable=False),
            sa.Column('stripe_payment_id', sa.String(), sa.ForeignKey('stripe_payments.id'), nullable=True),
            sa.Column('session_id', sa.String(), sa.ForeignKey('domain_charging_sessions.id'), nullable=True),
            sa.Column('metadata', sa.Text(), nullable=True),  # JSON stored as text for SQLite compatibility
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, index=True),
        )
        
        # Indexes for nova_transactions
        op.create_index('ix_nova_transactions_driver_user_id', 'nova_transactions', ['driver_user_id'])
        op.create_index('ix_nova_transactions_merchant_id', 'nova_transactions', ['merchant_id'])
        op.create_index('ix_nova_transactions_type_created', 'nova_transactions', ['type', 'created_at'])
    
    # 5. Create domain_charging_sessions table
    if not _has_table('domain_charging_sessions'):
        op.create_table(
            'domain_charging_sessions',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('driver_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('charger_provider', sa.String(), nullable=False, server_default='manual'),
            sa.Column('start_time', sa.DateTime(), nullable=True),
            sa.Column('end_time', sa.DateTime(), nullable=True),
            sa.Column('kwh_estimate', sa.Float(), nullable=True),
            sa.Column('verified', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('verification_source', sa.String(), nullable=True),
            sa.Column('event_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        )
        
        # Indexes for domain_charging_sessions
        op.create_index('ix_domain_charging_sessions_driver_user_id', 'domain_charging_sessions', ['driver_user_id'])
        op.create_index('ix_domain_charging_sessions_event_id', 'domain_charging_sessions', ['event_id'])
        op.create_index('ix_domain_charging_sessions_verified', 'domain_charging_sessions', ['verified'])
    
    # 6. Create stripe_payments table
    if not _has_table('stripe_payments'):
        op.create_table(
            'stripe_payments',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('stripe_session_id', sa.String(), nullable=False, unique=True),
            sa.Column('stripe_payment_intent_id', sa.String(), nullable=True),
            sa.Column('merchant_id', sa.String(), sa.ForeignKey('domain_merchants.id'), nullable=True),
            sa.Column('amount_usd', sa.Integer(), nullable=False),  # in cents
            sa.Column('nova_issued', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(), nullable=False, server_default='pending'),
            sa.Column('stripe_event_id', sa.String(), nullable=True, unique=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        )
        
        # Indexes for stripe_payments
        op.create_index('ix_stripe_payments_merchant_id', 'stripe_payments', ['merchant_id'])
        op.create_index('ix_stripe_payments_status', 'stripe_payments', ['status'])
        op.create_index('ix_stripe_payments_stripe_payment_intent_id', 'stripe_payments', ['stripe_payment_intent_id'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    if _has_table('nova_transactions'):
        op.drop_table('nova_transactions')
    if _has_table('domain_charging_sessions'):
        op.drop_table('domain_charging_sessions')
    if _has_table('stripe_payments'):
        op.drop_table('stripe_payments')
    if _has_table('driver_wallets'):
        op.drop_table('driver_wallets')
    if _has_table('domain_merchants'):
        op.drop_table('domain_merchants')
    
    # Remove columns from users table (be careful - only if safe)
    if _has_table('users'):
        if _has_column('users', 'oauth_sub'):
            op.drop_column('users', 'oauth_sub')
        if _has_column('users', 'auth_provider'):
            op.drop_column('users', 'auth_provider')
        if _has_column('users', 'role_flags'):
            op.drop_column('users', 'role_flags')
        if _has_column('users', 'display_name'):
            op.drop_column('users', 'display_name')
        if _has_column('users', 'updated_at'):
            op.drop_column('users', 'updated_at')

