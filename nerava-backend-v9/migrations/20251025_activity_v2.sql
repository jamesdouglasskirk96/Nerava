-- Ensure minimal reputation table exists, then add streak column.
CREATE TABLE IF NOT EXISTS user_reputation (
  user_id UUID PRIMARY KEY,
  score INT NOT NULL DEFAULT 0,
  tier  TEXT NOT NULL DEFAULT 'Bronze',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- v2: streak days for UI chip
ALTER TABLE user_reputation
  ADD COLUMN IF NOT EXISTS streak_days INT NOT NULL DEFAULT 0;

-- Minimal monthly follow earnings TO this user (seeded elsewhere)
CREATE TABLE IF NOT EXISTS follow_earnings_monthly (
  month_yyyymm INT NOT NULL,
  receiver_user_id UUID NOT NULL,
  payer_user_id UUID NOT NULL,
  amount_cents INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (month_yyyymm, receiver_user_id, payer_user_id)
);

CREATE INDEX IF NOT EXISTS idx_follow_earn_month_recv
ON follow_earnings_monthly (month_yyyymm, receiver_user_id);
