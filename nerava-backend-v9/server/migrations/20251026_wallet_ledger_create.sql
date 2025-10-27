-- Migration: Create new wallet_events table
-- Date: 2025-10-26

CREATE TABLE IF NOT EXISTS wallet_events (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    kind TEXT CHECK(kind IN ('credit','debit')) NOT NULL,
    source TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    meta JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
