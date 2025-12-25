"""Add GPT-related tables

Revision ID: 005
Revises: 004
Create Date: 2025-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text as sql_text

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def _table_exists(conn, table_name, is_postgres):
    """Check if table exists"""
    if is_postgres:
        result = conn.execute(sql_text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :name)"
        ), {"name": table_name})
        return result.scalar()
    else:
        result = conn.execute(sql_text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
        ), {"name": table_name})
        return result.first() is not None


def upgrade():
    # Detect database type for compatibility
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'
    conn = bind
    
    # Use appropriate JSON type
    if is_postgres:
        json_type = postgresql.JSON
        text_type = sa.Text
    else:
        # SQLite
        json_type = sa.Text  # SQLite uses TEXT for JSON
        text_type = sa.Text
    
    # Users table (if not exists, add handle field)
    # Skip if users table doesn't exist - it will be created later by migration d0dc1d5111a3
    if _table_exists(conn, 'users', is_postgres):
        try:
            op.add_column('users', sa.Column('handle', sa.String(50), nullable=True, unique=True))
            op.create_index('idx_users_handle', 'users', ['handle'])
        except Exception:
            pass  # Column might already exist

    # Follows table
    if not _table_exists(conn, 'follows', is_postgres):
        op.create_table('follows',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('follower_id', sa.Integer(), nullable=False),
            sa.Column('following_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('follower_id', 'following_id', name='uq_follows_follower_following')
        )
        op.create_index('idx_follows_follower', 'follows', ['follower_id'])
        op.create_index('idx_follows_following', 'follows', ['following_id'])
    
    # Merchants table (main merchants, not merchants_local)
    if not _table_exists(conn, 'merchants', is_postgres):
        op.create_table('merchants',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('category', sa.String(50), nullable=False),
            sa.Column('lat', sa.Float(), nullable=False),
            sa.Column('lng', sa.Float(), nullable=False),
            sa.Column('address', sa.String(500), nullable=True),
            sa.Column('logo_url', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_merchants_category', 'merchants', ['category'])
        op.create_index('idx_merchants_location', 'merchants', ['lat', 'lng'])
    
    # Offers table
    if not _table_exists(conn, 'offers', is_postgres):
        op.create_table('offers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('merchant_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', text_type, nullable=True),
            sa.Column('reward_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('start_time', sa.Time(), nullable=True),  # e.g., 14:00
            sa.Column('end_time', sa.Time(), nullable=True),    # e.g., 16:00
            sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], name='fk_offers_merchant'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_offers_merchant', 'offers', ['merchant_id'])
        op.create_index('idx_offers_active', 'offers', ['active'])
    
    # Sessions table
    if not _table_exists(conn, 'sessions', is_postgres):
        op.create_table('sessions',
            sa.Column('id', sa.String(100), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('session_type', sa.String(50), nullable=False, server_default='gpt'),
            sa.Column('data', json_type, nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_sessions_user', 'sessions', ['user_id'])
        op.create_index('idx_sessions_expires', 'sessions', ['expires_at'])
    
    # Payments table
    if not _table_exists(conn, 'payments', is_postgres):
        op.create_table('payments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('merchant_id', sa.Integer(), nullable=True),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('payment_method', sa.String(50), nullable=False),
            sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
            sa.Column('transaction_id', sa.String(200), nullable=True),
            sa.Column('metadata', json_type, nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_payments_user', 'payments', ['user_id'])
        op.create_index('idx_payments_merchant', 'payments', ['merchant_id'])
        op.create_index('idx_payments_status', 'payments', ['status'])
    
    # Reward events table
    if not _table_exists(conn, 'reward_events', is_postgres):
        op.create_table('reward_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('offer_id', sa.Integer(), nullable=True),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('reward_type', sa.String(50), nullable=False),
            sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
            sa.Column('metadata', json_type, nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], name='fk_reward_events_offer'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_reward_events_user', 'reward_events', ['user_id'])
        op.create_index('idx_reward_events_offer', 'reward_events', ['offer_id'])
        op.create_index('idx_reward_events_status', 'reward_events', ['status'])
    
    # Wallet ledger table
    if not _table_exists(conn, 'wallet_ledger', is_postgres):
        op.create_table('wallet_ledger',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('transaction_type', sa.String(50), nullable=False),
            sa.Column('reference_id', sa.String(200), nullable=True),
            sa.Column('reference_type', sa.String(50), nullable=True),
            sa.Column('balance_cents', sa.Integer(), nullable=False),
            sa.Column('metadata', json_type, nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_wallet_ledger_user', 'wallet_ledger', ['user_id'])
        op.create_index('idx_wallet_ledger_reference', 'wallet_ledger', ['reference_type', 'reference_id'])
        op.create_index('idx_wallet_ledger_created', 'wallet_ledger', ['created_at'])
    
    # Community pool table
    if not _table_exists(conn, 'community_pool', is_postgres):
        op.create_table('community_pool',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('pool_name', sa.String(100), nullable=False),
            sa.Column('total_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('allocated_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status', sa.String(50), nullable=False, server_default='active'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('pool_name', name='uq_community_pool_name')
        )
    
    # Community allocations table
    if not _table_exists(conn, 'community_allocations', is_postgres):
        op.create_table('community_allocations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('pool_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('reason', sa.String(200), nullable=True),
            sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['pool_id'], ['community_pool.id'], name='fk_community_allocations_pool'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_community_allocations_pool', 'community_allocations', ['pool_id'])
        op.create_index('idx_community_allocations_user', 'community_allocations', ['user_id'])


def downgrade():
    op.drop_index('idx_community_allocations_user', 'community_allocations')
    op.drop_index('idx_community_allocations_pool', 'community_allocations')
    op.drop_table('community_allocations')
    op.drop_table('community_pool')
    op.drop_index('idx_wallet_ledger_created', 'wallet_ledger')
    op.drop_index('idx_wallet_ledger_reference', 'wallet_ledger')
    op.drop_index('idx_wallet_ledger_user', 'wallet_ledger')
    op.drop_table('wallet_ledger')
    op.drop_index('idx_reward_events_status', 'reward_events')
    op.drop_index('idx_reward_events_offer', 'reward_events')
    op.drop_index('idx_reward_events_user', 'reward_events')
    op.drop_table('reward_events')
    op.drop_index('idx_payments_status', 'payments')
    op.drop_index('idx_payments_merchant', 'payments')
    op.drop_index('idx_payments_user', 'payments')
    op.drop_table('payments')
    op.drop_index('idx_sessions_expires', 'sessions')
    op.drop_index('idx_sessions_user', 'sessions')
    op.drop_table('sessions')
    op.drop_index('idx_offers_active', 'offers')
    op.drop_index('idx_offers_merchant', 'offers')
    op.drop_table('offers')
    op.drop_index('idx_merchants_location', 'merchants')
    op.drop_index('idx_merchants_category', 'merchants')
    op.drop_table('merchants')
    op.drop_index('idx_follows_following', 'follows')
    op.drop_index('idx_follows_follower', 'follows')
    op.drop_table('follows')
    try:
        op.drop_index('idx_users_handle', 'users')
        op.drop_column('users', 'handle')
    except Exception:
        pass
