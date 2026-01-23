-- Dual-Event Verification System Migration
-- Created: 2025-01-26

-- Sessions (charging behavior tracked)
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  t0 TIMESTAMP NOT NULL,
  station_id_guess TEXT,
  start_at TIMESTAMP,
  end_at TIMESTAMP,
  verified_charge BOOLEAN DEFAULT FALSE,
  kwh REAL,
  confidence TEXT DEFAULT 'NONE', -- 'NONE'|'MEDIUM'|'HIGH'
  start_lat REAL,
  start_lng REAL,
  last_lat REAL,
  last_lng REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_t0 ON sessions(user_id, t0 DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_end_at ON sessions(end_at);

-- POS events (ingested from Square webhooks)
CREATE TABLE IF NOT EXISTS pos_events (
  id TEXT PRIMARY KEY,
  user_id TEXT,
  merchant_id TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'square',
  event_type TEXT NOT NULL,
  event_id TEXT NOT NULL,
  order_id TEXT,
  amount_cents INTEGER NOT NULL,
  t_event TIMESTAMP NOT NULL,
  raw_json TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pos_events_provider_event_id ON pos_events(provider, event_id);
CREATE INDEX IF NOT EXISTS idx_pos_events_user_t_event ON pos_events(user_id, t_event DESC);
CREATE INDEX IF NOT EXISTS idx_pos_events_merchant ON pos_events(merchant_id);

-- Merchant balances (aggregation for settlement)
CREATE TABLE IF NOT EXISTS merchant_balances (
  merchant_id TEXT PRIMARY KEY,
  pending_cents INTEGER DEFAULT 0,
  paid_cents INTEGER DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unified wallet events ledger (if not exists)
CREATE TABLE IF NOT EXISTS wallet_events (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  kind TEXT CHECK(kind IN ('credit','debit')) NOT NULL,
  source TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  meta TEXT, -- JSON string
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wallet_events_user ON wallet_events(user_id);
CREATE INDEX IF NOT EXISTS idx_wallet_events_created ON wallet_events(created_at);

-- Idempotency: prevent duplicate credits on same payment
CREATE UNIQUE INDEX IF NOT EXISTS ux_wallet_payment ON wallet_events((json_extract(meta, '$.payment_id'))) WHERE json_extract(meta, '$.payment_id') IS NOT NULL;

-- If reward_events exists, add pointers; otherwise skip
-- ALTER TABLE reward_events ADD COLUMN IF NOT EXISTS session_id TEXT;
-- ALTER TABLE reward_events ADD COLUMN IF NOT EXISTS pos_event_id TEXT;
