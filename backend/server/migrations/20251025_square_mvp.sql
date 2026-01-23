-- Square MVP Payment Migration
-- Run with: python -c "from src.db import engine; from sqlalchemy import text; engine.execute(text(open('migrations/20251025_square_mvp.sql').read()))"

CREATE TABLE IF NOT EXISTS payments (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  merchant_id TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'square',
  provider_payment_id TEXT,
  status TEXT NOT NULL DEFAULT 'PENDING',
  amount_cents INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  note TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
