"""add intent models

Revision ID: 045_add_intent_models
Revises: 044_add_hubspot_outbox
Create Date: 2025-02-01 12:00:00.000000

Adds intent capture models: IntentSession, VehicleOnboarding, MerchantCache, PerkUnlock, WalletPassState
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '045_add_intent_models'
down_revision = '044_add_hubspot_outbox'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create intent capture tables"""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Use JSON for PostgreSQL, TEXT for SQLite
    json_type = sa.JSON() if dialect_name != 'sqlite' else sa.Text()
    
    # UUID type handling
    uuid_type = sa.String(36) if dialect_name == 'sqlite' else sa.UUID()
    
    # IntentSession table
    op.create_table(
        'intent_sessions',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('accuracy_m', sa.Float(), nullable=True),
        sa.Column('client_ts', sa.DateTime(), nullable=True),
        sa.Column('charger_id', sa.String(), nullable=True),
        sa.Column('charger_distance_m', sa.Float(), nullable=True),
        sa.Column('confidence_tier', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False, server_default='web'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['charger_id'], ['chargers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_intent_sessions_user_id', 'intent_sessions', ['user_id'])
    op.create_index('ix_intent_sessions_lat', 'intent_sessions', ['lat'])
    op.create_index('ix_intent_sessions_lng', 'intent_sessions', ['lng'])
    op.create_index('ix_intent_sessions_charger_id', 'intent_sessions', ['charger_id'])
    op.create_index('ix_intent_sessions_confidence_tier', 'intent_sessions', ['confidence_tier'])
    op.create_index('ix_intent_sessions_created_at', 'intent_sessions', ['created_at'])
    op.create_index('idx_intent_sessions_user_created', 'intent_sessions', ['user_id', 'created_at'])
    op.create_index('idx_intent_sessions_location', 'intent_sessions', ['lat', 'lng'])
    op.create_index('idx_intent_sessions_confidence', 'intent_sessions', ['confidence_tier', 'created_at'])
    
    # VehicleOnboarding table
    op.create_table(
        'vehicle_onboarding',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='SUBMITTED'),
        sa.Column('photo_urls', sa.Text(), nullable=False),
        sa.Column('license_plate', sa.String(), nullable=True),
        sa.Column('intent_session_id', uuid_type, nullable=True),
        sa.Column('charger_id', sa.String(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['intent_session_id'], ['intent_sessions.id'], ),
        sa.ForeignKeyConstraint(['charger_id'], ['chargers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_vehicle_onboarding_user_id', 'vehicle_onboarding', ['user_id'])
    op.create_index('ix_vehicle_onboarding_status', 'vehicle_onboarding', ['status'])
    op.create_index('ix_vehicle_onboarding_intent_session_id', 'vehicle_onboarding', ['intent_session_id'])
    op.create_index('ix_vehicle_onboarding_created_at', 'vehicle_onboarding', ['created_at'])
    op.create_index('ix_vehicle_onboarding_expires_at', 'vehicle_onboarding', ['expires_at'])
    op.create_index('idx_vehicle_onboarding_user_status', 'vehicle_onboarding', ['user_id', 'status'])
    op.create_index('idx_vehicle_onboarding_status_created', 'vehicle_onboarding', ['status', 'created_at'])
    op.create_index('idx_vehicle_onboarding_expires', 'vehicle_onboarding', ['expires_at'])
    
    # MerchantCache table
    op.create_table(
        'merchant_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('place_id', sa.String(), nullable=False),
        sa.Column('geo_cell_lat', sa.Float(), nullable=False),
        sa.Column('geo_cell_lng', sa.Float(), nullable=False),
        sa.Column('merchant_data', json_type, nullable=False),
        sa.Column('photo_url', sa.String(), nullable=True),
        sa.Column('cached_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_merchant_cache_place_id', 'merchant_cache', ['place_id'])
    op.create_index('ix_merchant_cache_geo_cell_lat', 'merchant_cache', ['geo_cell_lat'])
    op.create_index('ix_merchant_cache_geo_cell_lng', 'merchant_cache', ['geo_cell_lng'])
    op.create_index('ix_merchant_cache_cached_at', 'merchant_cache', ['cached_at'])
    op.create_index('ix_merchant_cache_expires_at', 'merchant_cache', ['expires_at'])
    op.create_index('idx_merchant_cache_place_geo', 'merchant_cache', ['place_id', 'geo_cell_lat', 'geo_cell_lng'])
    op.create_index('idx_merchant_cache_geo', 'merchant_cache', ['geo_cell_lat', 'geo_cell_lng'])
    op.create_index('idx_merchant_cache_expires', 'merchant_cache', ['expires_at'])
    
    # PerkUnlock table
    op.create_table(
        'perk_unlocks',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('perk_id', sa.Integer(), nullable=False),
        sa.Column('unlock_method', sa.String(), nullable=False),
        sa.Column('intent_session_id', uuid_type, nullable=True),
        sa.Column('merchant_id', sa.String(), nullable=True),
        sa.Column('dwell_time_seconds', sa.Integer(), nullable=True),
        sa.Column('unlocked_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['perk_id'], ['merchant_perks.id'], ),
        sa.ForeignKeyConstraint(['intent_session_id'], ['intent_sessions.id'], ),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_perk_unlocks_user_id', 'perk_unlocks', ['user_id'])
    op.create_index('ix_perk_unlocks_perk_id', 'perk_unlocks', ['perk_id'])
    op.create_index('ix_perk_unlocks_intent_session_id', 'perk_unlocks', ['intent_session_id'])
    op.create_index('ix_perk_unlocks_merchant_id', 'perk_unlocks', ['merchant_id'])
    op.create_index('ix_perk_unlocks_unlocked_at', 'perk_unlocks', ['unlocked_at'])
    op.create_index('idx_perk_unlocks_user_perk', 'perk_unlocks', ['user_id', 'perk_id'])
    op.create_index('idx_perk_unlocks_user_unlocked', 'perk_unlocks', ['user_id', 'unlocked_at'])
    op.create_index('idx_perk_unlocks_perk_unlocked', 'perk_unlocks', ['perk_id', 'unlocked_at'])
    
    # WalletPassState table
    op.create_table(
        'wallet_pass_state',
        sa.Column('id', uuid_type, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(), nullable=False, server_default='IDLE'),
        sa.Column('intent_session_id', uuid_type, nullable=True),
        sa.Column('perk_id', sa.Integer(), nullable=True),
        sa.Column('state_changed_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['intent_session_id'], ['intent_sessions.id'], ),
        sa.ForeignKeyConstraint(['perk_id'], ['merchant_perks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_wallet_pass_state_user_id', 'wallet_pass_state', ['user_id'])
    op.create_index('ix_wallet_pass_state_state', 'wallet_pass_state', ['state'])
    op.create_index('ix_wallet_pass_state_intent_session_id', 'wallet_pass_state', ['intent_session_id'])
    op.create_index('ix_wallet_pass_state_perk_id', 'wallet_pass_state', ['perk_id'])
    op.create_index('ix_wallet_pass_state_created_at', 'wallet_pass_state', ['created_at'])
    op.create_index('idx_wallet_pass_state_user_state', 'wallet_pass_state', ['user_id', 'state'])
    op.create_index('idx_wallet_pass_state_user_created', 'wallet_pass_state', ['user_id', 'created_at'])


def downgrade() -> None:
    """Drop intent capture tables"""
    # Drop indexes first
    op.drop_index('idx_wallet_pass_state_user_created', table_name='wallet_pass_state')
    op.drop_index('idx_wallet_pass_state_user_state', table_name='wallet_pass_state')
    op.drop_index('ix_wallet_pass_state_created_at', table_name='wallet_pass_state')
    op.drop_index('ix_wallet_pass_state_perk_id', table_name='wallet_pass_state')
    op.drop_index('ix_wallet_pass_state_intent_session_id', table_name='wallet_pass_state')
    op.drop_index('ix_wallet_pass_state_state', table_name='wallet_pass_state')
    op.drop_index('ix_wallet_pass_state_user_id', table_name='wallet_pass_state')
    op.drop_table('wallet_pass_state')
    
    op.drop_index('idx_perk_unlocks_perk_unlocked', table_name='perk_unlocks')
    op.drop_index('idx_perk_unlocks_user_unlocked', table_name='perk_unlocks')
    op.drop_index('idx_perk_unlocks_user_perk', table_name='perk_unlocks')
    op.drop_index('ix_perk_unlocks_unlocked_at', table_name='perk_unlocks')
    op.drop_index('ix_perk_unlocks_merchant_id', table_name='perk_unlocks')
    op.drop_index('ix_perk_unlocks_intent_session_id', table_name='perk_unlocks')
    op.drop_index('ix_perk_unlocks_perk_id', table_name='perk_unlocks')
    op.drop_index('ix_perk_unlocks_user_id', table_name='perk_unlocks')
    op.drop_table('perk_unlocks')
    
    op.drop_index('idx_merchant_cache_expires', table_name='merchant_cache')
    op.drop_index('idx_merchant_cache_geo', table_name='merchant_cache')
    op.drop_index('idx_merchant_cache_place_geo', table_name='merchant_cache')
    op.drop_index('ix_merchant_cache_expires_at', table_name='merchant_cache')
    op.drop_index('ix_merchant_cache_cached_at', table_name='merchant_cache')
    op.drop_index('ix_merchant_cache_geo_cell_lng', table_name='merchant_cache')
    op.drop_index('ix_merchant_cache_geo_cell_lat', table_name='merchant_cache')
    op.drop_index('ix_merchant_cache_place_id', table_name='merchant_cache')
    op.drop_table('merchant_cache')
    
    op.drop_index('idx_vehicle_onboarding_expires', table_name='vehicle_onboarding')
    op.drop_index('idx_vehicle_onboarding_status_created', table_name='vehicle_onboarding')
    op.drop_index('idx_vehicle_onboarding_user_status', table_name='vehicle_onboarding')
    op.drop_index('ix_vehicle_onboarding_expires_at', table_name='vehicle_onboarding')
    op.drop_index('ix_vehicle_onboarding_created_at', table_name='vehicle_onboarding')
    op.drop_index('ix_vehicle_onboarding_intent_session_id', table_name='vehicle_onboarding')
    op.drop_index('ix_vehicle_onboarding_status', table_name='vehicle_onboarding')
    op.drop_index('ix_vehicle_onboarding_user_id', table_name='vehicle_onboarding')
    op.drop_table('vehicle_onboarding')
    
    op.drop_index('idx_intent_sessions_confidence', table_name='intent_sessions')
    op.drop_index('idx_intent_sessions_location', table_name='intent_sessions')
    op.drop_index('idx_intent_sessions_user_created', table_name='intent_sessions')
    op.drop_index('ix_intent_sessions_created_at', table_name='intent_sessions')
    op.drop_index('ix_intent_sessions_confidence_tier', table_name='intent_sessions')
    op.drop_index('ix_intent_sessions_charger_id', table_name='intent_sessions')
    op.drop_index('ix_intent_sessions_lng', table_name='intent_sessions')
    op.drop_index('ix_intent_sessions_lat', table_name='intent_sessions')
    op.drop_index('ix_intent_sessions_user_id', table_name='intent_sessions')
    op.drop_table('intent_sessions')



