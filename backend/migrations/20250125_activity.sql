-- Reputation (lite)
CREATE TABLE IF NOT EXISTS user_reputation (
  user_id UUID PRIMARY KEY,
  score INT NOT NULL DEFAULT 0,
  tier  TEXT NOT NULL DEFAULT 'Bronze',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Follows (one-way)
CREATE TABLE IF NOT EXISTS follows (
  follower_id UUID NOT NULL,
  followee_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_auto BOOLEAN NOT NULL DEFAULT true,
  PRIMARY KEY (follower_id, followee_id)
);
CREATE INDEX IF NOT EXISTS idx_follows_followee ON follows (followee_id);

-- Per-session follow earnings events (receiver earned amount_cents because payer charged)
CREATE TABLE IF NOT EXISTS follow_earnings_events (
  id UUID PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payer_user_id UUID NOT NULL,      -- driver who charged
  receiver_user_id UUID NOT NULL,   -- follower who earned
  station_id TEXT,
  session_id UUID,
  energy_kwh NUMERIC(8,2),
  amount_cents INT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fee_receiver_time ON follow_earnings_events (receiver_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fee_payer_time    ON follow_earnings_events (payer_user_id, created_at DESC);

-- Sessions table assumption; add helpful index if not present
-- sessions(id UUID PK, user_id UUID, station_id TEXT, start_at TIMESTAMPTZ, end_at TIMESTAMPTZ, energy_kwh NUMERIC)
CREATE INDEX IF NOT EXISTS idx_sessions_station_time ON sessions (station_id, start_at);
