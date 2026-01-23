CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, created_at DESC);
