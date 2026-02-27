"""Add Tesla connection and EV verification code tables

Revision ID: 072
Revises: 071_fix_arrival_sessions_id_type
Create Date: 2026-02-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '072'
down_revision = '071'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS tesla_connections (
            id VARCHAR(36) PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            token_expires_at TIMESTAMP NOT NULL,
            tesla_user_id VARCHAR(100),
            vehicle_id VARCHAR(100),
            vin VARCHAR(17),
            vehicle_name VARCHAR(100),
            vehicle_model VARCHAR(50),
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP,
            last_used_at TIMESTAMP
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS ev_verification_codes (
            id VARCHAR(36) PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            tesla_connection_id VARCHAR(36),
            code VARCHAR(10) UNIQUE NOT NULL,
            charger_id VARCHAR(100),
            merchant_place_id VARCHAR(255),
            merchant_name VARCHAR(255),
            charging_verified BOOLEAN NOT NULL DEFAULT false,
            battery_level INTEGER,
            charge_rate_kw INTEGER,
            lat VARCHAR(20),
            lng VARCHAR(20),
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            expires_at TIMESTAMP NOT NULL,
            redeemed_at TIMESTAMP
        )
    """))

    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_tesla_connection_user ON tesla_connections(user_id)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_tesla_connection_vehicle ON tesla_connections(vehicle_id)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_ev_code ON ev_verification_codes(code)"
    ))
    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS idx_ev_code_user_status ON ev_verification_codes(user_id, status)"
    ))


def downgrade():
    op.drop_table('ev_verification_codes')
    op.drop_table('tesla_connections')
