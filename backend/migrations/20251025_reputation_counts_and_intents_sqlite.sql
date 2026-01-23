-- Followers / Following counts (store on reputation row for quick read)
-- First create the user_reputation table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_reputation (
  user_id TEXT PRIMARY KEY,
  score INTEGER NOT NULL DEFAULT 0,
  tier TEXT NOT NULL DEFAULT 'Bronze',
  streak_days INTEGER NOT NULL DEFAULT 0,
  followers_count INTEGER NOT NULL DEFAULT 0,
  following_count INTEGER NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Saved Charger Intents
CREATE TABLE IF NOT EXISTS charge_intents (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  station_id TEXT NOT NULL,
  station_name TEXT NOT NULL,
  merchant_name TEXT,
  perk_title TEXT,
  address TEXT,
  eta_minutes INTEGER,             -- rough ETA shown on Explore
  starts_at DATETIME,       -- when user taps "Start"
  status TEXT NOT NULL DEFAULT 'saved', -- saved | started | completed | canceled
  merchant_lat REAL,
  merchant_lng REAL,
  station_lat REAL,
  station_lng REAL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_charge_intents_user ON charge_intents(user_id, status, created_at DESC);
