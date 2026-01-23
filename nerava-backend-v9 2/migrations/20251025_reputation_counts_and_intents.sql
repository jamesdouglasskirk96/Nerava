-- Followers / Following counts (store on reputation row for quick read)
ALTER TABLE user_reputation
  ADD COLUMN IF NOT EXISTS followers_count INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS following_count INT NOT NULL DEFAULT 0;

-- Saved Charger Intents
CREATE TABLE IF NOT EXISTS charge_intents (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  station_id TEXT NOT NULL,
  station_name TEXT NOT NULL,
  merchant_name TEXT,
  perk_title TEXT,
  address TEXT,
  eta_minutes INT,             -- rough ETA shown on Explore
  starts_at TIMESTAMPTZ,       -- when user taps "Start"
  status TEXT NOT NULL DEFAULT 'saved', -- saved | started | completed | canceled
  merchant_lat DOUBLE PRECISION,
  merchant_lng DOUBLE PRECISION,
  station_lat DOUBLE PRECISION,
  station_lng DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_charge_intents_user ON charge_intents(user_id, status, created_at DESC);
