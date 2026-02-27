"""Add campaigns, session_events, incentive_grants tables and nova_transactions.campaign_id

Revision ID: 074_campaign_pivot
Revises: 073_add_driver_wallet_and_payouts
Create Date: 2026-02-23
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

# revision identifiers
revision = '074_campaign_pivot'
down_revision = '073'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    # --- campaigns ---
    if 'campaigns' not in existing_tables:
        op.create_table(
            'campaigns',
            sa.Column('id', sa.String(36), primary_key=True),
            # Sponsor
            sa.Column('sponsor_name', sa.String(), nullable=False),
            sa.Column('sponsor_email', sa.String(), nullable=True),
            sa.Column('sponsor_logo_url', sa.String(), nullable=True),
            sa.Column('sponsor_type', sa.String(), nullable=True),
            # Basics
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('campaign_type', sa.String(), nullable=False, server_default='custom'),
            sa.Column('status', sa.String(), nullable=False, server_default='draft'),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
            # Budget
            sa.Column('budget_cents', sa.Integer(), nullable=False),
            sa.Column('spent_cents', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('cost_per_session_cents', sa.Integer(), nullable=False),
            sa.Column('max_sessions', sa.Integer(), nullable=True),
            sa.Column('sessions_granted', sa.Integer(), nullable=False, server_default='0'),
            # Schedule
            sa.Column('start_date', sa.DateTime(), nullable=False),
            sa.Column('end_date', sa.DateTime(), nullable=True),
            sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('auto_renew_budget_cents', sa.Integer(), nullable=True),
            # Driver caps
            sa.Column('max_grants_per_driver_per_day', sa.Integer(), nullable=True),
            sa.Column('max_grants_per_driver_per_campaign', sa.Integer(), nullable=True),
            sa.Column('max_grants_per_driver_per_charger', sa.Integer(), nullable=True),
            # Targeting rules (JSON columns)
            sa.Column('rule_charger_ids', sa.JSON(), nullable=True),
            sa.Column('rule_charger_networks', sa.JSON(), nullable=True),
            sa.Column('rule_zone_ids', sa.JSON(), nullable=True),
            sa.Column('rule_geo_center_lat', sa.Float(), nullable=True),
            sa.Column('rule_geo_center_lng', sa.Float(), nullable=True),
            sa.Column('rule_geo_radius_m', sa.Integer(), nullable=True),
            sa.Column('rule_time_start', sa.String(), nullable=True),
            sa.Column('rule_time_end', sa.String(), nullable=True),
            sa.Column('rule_days_of_week', sa.JSON(), nullable=True),
            sa.Column('rule_min_duration_minutes', sa.Integer(), nullable=False, server_default='15'),
            sa.Column('rule_max_duration_minutes', sa.Integer(), nullable=True),
            sa.Column('rule_min_power_kw', sa.Float(), nullable=True),
            sa.Column('rule_connector_types', sa.JSON(), nullable=True),
            sa.Column('rule_driver_session_count_min', sa.Integer(), nullable=True),
            sa.Column('rule_driver_session_count_max', sa.Integer(), nullable=True),
            sa.Column('rule_driver_allowlist', sa.JSON(), nullable=True),
            # Metadata
            sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('campaign_metadata', sa.JSON(), nullable=True),
        )
    try:
        op.create_index('ix_campaigns_status_priority', 'campaigns', ['status', 'priority'])
    except Exception:
        pass
    try:
        op.create_index('ix_campaigns_sponsor', 'campaigns', ['sponsor_name'])
    except Exception:
        pass
    try:
        op.create_index('ix_campaigns_start_end', 'campaigns', ['start_date', 'end_date'])
    except Exception:
        pass

    # --- session_events ---
    if 'session_events' not in existing_tables:
        op.create_table(
            'session_events',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('driver_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            # Charger
            sa.Column('charger_id', sa.String(), sa.ForeignKey('chargers.id'), nullable=True),
            sa.Column('charger_network', sa.String(), nullable=True),
            sa.Column('zone_id', sa.String(), nullable=True),
            sa.Column('connector_type', sa.String(), nullable=True),
            sa.Column('power_kw', sa.Float(), nullable=True),
            # Timing
            sa.Column('session_start', sa.DateTime(), nullable=False),
            sa.Column('session_end', sa.DateTime(), nullable=True),
            sa.Column('duration_minutes', sa.Integer(), nullable=True),
            # Energy
            sa.Column('kwh_delivered', sa.Float(), nullable=True),
            # Source
            sa.Column('source', sa.String(), nullable=False, server_default='tesla_api'),
            sa.Column('source_session_id', sa.String(), nullable=True),
            sa.Column('verified', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('verification_method', sa.String(), nullable=True),
            # Location
            sa.Column('lat', sa.Float(), nullable=True),
            sa.Column('lng', sa.Float(), nullable=True),
            # Vehicle
            sa.Column('battery_start_pct', sa.Integer(), nullable=True),
            sa.Column('battery_end_pct', sa.Integer(), nullable=True),
            sa.Column('vehicle_id', sa.String(), nullable=True),
            sa.Column('vehicle_vin', sa.String(), nullable=True),
            # Anti-fraud
            sa.Column('ended_reason', sa.String(), nullable=True),
            sa.Column('quality_score', sa.Integer(), nullable=True),
            # Metadata
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('metadata', sa.JSON(), nullable=True),
        )
    try:
        op.create_index('ix_session_events_driver_user_id', 'session_events', ['driver_user_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_session_events_charger_id', 'session_events', ['charger_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_session_events_zone_id', 'session_events', ['zone_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_session_events_session_start', 'session_events', ['session_start'])
    except Exception:
        pass
    try:
        op.create_index('ix_session_events_created_at', 'session_events', ['created_at'])
    except Exception:
        pass
    try:
        op.create_index('ix_session_events_driver_start', 'session_events', ['driver_user_id', 'session_start'])
    except Exception:
        pass
    try:
        op.create_index('ix_session_events_charger_start', 'session_events', ['charger_id', 'session_start'])
    except Exception:
        pass
    try:
        op.create_unique_constraint('uq_session_source', 'session_events', ['source', 'source_session_id'])
    except Exception:
        pass

    # --- incentive_grants ---
    if 'incentive_grants' not in existing_tables:
        op.create_table(
            'incentive_grants',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('session_event_id', sa.String(36), sa.ForeignKey('session_events.id'), nullable=False),
            sa.Column('campaign_id', sa.String(36), sa.ForeignKey('campaigns.id'), nullable=False),
            sa.Column('driver_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('amount_cents', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(), nullable=False, server_default='pending'),
            sa.Column('nova_transaction_id', sa.String(36), sa.ForeignKey('nova_transactions.id'), nullable=True),
            sa.Column('idempotency_key', sa.String(), nullable=False),
            sa.Column('granted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('metadata', sa.JSON(), nullable=True),
        )
    try:
        op.create_index('ix_incentive_grants_session_event_id', 'incentive_grants', ['session_event_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_incentive_grants_campaign_id', 'incentive_grants', ['campaign_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_incentive_grants_driver_user_id', 'incentive_grants', ['driver_user_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_incentive_grants_idempotency_key', 'incentive_grants', ['idempotency_key'], unique=True)
    except Exception:
        pass
    try:
        op.create_unique_constraint('uq_one_grant_per_session', 'incentive_grants', ['session_event_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_incentive_grants_campaign_created', 'incentive_grants', ['campaign_id', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('ix_incentive_grants_driver_created', 'incentive_grants', ['driver_user_id', 'created_at'])
    except Exception:
        pass

    # --- Add campaign_id to nova_transactions ---
    existing_columns = [c['name'] for c in inspector.get_columns('nova_transactions')] if 'nova_transactions' in existing_tables else []
    if 'campaign_id' not in existing_columns:
        op.add_column('nova_transactions', sa.Column('campaign_id', sa.String(36), nullable=True))
    try:
        op.create_index('ix_nova_transactions_campaign_id', 'nova_transactions', ['campaign_id'])
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index('ix_nova_transactions_campaign_id', table_name='nova_transactions')
    op.drop_column('nova_transactions', 'campaign_id')
    op.drop_table('incentive_grants')
    op.drop_table('session_events')
    op.drop_table('campaigns')
