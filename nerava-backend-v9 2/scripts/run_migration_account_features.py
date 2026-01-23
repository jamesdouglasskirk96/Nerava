#!/usr/bin/env python3
"""
Run migration_account_features.sql on production database.
"""
import sys
import psycopg2

DATABASE_URL = "postgresql://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"

MIGRATION_SQL = """
-- Add avatar_url to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);

-- Create merchant_favorites table
CREATE TABLE IF NOT EXISTS merchant_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, merchant_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_merchant_favorites_user_id ON merchant_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_merchant_favorites_merchant_id ON merchant_favorites(merchant_id);

-- Create support_tickets table (for future use)
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def main():
    try:
        print("Connecting to production database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Running migration SQL...")
        cursor.execute(MIGRATION_SQL)
        
        print("Migration completed successfully!")
        
        # Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('merchant_favorites', 'support_tickets')
        """)
        tables = cursor.fetchall()
        print(f"Created tables: {[t[0] for t in tables]}")
        
        # Verify column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'avatar_url'
        """)
        column = cursor.fetchone()
        if column:
            print(f"Added column: users.{column[0]}")
        
        cursor.close()
        conn.close()
        return 0
        
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())


