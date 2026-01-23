"""Add anti-fraud tables and tracking

Revision ID: 009
Revises: 008
Create Date: 2025-10-29 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Create verify_attempts table
    try:
        op.create_table(
            'verify_attempts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(200), nullable=True),
            sa.Column('ip', sa.String(100), nullable=True),
            sa.Column('ua', sa.String(500), nullable=True),
            sa.Column('accuracy_m', sa.Float(), nullable=True),
            sa.Column('outcome', sa.String(50), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_verify_attempts_user_created', 'verify_attempts', ['user_id', 'created_at'])
        op.create_index('idx_verify_attempts_session', 'verify_attempts', ['session_id'])
    except Exception:
        pass
    
    # Create device_fingerprints table
    try:
        op.create_table(
            'device_fingerprints',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('device_hash', sa.String(64), nullable=False),
            sa.Column('first_seen', sa.DateTime(), nullable=False),
            sa.Column('last_seen', sa.DateTime(), nullable=False),
            sa.Column('ua', sa.String(500), nullable=True),
            sa.Column('last_ip', sa.String(100), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_device_fingerprints_user_hash', 'device_fingerprints', ['user_id', 'device_hash'])
        op.create_index('idx_device_fingerprints_hash', 'device_fingerprints', ['device_hash'])
    except Exception:
        pass
    
    # Create abuse_events table
    try:
        op.create_table(
            'abuse_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('type', sa.String(100), nullable=False),
            sa.Column('severity', sa.Integer(), nullable=False),
            sa.Column('details_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_abuse_events_user_created', 'abuse_events', ['user_id', 'created_at'])
    except Exception:
        pass


def downgrade():
    try:
        op.drop_index('idx_abuse_events_user_created', 'abuse_events')
        op.drop_table('abuse_events')
        op.drop_index('idx_device_fingerprints_hash', 'device_fingerprints')
        op.drop_index('idx_device_fingerprints_user_hash', 'device_fingerprints')
        op.drop_table('device_fingerprints')
        op.drop_index('idx_verify_attempts_session', 'verify_attempts')
        op.drop_index('idx_verify_attempts_user_created', 'verify_attempts')
        op.drop_table('verify_attempts')
    except Exception:
        pass

