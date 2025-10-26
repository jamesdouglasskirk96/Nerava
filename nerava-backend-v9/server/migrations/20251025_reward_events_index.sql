CREATE INDEX IF NOT EXISTS idx_reward_events_user ON reward_events(user_id, created_at DESC);
