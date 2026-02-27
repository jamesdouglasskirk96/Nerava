"""Fix campaigns table - add missing columns

The campaigns table was created by metadata.create_all() with incomplete schema.
Migration 074 skipped it because the table already existed.

Revision ID: 084_fix_campaigns
Revises: 083_fix_session_events
Create Date: 2026-02-27
"""
from alembic import op
from sqlalchemy import inspect as sa_inspect
import sqlalchemy as sa

revision = '084_fix_campaigns'
down_revision = '083_fix_session_events'
branch_labels = None
depends_on = None


def _add_column_if_missing(inspector, table_name, column_name, column):
    existing = [c['name'] for c in inspector.get_columns(table_name)]
    if column_name not in existing:
        op.add_column(table_name, column)
        return True
    return False


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'campaigns' not in existing_tables:
        return

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

    # Recreate indexes
    for idx_name, idx_cols in [
        ('ix_campaigns_status_priority', ['status', 'priority']),
        ('ix_campaigns_sponsor', ['sponsor_name']),
        ('ix_campaigns_start_end', ['start_date', 'end_date']),
    ]:
        try:
            op.create_index(idx_name, 'campaigns', idx_cols)
        except Exception:
            pass


def downgrade() -> None:
    pass
