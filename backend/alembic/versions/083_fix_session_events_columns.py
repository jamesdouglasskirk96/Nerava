"""Fix session_events and incentive_grants tables - add missing columns

If the tables were created by metadata.create_all() without the full schema,
this migration adds any missing columns.

Revision ID: 083_fix_session_events
Revises: 082_credit_wallet_final
Create Date: 2026-02-27
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

revision = '083_fix_session_events'
down_revision = '082_credit_wallet_final'
branch_labels = None
depends_on = None


def _add_column_if_missing(inspector, table_name, column_name, column):
    """Add a column to a table if it doesn't already exist."""
    existing = [c['name'] for c in inspector.get_columns(table_name)]
    if column_name not in existing:
        op.add_column(table_name, column)
        return True
    return False


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    # --- Fix campaigns ---
    if 'campaigns' in existing_tables:
        cols_added = []
        for col_name, col_def in [
            ('sponsor_name', sa.Column('sponsor_name', sa.String(), nullable=True)),
            ('sponsor_email', sa.Column('sponsor_email', sa.String(), nullable=True)),
            ('sponsor_logo_url', sa.Column('sponsor_logo_url', sa.String(), nullable=True)),
            ('sponsor_type', sa.Column('sponsor_type', sa.String(), nullable=True)),
            ('name', sa.Column('name', sa.String(), nullable=True)),
            ('description', sa.Column('description', sa.Text(), nullable=True)),
            ('campaign_type', sa.Column('campaign_type', sa.String(), nullable=True, server_default='custom')),
            ('status', sa.Column('status', sa.String(), nullable=True, server_default='draft')),
            ('priority', sa.Column('priority', sa.Integer(), nullable=True, server_default='100')),
            ('budget_cents', sa.Column('budget_cents', sa.Integer(), nullable=True, server_default='0')),
            ('spent_cents', sa.Column('spent_cents', sa.Integer(), nullable=True, server_default='0')),
            ('cost_per_session_cents', sa.Column('cost_per_session_cents', sa.Integer(), nullable=True, server_default='0')),
            ('max_sessions', sa.Column('max_sessions', sa.Integer(), nullable=True)),
            ('sessions_granted', sa.Column('sessions_granted', sa.Integer(), nullable=True, server_default='0')),
            ('start_date', sa.Column('start_date', sa.DateTime(), nullable=True)),
            ('end_date', sa.Column('end_date', sa.DateTime(), nullable=True)),
            ('auto_renew', sa.Column('auto_renew', sa.Boolean(), nullable=True, server_default='0')),
            ('auto_renew_budget_cents', sa.Column('auto_renew_budget_cents', sa.Integer(), nullable=True)),
            ('max_grants_per_driver_per_day', sa.Column('max_grants_per_driver_per_day', sa.Integer(), nullable=True)),
            ('max_grants_per_driver_per_campaign', sa.Column('max_grants_per_driver_per_campaign', sa.Integer(), nullable=True)),
            ('max_grants_per_driver_per_charger', sa.Column('max_grants_per_driver_per_charger', sa.Integer(), nullable=True)),
            ('rule_charger_ids', sa.Column('rule_charger_ids', sa.JSON(), nullable=True)),
            ('rule_charger_networks', sa.Column('rule_charger_networks', sa.JSON(), nullable=True)),
            ('rule_zone_ids', sa.Column('rule_zone_ids', sa.JSON(), nullable=True)),
            ('rule_geo_center_lat', sa.Column('rule_geo_center_lat', sa.Float(), nullable=True)),
            ('rule_geo_center_lng', sa.Column('rule_geo_center_lng', sa.Float(), nullable=True)),
            ('rule_geo_radius_m', sa.Column('rule_geo_radius_m', sa.Integer(), nullable=True)),
            ('rule_time_start', sa.Column('rule_time_start', sa.String(), nullable=True)),
            ('rule_time_end', sa.Column('rule_time_end', sa.String(), nullable=True)),
            ('rule_days_of_week', sa.Column('rule_days_of_week', sa.JSON(), nullable=True)),
            ('rule_min_duration_minutes', sa.Column('rule_min_duration_minutes', sa.Integer(), nullable=True, server_default='15')),
            ('rule_max_duration_minutes', sa.Column('rule_max_duration_minutes', sa.Integer(), nullable=True)),
            ('rule_min_power_kw', sa.Column('rule_min_power_kw', sa.Float(), nullable=True)),
            ('rule_connector_types', sa.Column('rule_connector_types', sa.JSON(), nullable=True)),
            ('rule_driver_session_count_min', sa.Column('rule_driver_session_count_min', sa.Integer(), nullable=True)),
            ('rule_driver_session_count_max', sa.Column('rule_driver_session_count_max', sa.Integer(), nullable=True)),
            ('rule_driver_allowlist', sa.Column('rule_driver_allowlist', sa.JSON(), nullable=True)),
            ('created_by_user_id', sa.Column('created_by_user_id', sa.Integer(), nullable=True)),
            ('created_at', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now())),
            ('updated_at', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now())),
            ('campaign_metadata', sa.Column('campaign_metadata', sa.JSON(), nullable=True)),
        ]:
            if _add_column_if_missing(inspector, 'campaigns', col_name, col_def):
                cols_added.append(col_name)

        if cols_added:
            print(f"  Added {len(cols_added)} missing columns to campaigns: {cols_added}")

    # --- Fix session_events ---
    if 'session_events' in existing_tables:
        cols_added = []
        if _add_column_if_missing(inspector, 'session_events', 'driver_user_id',
                sa.Column('driver_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True)):
            cols_added.append('driver_user_id')
        if _add_column_if_missing(inspector, 'session_events', 'charger_id',
                sa.Column('charger_id', sa.String(), nullable=True)):
            cols_added.append('charger_id')
        if _add_column_if_missing(inspector, 'session_events', 'charger_network',
                sa.Column('charger_network', sa.String(), nullable=True)):
            cols_added.append('charger_network')
        if _add_column_if_missing(inspector, 'session_events', 'zone_id',
                sa.Column('zone_id', sa.String(), nullable=True)):
            cols_added.append('zone_id')
        if _add_column_if_missing(inspector, 'session_events', 'connector_type',
                sa.Column('connector_type', sa.String(), nullable=True)):
            cols_added.append('connector_type')
        if _add_column_if_missing(inspector, 'session_events', 'power_kw',
                sa.Column('power_kw', sa.Float(), nullable=True)):
            cols_added.append('power_kw')
        if _add_column_if_missing(inspector, 'session_events', 'session_start',
                sa.Column('session_start', sa.DateTime(), nullable=True)):
            cols_added.append('session_start')
        if _add_column_if_missing(inspector, 'session_events', 'session_end',
                sa.Column('session_end', sa.DateTime(), nullable=True)):
            cols_added.append('session_end')
        if _add_column_if_missing(inspector, 'session_events', 'duration_minutes',
                sa.Column('duration_minutes', sa.Integer(), nullable=True)):
            cols_added.append('duration_minutes')
        if _add_column_if_missing(inspector, 'session_events', 'kwh_delivered',
                sa.Column('kwh_delivered', sa.Float(), nullable=True)):
            cols_added.append('kwh_delivered')
        if _add_column_if_missing(inspector, 'session_events', 'source',
                sa.Column('source', sa.String(), nullable=True)):
            cols_added.append('source')
        if _add_column_if_missing(inspector, 'session_events', 'source_session_id',
                sa.Column('source_session_id', sa.String(), nullable=True)):
            cols_added.append('source_session_id')
        if _add_column_if_missing(inspector, 'session_events', 'verified',
                sa.Column('verified', sa.Boolean(), nullable=True, server_default='0')):
            cols_added.append('verified')
        if _add_column_if_missing(inspector, 'session_events', 'verification_method',
                sa.Column('verification_method', sa.String(), nullable=True)):
            cols_added.append('verification_method')
        if _add_column_if_missing(inspector, 'session_events', 'lat',
                sa.Column('lat', sa.Float(), nullable=True)):
            cols_added.append('lat')
        if _add_column_if_missing(inspector, 'session_events', 'lng',
                sa.Column('lng', sa.Float(), nullable=True)):
            cols_added.append('lng')
        if _add_column_if_missing(inspector, 'session_events', 'battery_start_pct',
                sa.Column('battery_start_pct', sa.Integer(), nullable=True)):
            cols_added.append('battery_start_pct')
        if _add_column_if_missing(inspector, 'session_events', 'battery_end_pct',
                sa.Column('battery_end_pct', sa.Integer(), nullable=True)):
            cols_added.append('battery_end_pct')
        if _add_column_if_missing(inspector, 'session_events', 'vehicle_id',
                sa.Column('vehicle_id', sa.String(), nullable=True)):
            cols_added.append('vehicle_id')
        if _add_column_if_missing(inspector, 'session_events', 'vehicle_vin',
                sa.Column('vehicle_vin', sa.String(), nullable=True)):
            cols_added.append('vehicle_vin')
        if _add_column_if_missing(inspector, 'session_events', 'ended_reason',
                sa.Column('ended_reason', sa.String(), nullable=True)):
            cols_added.append('ended_reason')
        if _add_column_if_missing(inspector, 'session_events', 'quality_score',
                sa.Column('quality_score', sa.Integer(), nullable=True)):
            cols_added.append('quality_score')
        if _add_column_if_missing(inspector, 'session_events', 'created_at',
                sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now())):
            cols_added.append('created_at')
        if _add_column_if_missing(inspector, 'session_events', 'updated_at',
                sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now())):
            cols_added.append('updated_at')
        if _add_column_if_missing(inspector, 'session_events', 'metadata',
                sa.Column('metadata', sa.JSON(), nullable=True)):
            cols_added.append('metadata')

        if cols_added:
            print(f"  Added {len(cols_added)} missing columns to session_events: {cols_added}")

        # Recreate indexes that may be missing
        for idx_name, idx_cols in [
            ('ix_session_events_driver_user_id', ['driver_user_id']),
            ('ix_session_events_charger_id', ['charger_id']),
            ('ix_session_events_session_start', ['session_start']),
            ('ix_session_events_created_at', ['created_at']),
            ('ix_session_events_driver_start', ['driver_user_id', 'session_start']),
        ]:
            try:
                op.create_index(idx_name, 'session_events', idx_cols)
            except Exception:
                pass

    # --- Fix incentive_grants ---
    if 'incentive_grants' in existing_tables:
        cols_added = []
        if _add_column_if_missing(inspector, 'incentive_grants', 'driver_user_id',
                sa.Column('driver_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True)):
            cols_added.append('driver_user_id')
        if _add_column_if_missing(inspector, 'incentive_grants', 'session_event_id',
                sa.Column('session_event_id', sa.String(36), sa.ForeignKey('session_events.id'), nullable=True)):
            cols_added.append('session_event_id')
        if _add_column_if_missing(inspector, 'incentive_grants', 'campaign_id',
                sa.Column('campaign_id', sa.String(36), sa.ForeignKey('campaigns.id'), nullable=True)):
            cols_added.append('campaign_id')
        if _add_column_if_missing(inspector, 'incentive_grants', 'amount_cents',
                sa.Column('amount_cents', sa.Integer(), nullable=True)):
            cols_added.append('amount_cents')
        if _add_column_if_missing(inspector, 'incentive_grants', 'status',
                sa.Column('status', sa.String(), nullable=True, server_default='pending')):
            cols_added.append('status')
        if _add_column_if_missing(inspector, 'incentive_grants', 'nova_transaction_id',
                sa.Column('nova_transaction_id', sa.String(36), nullable=True)):
            cols_added.append('nova_transaction_id')
        if _add_column_if_missing(inspector, 'incentive_grants', 'idempotency_key',
                sa.Column('idempotency_key', sa.String(), nullable=True)):
            cols_added.append('idempotency_key')
        if _add_column_if_missing(inspector, 'incentive_grants', 'granted_at',
                sa.Column('granted_at', sa.DateTime(), nullable=True)):
            cols_added.append('granted_at')
        if _add_column_if_missing(inspector, 'incentive_grants', 'created_at',
                sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now())):
            cols_added.append('created_at')
        if _add_column_if_missing(inspector, 'incentive_grants', 'metadata',
                sa.Column('metadata', sa.JSON(), nullable=True)):
            cols_added.append('metadata')

        if cols_added:
            print(f"  Added {len(cols_added)} missing columns to incentive_grants: {cols_added}")

        for idx_name, idx_cols in [
            ('ix_incentive_grants_driver_user_id', ['driver_user_id']),
            ('ix_incentive_grants_campaign_id', ['campaign_id']),
            ('ix_incentive_grants_session_event_id', ['session_event_id']),
            ('ix_incentive_grants_driver_created', ['driver_user_id', 'created_at']),
        ]:
            try:
                op.create_index(idx_name, 'incentive_grants', idx_cols)
            except Exception:
                pass


def downgrade() -> None:
    # Not reversible - columns should stay
    pass
