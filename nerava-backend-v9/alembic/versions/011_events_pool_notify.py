"""add events, verifications, pool, notifications

Revision ID: 011_events_pool_notify
Revises: 010_merchant_keys
Create Date: 2025-10-29 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # Create events table
    op.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activator_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            city TEXT,
            lat REAL,
            lng REAL,
            starts_at TIMESTAMP NOT NULL,
            ends_at TIMESTAMP NOT NULL,
            green_window_start TEXT,
            green_window_end TEXT,
            price_cents INTEGER DEFAULT 0,
            revenue_split_json TEXT,
            capacity INTEGER,
            visibility TEXT DEFAULT 'public',
            status TEXT DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activator_id) REFERENCES users(id)
        )
    """)
    
    # Create indexes for events
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_city_starts 
        ON events(city, starts_at)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_lat_lng 
        ON events(lat, lng)
    """)
    
    # Create event_attendance table
    op.execute("""
        CREATE TABLE IF NOT EXISTS event_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            state TEXT DEFAULT 'invited',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(event_id, user_id)
        )
    """)
    
    # Create verifications table
    op.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            mode TEXT NOT NULL,
            charger_id TEXT,
            merchant_id INTEGER,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            lat REAL,
            lng REAL,
            photo_url TEXT,
            status TEXT DEFAULT 'pending',
            meta_json TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)
    
    # Create index for verifications
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_verifications_user_started 
        ON verifications(user_id, started_at)
    """)
    
    # Create pool_ledger table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pool_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            source TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            city TEXT,
            related_event_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (related_event_id) REFERENCES events(id)
        )
    """)
    
    # Create notification_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            payload_json TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create index for notification_logs
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_notification_logs_user_sent 
        ON notification_logs(user_id, sent_at)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_notification_logs_user_sent")
    op.execute("DROP TABLE IF EXISTS notification_logs")
    op.execute("DROP TABLE IF EXISTS pool_ledger")
    op.execute("DROP INDEX IF EXISTS idx_verifications_user_started")
    op.execute("DROP TABLE IF EXISTS verifications")
    op.execute("DROP TABLE IF EXISTS event_attendance")
    op.execute("DROP INDEX IF EXISTS idx_events_lat_lng")
    op.execute("DROP INDEX IF EXISTS idx_events_city_starts")
    op.execute("DROP TABLE IF EXISTS events")

